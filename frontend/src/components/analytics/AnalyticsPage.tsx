'use client';

import { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis
} from 'recharts';
import { analyticsApi } from '@/lib/api';
import ForecastPanel from './ForecastPanel';

const COLORS = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#f97316','#84cc16'];

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-5">
      <p className="text-sm font-semibold text-slate-700 mb-4">{title}</p>
      {children}

      {/* Forecasting */}
      <div>
        <p className="text-sm font-semibold text-slate-700 mb-4">🔮 Predictive Forecasting</p>
        <ForecastPanel />
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);
  const [abData, setAbData] = useState<any>(null);
  const [models, setModels] = useState<any>(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      analyticsApi.dashboard(days),
      analyticsApi.abTest(),
      analyticsApi.modelPerformance(),
    ]).then(([dash, ab, mod]) => {
      setData(dash);
      setAbData(ab);
      setModels(mod);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [days]);

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  const s = data?.summary || {};
  const p = data?.performance || {};
  const trend = data?.trend || [];
  const catDist = Object.entries(data?.distributions?.by_category || {})
    .map(([name, value]) => ({ name, value }));
  const priDist = Object.entries(data?.distributions?.by_priority || {})
    .map(([name, value]) => ({ name, value: Number(value) }));
  const agentData = (data?.agent_performance || []).slice(0, 6);

  // Radar data for agent performance
  const radarData = agentData.map((a: any) => ({
    agent: a.agent.split(' ')[0],
    tickets: a.total_tickets,
    resolved: a.resolved,
    rate: Math.round((a.resolution_rate || 0) * 100),
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-800">Analytics</h1>
          <p className="text-sm text-slate-500 mt-0.5">Deep-dive into helpdesk performance metrics</p>
        </div>
        <select className="input w-36 text-sm"
          value={days} onChange={e => setDays(Number(e.target.value))}>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'SLA Compliance', value: `${Math.round((s.sla_compliance_rate || 0) * 100)}%`, icon: '🎯', color: s.sla_compliance_rate > 0.9 ? 'text-green-600' : 'text-red-600' },
          { label: 'Avg Resolution', value: `${p.avg_resolution_hours || 0}h`, icon: '⏱️', color: 'text-blue-600' },
          { label: 'Avg First Response', value: `${p.avg_first_response_hours || 0}h`, icon: '💬', color: 'text-purple-600' },
          { label: 'CSAT Score', value: `${p.avg_csat_score || 0}/5`, icon: '⭐', color: 'text-yellow-600' },
        ].map(kpi => (
          <div key={kpi.label} className="card p-4 text-center">
            <p className="text-2xl mb-1">{kpi.icon}</p>
            <p className={`text-2xl font-bold ${kpi.color}`}>{kpi.value}</p>
            <p className="text-xs text-slate-500 mt-1">{kpi.label}</p>
          </div>
        ))}
      </div>

      {/* Volume Trend */}
      <Section title="📈 Ticket Volume Over Time">
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={trend}>
            <defs>
              <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={v => v.slice(5)} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip />
            <Area type="monotone" dataKey="count" stroke="#3b82f6" fill="url(#grad)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </Section>

      {/* Category + Priority */}
      <div className="grid grid-cols-2 gap-4">
        <Section title="🏷️ By Category">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={catDist} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {catDist.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="🔥 By Priority">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={priDist} dataKey="value" nameKey="name" cx="50%" cy="50%"
                outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false} fontSize={11}>
                {priDist.map((e, i) => (
                  <Cell key={i} fill={{
                    critical: '#ef4444', high: '#f97316',
                    medium: '#f59e0b', low: '#10b981'
                  }[e.name] || COLORS[i]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Section>
      </div>

      {/* Agent Performance */}
      <Section title="👥 Agent Performance">
        <div className="grid grid-cols-2 gap-6">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={agentData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="agent" tick={{ fontSize: 9 }} tickFormatter={v => v.split(' ')[0]} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="total_tickets" name="Total" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="resolved" name="Resolved" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>

          <div className="space-y-2">
            {agentData.map((a: any, i: number) => (
              <div key={a.agent} className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold text-white"
                  style={{ background: COLORS[i % COLORS.length] }}>
                  {a.agent.split(' ').map((n: string) => n[0]).join('')}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-baseline mb-0.5">
                    <span className="text-xs font-medium text-slate-700">{a.agent}</span>
                    <span className="text-xs text-slate-500">{Math.round((a.resolution_rate || 0) * 100)}%</span>
                  </div>
                  <div className="h-1.5 bg-slate-100 rounded-full">
                    <div className="h-1.5 rounded-full" style={{
                      width: `${Math.round((a.resolution_rate || 0) * 100)}%`,
                      background: COLORS[i % COLORS.length]
                    }} />
                  </div>
                </div>
                <span className="text-xs text-slate-400 w-16 text-right">{a.avg_resolution_hours}h avg</span>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* A/B Test + Models */}
      <div className="grid grid-cols-2 gap-4">
        <Section title="🧪 A/B Test — Routing Strategy">
          {abData ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'Rule-Based', count: abData.rule_based_count, color: 'bg-blue-50 text-blue-600 border-blue-100' },
                  { label: 'ML Routing', count: abData.ml_routing_count, color: 'bg-purple-50 text-purple-600 border-purple-100' },
                ].map(g => (
                  <div key={g.label} className={`rounded-xl p-4 text-center border ${g.color}`}>
                    <p className="text-3xl font-bold">{g.count}</p>
                    <p className="text-xs mt-1">{g.label}</p>
                  </div>
                ))}
              </div>
              <div className="text-xs text-slate-500 space-y-1">
                <p>Total experiments: <strong>{abData.total_experiments}</strong></p>
                <p>Winner: <strong className="text-green-600">{abData.recommendation === 'ml_routing' ? 'ML Routing' : 'Rule-Based'}</strong></p>
              </div>
            </div>
          ) : <p className="text-sm text-slate-400">No A/B data yet</p>}
        </Section>

        <Section title="🤖 Model Performance">
          {models ? (
            <div className="space-y-3">
              {Object.entries(models).map(([key, meta]: [string, any]) => (
                <div key={key} className="border border-slate-100 rounded-lg p-3">
                  <p className="text-xs font-semibold text-slate-700">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </p>
                  {meta.accuracy && (
                    <div className="flex gap-4 mt-1">
                      <span className="text-xs text-slate-500">Accuracy: <strong className="text-green-600">{(meta.accuracy * 100).toFixed(1)}%</strong></span>
                      {meta.f1_weighted && <span className="text-xs text-slate-500">F1: <strong className="text-blue-600">{(meta.f1_weighted * 100).toFixed(1)}%</strong></span>}
                    </div>
                  )}
                  {meta.mae_hours && (
                    <div className="flex gap-4 mt-1">
                      <span className="text-xs text-slate-500">MAE: <strong>{meta.mae_hours}h</strong></span>
                      <span className="text-xs text-slate-500">R²: <strong>{meta.r2_score}</strong></span>
                    </div>
                  )}
                  {meta.model_type && <p className="text-xs text-slate-400 mt-1">{meta.model_type}</p>}
                  {meta.trained_at && <p className="text-xs text-slate-300 mt-0.5">{new Date(meta.trained_at).toLocaleString()}</p>}
                  {meta.status === 'not_found' && <p className="text-xs text-slate-400">Model not trained yet</p>}
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-slate-400">Loading model info...</p>}
        </Section>
      </div>

      {/* Forecasting */}
      <div>
        <p className="text-sm font-semibold text-slate-700 mb-4">🔮 Predictive Forecasting</p>
        <ForecastPanel />
      </div>
    </div>
  );
}
