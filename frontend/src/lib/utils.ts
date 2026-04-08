// Utility helpers for OpsDesk UI

export function cn(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ');
}

export function priorityColor(priority: string) {
  switch (priority?.toLowerCase()) {
    case 'critical': return 'bg-red-100 text-red-700 border-red-200';
    case 'high':     return 'bg-orange-100 text-orange-700 border-orange-200';
    case 'medium':   return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    case 'low':      return 'bg-green-100 text-green-700 border-green-200';
    default:         return 'bg-slate-100 text-slate-600';
  }
}

export function statusColor(status: string) {
  switch (status?.toLowerCase()) {
    case 'open':        return 'bg-blue-100 text-blue-700';
    case 'in_progress': return 'bg-purple-100 text-purple-700';
    case 'resolved':    return 'bg-green-100 text-green-700';
    case 'closed':      return 'bg-slate-100 text-slate-600';
    case 'escalated':   return 'bg-red-100 text-red-700';
    case 'pending':     return 'bg-yellow-100 text-yellow-700';
    default:            return 'bg-slate-100 text-slate-600';
  }
}

export function formatDate(dateStr?: string) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function formatDateTime(dateStr?: string) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function confidenceBar(score: number) {
  const pct = Math.round(score * 100);
  const color = pct >= 80 ? 'bg-green-500' : pct >= 60 ? 'bg-yellow-400' : 'bg-red-400';
  return { pct, color };
}

export function categoryIcon(category: string) {
  const icons: Record<string, string> = {
    'Network': '🌐', 'Hardware': '💻', 'Software': '⚙️',
    'Security': '🔒', 'Database': '🗄️', 'Cloud': '☁️',
    'Email': '📧', 'VPN': '🔐', 'Printing': '🖨️',
    'Access Management': '🔑', 'Other': '📋',
  };
  return icons[category] || '📋';
}
