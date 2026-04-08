/**
 * OpsDesk AI — API Client
 * Wraps all backend endpoints with type-safe functions.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const TENANT_ID = 'tenant_acme';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-ID': TENANT_ID,
      ...options.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API error');
  }
  return res.json();
}

// ── Tickets ────────────────────────────────────────────────────────────────────

export interface Ticket {
  id: string;
  subject: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  requester_email: string;
  requester_name: string;
  department: string;
  assigned_agent: string;
  ai_category: string;
  ai_category_confidence: number;
  ai_predicted_resolution_hours: number;
  ai_sla_risk: number;
  routing_method: string;
  sla_target_hours: number;
  sla_deadline: string;
  sla_breached: boolean;
  escalated: boolean;
  ab_test_group: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  resolution_hours?: number;
  satisfaction_score?: number;
  language: string;
  source: string;
  tags: string[];
}

export interface TicketListResponse {
  tickets: Ticket[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateTicketPayload {
  subject: string;
  description?: string;
  priority?: string;
  category?: string;
  requester_email?: string;
  requester_name?: string;
  department?: string;
  language?: string;
  tags?: string[];
}

export const ticketsApi = {
  list: (params: Record<string, string | number> = {}) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    return request<TicketListResponse>(`/api/tickets?${qs}`);
  },
  get: (id: string) => request<Ticket>(`/api/tickets/${id}`),
  create: (payload: CreateTicketPayload) =>
    request<{ success: boolean; ticket: Ticket }>('/api/tickets', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  update: (id: string, updates: Partial<Ticket>) =>
    request<Ticket>(`/api/tickets/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    }),
  escalate: (id: string, reason?: string) =>
    request<{ success: boolean; ticket: Ticket }>(`/api/tickets/${id}/escalate?reason=${reason || ''}}`, {
      method: 'POST',
    }),
  addComment: (id: string, body: string, author: string, isInternal = false) =>
    request(`/api/tickets/${id}/comments`, {
      method: 'POST',
      body: JSON.stringify({ body, author, is_internal: isInternal }),
    }),
  getComments: (id: string) => request<any[]>(`/api/tickets/${id}/comments`),
  getEvents: (id: string) => request<any[]>(`/api/tickets/${id}/events`),
  classify: (subject: string, description?: string) =>
    request<any>('/api/tickets/classify', {
      method: 'POST',
      body: JSON.stringify({ subject, description }),
    }),
  explain: (id: string) => request<any>(`/api/tickets/${id}/explain`),
  seedDemo: (count = 50) =>
    request<any>(`/api/tickets/seed-demo?count=${count}`, { method: 'POST' }),
};

// ── Analytics ─────────────────────────────────────────────────────────────────

export const analyticsApi = {
  dashboard: (days = 30) => request<any>(`/api/analytics/dashboard?days=${days}`),
  sla: (days = 30) => request<any>(`/api/analytics/sla?days=${days}`),
  abTest: () => request<any>('/api/analytics/ab-test'),
  modelPerformance: () => request<any>('/api/analytics/model-performance'),
};

// ── Agents ────────────────────────────────────────────────────────────────────

export const agentsApi = {
  list: () => request<any[]>('/api/agents'),
};

// ── Chatbot ───────────────────────────────────────────────────────────────────

export const chatbotApi = {
  send: (sessionId: string, message: string) =>
    request<any>('/api/chatbot/message', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, message }),
    }),
  clearSession: (sessionId: string) =>
    request(`/api/chatbot/session/${sessionId}`, { method: 'DELETE' }),
};

// ── Knowledge Base ────────────────────────────────────────────────────────────

export const knowledgeApi = {
  search: (q: string, topK = 5) =>
    request<any>(`/api/knowledge/search?q=${encodeURIComponent(q)}&top_k=${topK}`),
  articles: () => request<any>('/api/knowledge/articles'),
};

// ── Health ────────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () => request<any>('/api/health'),
};
