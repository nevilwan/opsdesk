'use client';

import { useState, useEffect, useCallback } from 'react';
import { ticketsApi, type Ticket } from '@/lib/api';
import { priorityColor, statusColor, formatDateTime, timeAgo, categoryIcon, confidenceBar } from '@/lib/utils';

const PRIORITIES = ['', 'critical', 'high', 'medium', 'low'];
const STATUSES = ['', 'open', 'in_progress', 'resolved', 'closed', 'escalated'];
const CATEGORIES = ['', 'Network', 'Hardware', 'Software', 'Security', 'Database', 'Cloud', 'Email', 'VPN', 'Printing', 'Access Management'];

function Badge({ text, className }: { text: string; className: string }) {
  return <span className={`badge border ${className}`}>{text}</span>;
}

function NewTicketModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({
    subject: '', description: '', priority: 'medium',
    requester_name: '', requester_email: '', department: '',
  });
  const [preview, setPreview] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);

  const classifyPreview = useCallback(async () => {
    if (form.subject.length < 5) return;
    try {
      const r = await ticketsApi.classify(form.subject, form.description);
      setPreview(r);
    } catch {}
  }, [form.subject, form.description]);

  useEffect(() => {
    const t = setTimeout(classifyPreview, 600);
    return () => clearTimeout(t);
  }, [classifyPreview]);

  const handleSubmit = async () => {
    if (!form.subject) return;
    setSubmitting(true);
    try {
      await ticketsApi.create(form);
      onCreated();
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="font-semibold text-slate-800">Create New Ticket</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl">×</button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="text-xs font-medium text-slate-600 block mb-1">Subject *</label>
            <input className="input" placeholder="Brief description of the issue"
              value={form.subject} onChange={e => setForm(f => ({ ...f, subject: e.target.value }))} />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 block mb-1">Description</label>
            <textarea className="input min-h-[80px] resize-none" placeholder="Detailed description..."
              value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
          </div>

          {/* AI Preview */}
          {preview && (
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
              <p className="text-xs font-medium text-blue-700 mb-2">🤖 AI Classification Preview</p>
              <div className="flex flex-wrap gap-2">
                {preview.top_predictions?.slice(0, 3).map((p: any) => {
                  const { pct, color } = confidenceBar(p.probability);
                  return (
                    <div key={p.category} className="bg-white rounded px-2 py-1 text-xs border border-blue-100">
                      {categoryIcon(p.category)} {p.category}
                      <span className={`ml-1.5 px-1.5 py-0.5 rounded text-white text-xs ${color}`}>{pct}%</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Priority</label>
              <select className="input" value={form.priority} onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}>
                {['low','medium','high','critical'].map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Department</label>
              <input className="input" placeholder="e.g. Engineering" value={form.department}
                onChange={e => setForm(f => ({ ...f, department: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Your Name</label>
              <input className="input" placeholder="John Doe" value={form.requester_name}
                onChange={e => setForm(f => ({ ...f, requester_name: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Your Email</label>
              <input className="input" type="email" placeholder="john@company.com" value={form.requester_email}
                onChange={e => setForm(f => ({ ...f, requester_email: e.target.value }))} />
            </div>
          </div>
        </div>
        <div className="px-6 py-4 border-t border-slate-100 flex justify-end gap-3">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSubmit} disabled={submitting || !form.subject} className="btn-primary">
            {submitting ? '⏳ Creating...' : '🎫 Create Ticket'}
          </button>
        </div>
      </div>
    </div>
  );
}

function TicketRow({ ticket, onClick }: { ticket: Ticket; onClick: () => void }) {
  const risk = ticket.ai_sla_risk;
  const riskColor = risk > 0.7 ? 'text-red-600' : risk > 0.4 ? 'text-yellow-600' : 'text-green-600';
  return (
    <tr onClick={onClick} className="hover:bg-slate-50 cursor-pointer border-b border-slate-100 last:border-0 transition-colors">
      <td className="px-4 py-3">
        <p className="text-xs font-mono text-slate-400">{ticket.id}</p>
        <p className="text-sm font-medium text-slate-800 mt-0.5 truncate max-w-xs">{ticket.subject}</p>
        <p className="text-xs text-slate-400 mt-0.5">{ticket.department || ticket.requester_email}</p>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <span className="text-base">{categoryIcon(ticket.category)}</span>
        <span className="text-xs text-slate-600 ml-1">{ticket.category}</span>
        {ticket.ai_category_confidence && (
          <div className="text-xs text-slate-400 mt-0.5">
            {Math.round(ticket.ai_category_confidence * 100)}% conf.
          </div>
        )}
      </td>
      <td className="px-4 py-3">
        <Badge text={ticket.priority} className={priorityColor(ticket.priority)} />
      </td>
      <td className="px-4 py-3">
        <Badge text={ticket.status.replace('_', ' ')} className={statusColor(ticket.status)} />
      </td>
      <td className="px-4 py-3 text-xs text-slate-600 whitespace-nowrap">
        {ticket.assigned_agent || '—'}
        <p className="text-xs text-slate-400">{ticket.routing_method}</p>
      </td>
      <td className="px-4 py-3 text-xs whitespace-nowrap">
        <span className={riskColor}>{Math.round(risk * 100)}%</span>
        <p className="text-xs text-slate-400">{ticket.sla_target_hours}h SLA</p>
      </td>
      <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">
        {timeAgo(ticket.created_at)}
      </td>
    </tr>
  );
}

function TicketDetail({ ticket, onClose, onUpdate }: { ticket: Ticket; onClose: () => void; onUpdate: () => void }) {
  const [comment, setComment] = useState('');
  const [status, setStatus] = useState(ticket.status);
  const [submittingComment, setSubmittingComment] = useState(false);
  const [explanation, setExplanation] = useState<any>(null);

  useEffect(() => {
    ticketsApi.explain(ticket.id).then(setExplanation).catch(() => {});
  }, [ticket.id]);

  const handleStatusChange = async (newStatus: string) => {
    setStatus(newStatus);
    await ticketsApi.update(ticket.id, { status: newStatus });
    onUpdate();
  };

  const handleComment = async () => {
    if (!comment.trim()) return;
    setSubmittingComment(true);
    await ticketsApi.addComment(ticket.id, comment, 'Admin User');
    setComment('');
    setSubmittingComment(false);
  };

  const handleEscalate = async () => {
    await ticketsApi.escalate(ticket.id, 'Manual escalation');
    onUpdate();
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-start justify-end z-50">
      <div className="bg-white h-full w-full max-w-2xl shadow-2xl overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-slate-100 px-6 py-4 flex items-start justify-between">
          <div>
            <p className="text-xs font-mono text-slate-400">{ticket.id}</p>
            <h2 className="font-semibold text-slate-800 text-sm mt-0.5 max-w-md">{ticket.subject}</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-2xl ml-4">×</button>
        </div>

        <div className="p-6 space-y-5">
          {/* Badges */}
          <div className="flex flex-wrap gap-2">
            <Badge text={ticket.priority} className={priorityColor(ticket.priority)} />
            <Badge text={ticket.status.replace('_', ' ')} className={statusColor(ticket.status)} />
            {ticket.sla_breached && <Badge text="SLA Breached" className="bg-red-100 text-red-700 border-red-200" />}
            {ticket.escalated && <Badge text="Escalated" className="bg-orange-100 text-orange-700 border-orange-200" />}
            <Badge text={ticket.ab_test_group?.replace('_', ' ')} className="bg-slate-100 text-slate-600 border-slate-200" />
          </div>

          {/* AI Box */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-xl p-4">
            <p className="text-xs font-semibold text-blue-700 mb-3">🤖 AI Analysis</p>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <p className="text-slate-500">Predicted Category</p>
                <p className="font-medium text-slate-800">{categoryIcon(ticket.ai_category)} {ticket.ai_category}</p>
                <p className="text-slate-400">{Math.round((ticket.ai_category_confidence || 0) * 100)}% confidence</p>
              </div>
              <div>
                <p className="text-slate-500">Est. Resolution</p>
                <p className="font-medium text-slate-800">{ticket.ai_predicted_resolution_hours}h</p>
                <p className="text-slate-400">SLA target: {ticket.sla_target_hours}h</p>
              </div>
              <div>
                <p className="text-slate-500">SLA Risk</p>
                <p className={`font-medium ${ticket.ai_sla_risk > 0.7 ? 'text-red-600' : ticket.ai_sla_risk > 0.4 ? 'text-yellow-600' : 'text-green-600'}`}>
                  {Math.round((ticket.ai_sla_risk || 0) * 100)}%
                </p>
              </div>
              <div>
                <p className="text-slate-500">Routing Method</p>
                <p className="font-medium text-slate-800">{ticket.routing_method}</p>
              </div>
            </div>
          </div>

          {/* Explainability */}
          {explanation && (
            <div className="border border-slate-200 rounded-xl p-4">
              <p className="text-xs font-semibold text-slate-700 mb-3">🔍 Routing Explanation (SHAP-style)</p>
              <p className="text-xs text-slate-500 mb-3">Assigned to <strong>{explanation.assigned_to}</strong> — {Math.round(explanation.routing_confidence * 100)}% confidence</p>
              <div className="space-y-2">
                {explanation.explanation_factors?.map((f: any, i: number) => (
                  <div key={i} className="flex items-start gap-2">
                    <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${f.direction === 'positive' ? 'bg-green-400' : 'bg-slate-300'}`} />
                    <div>
                      <p className="text-xs font-medium text-slate-700">{f.feature}: <span className="text-blue-600">{f.value}</span></p>
                      <p className="text-xs text-slate-400">{f.explanation}</p>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-2">Model: {explanation.routing_logic}</p>
            </div>
          )}

          {/* Details */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            {[
              ['Requester', ticket.requester_name || ticket.requester_email || '—'],
              ['Assigned To', ticket.assigned_agent || '—'],
              ['Department', ticket.department || '—'],
              ['Language', ticket.language],
              ['Source', ticket.source],
              ['Created', formatDateTime(ticket.created_at)],
              ['Updated', formatDateTime(ticket.updated_at)],
              ['Resolved', formatDateTime(ticket.resolved_at)],
            ].map(([label, val]) => (
              <div key={label}>
                <p className="text-slate-400">{label}</p>
                <p className="font-medium text-slate-700 mt-0.5">{val}</p>
              </div>
            ))}
          </div>

          {/* Description */}
          {ticket.description && (
            <div>
              <p className="text-xs font-semibold text-slate-600 mb-1.5">Description</p>
              <p className="text-sm text-slate-600 bg-slate-50 rounded-lg p-3">{ticket.description}</p>
            </div>
          )}

          {/* Status Change */}
          <div className="flex gap-2 flex-wrap">
            <p className="text-xs font-semibold text-slate-600 w-full">Change Status</p>
            {['open','in_progress','resolved','closed'].map(s => (
              <button key={s} onClick={() => handleStatusChange(s)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${status === s ? statusColor(s) + ' border-current' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>
                {s.replace('_', ' ')}
              </button>
            ))}
            <button onClick={handleEscalate} className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-50 text-red-600 border border-red-200 hover:bg-red-100">
              ⚠️ Escalate
            </button>
          </div>

          {/* Comment */}
          <div>
            <p className="text-xs font-semibold text-slate-600 mb-1.5">Add Note</p>
            <textarea className="input min-h-[70px] resize-none text-sm" placeholder="Type a note or reply..."
              value={comment} onChange={e => setComment(e.target.value)} />
            <button onClick={handleComment} disabled={!comment.trim() || submittingComment}
              className="btn-primary mt-2 text-xs px-3 py-1.5">
              {submittingComment ? '⏳' : '💬 Add Note'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: '', priority: '', category: '' });
  const [page, setPage] = useState(1);
  const [showNew, setShowNew] = useState(false);
  const [selected, setSelected] = useState<Ticket | null>(null);
  const [search, setSearch] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, page_size: 20 };
      if (filters.status) params.status = filters.status;
      if (filters.priority) params.priority = filters.priority;
      if (filters.category) params.category = filters.category;
      const data = await ticketsApi.list(params);
      setTickets(data.tickets);
      setTotal(data.total);
    } catch {
      setTickets([]);
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => { load(); }, [load]);

  const filtered = search
    ? tickets.filter(t => t.subject.toLowerCase().includes(search.toLowerCase()) || t.id.includes(search))
    : tickets;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-800">Tickets</h1>
          <p className="text-sm text-slate-500 mt-0.5">{total.toLocaleString()} total tickets</p>
        </div>
        <button onClick={() => setShowNew(true)} className="btn-primary">+ New Ticket</button>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-4 flex flex-wrap gap-3 items-center">
        <input className="input w-48" placeholder="🔍 Search tickets..." value={search}
          onChange={e => setSearch(e.target.value)} />
        {(['status','priority','category'] as const).map(key => (
          <select key={key} className="input w-36" value={filters[key]}
            onChange={e => { setFilters(f => ({ ...f, [key]: e.target.value })); setPage(1); }}>
            <option value="">{key.charAt(0).toUpperCase() + key.slice(1)}: All</option>
            {(key === 'status' ? STATUSES : key === 'priority' ? PRIORITIES : CATEGORIES).filter(Boolean).map(o => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
        ))}
        <button onClick={() => { setFilters({ status: '', priority: '', category: '' }); setSearch(''); }} className="btn-secondary text-xs">
          Clear
        </button>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-sm text-slate-500">Loading tickets...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-3xl mb-2">🎫</p>
            <p className="text-slate-500 text-sm">No tickets found. Create one or adjust filters.</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                {['Ticket','Category','Priority','Status','Agent','SLA Risk','Created'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(t => (
                <TicketRow key={t.id} ticket={t} onClick={() => setSelected(t)} />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {total > 20 && (
        <div className="flex items-center justify-between mt-4 text-sm text-slate-500">
          <p>Showing {Math.min((page - 1) * 20 + 1, total)}–{Math.min(page * 20, total)} of {total}</p>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary text-xs py-1">← Prev</button>
            <button onClick={() => setPage(p => p + 1)} disabled={page * 20 >= total} className="btn-secondary text-xs py-1">Next →</button>
          </div>
        </div>
      )}

      {/* Modals */}
      {showNew && <NewTicketModal onClose={() => setShowNew(false)} onCreated={load} />}
      {selected && <TicketDetail ticket={selected} onClose={() => setSelected(null)} onUpdate={load} />}
    </div>
  );
}
