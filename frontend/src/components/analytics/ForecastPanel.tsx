'use client';

import { useState, useEffect } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchForecast(days: number) {
  const r = await fetch(`${API}/api/forecasting/forecast?days=${days}`);
  return r.json();
}

async function fetchIncidents() {
  const r = await fetch(`${API}/api/forecasting/incidents?lookback_days=7`);
  return r.json();
}

export default function ForecastPanel() {
  const [forecast, setForecast] = useState<any>(null);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [days, setDays] = useState(14);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchForecast(days), fetchIncidents()])
      .then(([f, inc]) => {
        setForecast(f);
        setIncidents(inc.incidents || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) return (
    <div className="card p-8 flex items-center justify-center">
      <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  // Combine historical + forecast for one chart
  const hist = (forecast?.historical || []).map((d: any) => ({
    date: d.ds, actual: d.y, type: 'actual'
  }));
  const fcast = (forecast?.forecast || []).map((d: any) => ({
    date: d.ds, predicted: d.predicted, lower: d.lower, upper: d.upper, type: 'forecast'
  }));
  const chartData = [...hist.slice(-14), ...fcast];

  const peakDay = forecast?.peak_day;
  const recommendation = forecast?.recommendation || '';
  const anomalies = forecast?.anomalies || [];
  const method = forecast?.method || 'unknown';

  const recColor = recommendation.startsWith('🔴') ? 'bg-red-50 border-red-200 text-red-700'
    : recommendation.startsWith('🟡') ? 'bg-yellow-50 border-yellow-200 text-yellow-700'
    : 'bg-green-50 border-green-200 text-green-700';

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-sm font-semibold text-slate-700">📈 Ticket Volume Forecast</p>
            <p className="text-xs text-slate-400 mt-0.5">Method: {method} · Anomalies detected: {anomalies.length}</p>
          </div>
          <select className="input w-32 text-sm"
            value={days} onChange={e => setDays(Number(e.target.value))}>
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>
        </div>

        {/* Recommendation */}
        <div className={`border rounded-lg px-4 py-2.5 text-sm mb-4 ${recColor}`}>
          {recommendation}
        </div>

        {/* Combined Chart */}
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="predGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="date" tick={{ fontSize: 9 }} tickFormatter={v => v.slice(5)} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip formatter={(v: any, name: string) => [v, name === 'actual' ? 'Actual' : 'Forecast']} />
            <Area type="monotone" dataKey="actual" stroke="#3b82f6" fill="url(#actualGrad)" strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="predicted" stroke="#8b5cf6" fill="url(#predGrad)" strokeWidth={2} dot={false} strokeDasharray="5 3" />
            {peakDay && <ReferenceLine x={peakDay} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Peak', fontSize: 10, fill: '#f59e0b' }} />}
          </AreaChart>
        </ResponsiveContainer>

        <div className="flex gap-4 mt-3 text-xs text-slate-500">
          <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-blue-500 inline-block" /> Actual</span>
          <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-purple-500 inline-block border-dashed" /> Forecast</span>
          {peakDay && <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-yellow-500 inline-block" /> Peak day: {peakDay}</span>}
        </div>
      </div>

      {/* Anomalies */}
      {anomalies.length > 0 && (
        <div className="card p-4">
          <p className="text-sm font-semibold text-slate-700 mb-3">⚠️ Historical Anomalies Detected</p>
          <div className="flex flex-wrap gap-2">
            {anomalies.map((d: string) => (
              <span key={d} className="badge bg-orange-100 text-orange-700 border border-orange-200 text-xs">{d}</span>
            ))}
          </div>
          <p className="text-xs text-slate-400 mt-2">Volume spikes 2.5σ above rolling 7-day average</p>
        </div>
      )}

      {/* Predicted Incidents */}
      {incidents.length > 0 && (
        <div className="card p-4">
          <p className="text-sm font-semibold text-slate-700 mb-3">🚨 Predicted Incident Alerts</p>
          <div className="space-y-2">
            {incidents.slice(0, 5).map((inc: any, i: number) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
                <span className={`text-xs font-semibold px-2 py-0.5 rounded ${inc.severity === 'high' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>
                  {inc.severity.toUpperCase()}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-slate-700">{String(inc.timestamp).slice(0, 16)}</p>
                  <p className="text-xs text-slate-500">Volume: {inc.volume} tickets · {inc.suggested_action}</p>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-400 mt-2">Auto-ticket creation available via POST /api/forecasting/incidents</p>
        </div>
      )}
    </div>
  );
}
