'use client';

import { cn } from '@/lib/utils';

const NAV = [
  { id: 'dashboard',  label: 'Dashboard',       icon: '📊' },
  { id: 'tickets',    label: 'Tickets',          icon: '🎫' },
  { id: 'analytics',  label: 'Analytics',        icon: '📈' },
  { id: 'chatbot',    label: 'AI Chatbot',       icon: '🤖' },
  { id: 'knowledge',  label: 'Knowledge Base',   icon: '📚' },
];

const AGENTS = [
  { name: 'Alice Johnson',  status: 'online',  tickets: 5 },
  { name: 'Bob Martinez',   status: 'online',  tickets: 3 },
  { name: 'Carol White',    status: 'busy',    tickets: 7 },
  { name: 'Frank Davis',    status: 'online',  tickets: 6 },
];

const statusDot = (s: string) => ({
  online: 'bg-green-400',
  busy:   'bg-yellow-400',
  away:   'bg-slate-300',
}[s] || 'bg-slate-300');

export default function Sidebar({
  activePage,
  onNavigate,
}: {
  activePage: string;
  onNavigate: (page: string) => void;
}) {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-full shrink-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white text-sm font-bold">O</div>
          <div>
            <p className="font-semibold text-slate-900 text-sm leading-tight">OpsDesk AI</p>
            <p className="text-xs text-slate-400">IT Operations Platform</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="px-3 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Menu</p>
        {NAV.map(({ id, label, icon }) => (
          <button
            key={id}
            onClick={() => onNavigate(id)}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors text-left',
              activePage === id
                ? 'bg-blue-50 text-blue-700'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            )}
          >
            <span className="text-base">{icon}</span>
            {label}
          </button>
        ))}

        {/* Active Agents */}
        <p className="px-3 pt-5 pb-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Active Agents
        </p>
        {AGENTS.map((a) => (
          <div key={a.name} className="flex items-center gap-2.5 px-3 py-1.5">
            <div className="relative">
              <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-xs font-medium text-slate-600">
                {a.name.split(' ').map(n => n[0]).join('')}
              </div>
              <span className={cn('absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-white', statusDot(a.status))} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-slate-700 truncate">{a.name}</p>
              <p className="text-xs text-slate-400">{a.tickets} tickets</p>
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs text-white font-semibold">A</div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-slate-800">Admin User</p>
            <p className="text-xs text-slate-400">admin@opsdesk.ai</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
