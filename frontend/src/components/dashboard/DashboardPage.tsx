'use client';

import { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { analyticsApi, ticketsApi } from '@/lib/api';

const CATEGORY_COLORS = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#f97316','#84cc16','#ec4899','#6366f1'];

function StatCard({ label, value, sub, color = 'blue', icon }: any) {
  const colors: Record<string, string> = {
    blue: 'border-l-blue-500 bg-blue-50', green: 'border-l-green-500 bg-green-50',
    yellow: 'border-l-yellow-500 bg-yellow-50', red: 'border-l-red-500 bg-red-50',
    purple: 'border-l-purple-500 bg-purple-50',
  };
  return (
    <div className={`card p-5 border-l-4 ${colors[color]}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
          {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
        </div>
        <span className="text-2xl">{icon}</span>
      </div>
    </div>
  );
}

function SLAGauge({ rate }: { rate: number }) {
  const pct = Math.round(rate * 100);
  const color = pct >= 90 ? '#10b981' : pct >= 70 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex flex-col items-center gap-2">
      <svg viewBox="0 0 100 60" className="w-32">
        <path d="M10,55 A45,45 0 0,1 90,55" fill="none" stroke="#e2e8f0" strokeWidth="10" strokeLinecap="round" />
        <path d="M10,55 A45,45 0 0,1 90,55" fill="none" stroke={color} strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${pct * 1.41} 141`} />
        <text x="50" y="52" textAnchor="middle" fontSize="16" fontWeight="bold" fill={color}>{pct}%</text>
      </svg>
      <p className="text-xs text-slate-500">SLA Compliance</p>
    </div>
  );
}

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);

  const loadData = async () => {
    try {
      const data = await analyticsApi.dashboard(30);
      setAnalytics(data);
    } catch {
      // Backend may not be running — show empty state
      setAnalytics(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await ticketsApi.seedDemo(80);
      await loadData();
    } finally {
      setSeeding(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-500 text-sm">Loading dashboard...</p>
      </div>
    </div>
  );

  const s = analytics?.summary || {};
  const p = analytics?.performance || {};
  const trend = analytics?.trend || [];
  const catDist = Object.entries(analytics?.distributions?.by_category || {}).map(([cat, count]) => ({ name: cat, value: count }));
  const agentPerf = analytics?.agent_performance || [];
  const ab = analytics?.ab_test || {};
  const cost = analytics?.cost_analysis || {};

  const isEmpty = s.total_tickets === 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-800">Operations Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">Real-time IT helpdesk analytics — last 30 days</p>
        </div>
        <div className="flex gap-3">
          {isEmpty && (
            <button onClick={handleSeed} disabled={seeding} className="btn-primary">
              {seeding ? '⏳ Seeding...' : '🌱 Seed Demo Data'}
            </button>
          )}
          <button onClick={loadData} className="btn-secondary">↻ Refresh</button>
        </div>
      </div>

      {isEmpty ? (
        <div className="card p-12 text-center">
          <p className="text-4xl mb-4">📊</p>
          <h2 className="text-lg font-semibold text-slate-700 mb-2">No tickets yet</h2>
          <p className="text-slate-500 text-sm mb-4">Seed demo data to see the full dashboard in action.</p>
          <button onClick={handleSeed} disabled={seeding} className="btn-primary">
            {seeding ? 'Seeding...' : '🌱 Seed 80 Demo Tickets'}
          </button>
        </div>
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <StatCard label="Total Tickets" value={s.total_tickets?.toLocaleString()} icon="🎫" color="blue" sub="Last 30 days" />
            <StatCard label="Open" value={s.open} icon="📬" color="yellow" sub={`${s.in_progress} in progress`} />
            <StatCard label="Resolved" value={s.resolved} icon="✅" color="green" sub={`${Math.round((s.resolved / s.total_tickets) * 100)}% rate`} />
            <StatCard label="Escalated" value={s.escalated} icon="⚠️" color="red" sub={`${s.sla_breached} SLA breached`} />
            <StatCard label="Avg Resolution" value={`${p.avg_resolution_hours}h`} icon="⏱️" color="purple" sub={`CSAT: ${p.avg_csat_score || '—'}/5`} />
          </div>

          {/* SLA + Trend Row */}
          <div className="grid grid-cols-3 gap-4">
            <div className="card p-5 flex flex-col items-center justify-center">
              <SLAGauge rate={s.sla_compliance_rate || 0} />
              <div className="mt-3 text-center">
                <p className="text-sm font-medium text-slate-700">SLA Metrics</p>
                <p className="text-xs text-slate-500">{s.sla_breached} breaches of {s.total_tickets} tickets</p>
              </div>
            </div>

            <div className="card p-5 col-span-2">
              <p className="text-sm font-semibold text-slate-700 mb-4">Ticket Volume Trend</p>
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={trend.slice(-14)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={v => v.slice(5)} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Category + Agent Row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="card p-5">
              <p className="text-sm font-semibold text-slate-700 mb-4">Tickets by Category</p>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={catDist} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`} labelLine={false} fontSize={10}>
                    {catDist.map((_, i) => <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-5">
              <p className="text-sm font-semibold text-slate-700 mb-4">Agent Performance</p>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={agentPerf} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis type="number" tick={{ fontSize: 10 }} />
                  <YAxis type="category" dataKey="agent" width={80} tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="total_tickets" fill="#3b82f6" radius={[0,4,4,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* A/B Test + Cost Row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="card p-5">
              <p className="text-sm font-semibold text-slate-700 mb-1">A/B Test — Routing Strategy</p>
              <p className="text-xs text-slate-500 mb-4">Rule-based vs ML routing comparison</p>
              <div className="flex gap-4">
                <div className="flex-1 bg-blue-50 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-blue-600">{ab.rule_based_count}</p>
                  <p className="text-xs text-blue-500 mt-1">Rule-Based</p>
                </div>
                <div className="flex-1 bg-purple-50 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-purple-600">{ab.ml_routing_count}</p>
                  <p className="text-xs text-purple-500 mt-1">ML Routing</p>
                </div>
              </div>
              <div className="mt-3 p-2 bg-green-50 rounded text-xs text-green-700">
                ✅ Recommended: {ab.recommendation === 'ml_routing' ? 'ML Routing' : 'Rule-Based'} based on resolution metrics
              </div>
            </div>

            <div className="card p-5">
              <p className="text-sm font-semibold text-slate-700 mb-1">Cost Analysis</p>
              <p className="text-xs text-slate-500 mb-4">Simulated operational cost per ticket</p>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Cost per ticket</span>
                  <span className="font-semibold text-slate-800">${cost.cost_per_ticket}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Total period cost</span>
                  <span className="font-semibold text-slate-800">${cost.total_cost_usd?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Avg first response</span>
                  <span className="font-semibold text-slate-800">{p.avg_first_response_hours}h</span>
                </div>
                <div className="h-px bg-slate-100" />
                <p className="text-xs text-slate-400">AI automation reduces cost by ~40% vs manual triage</p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
