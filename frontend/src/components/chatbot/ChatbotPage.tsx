'use client';

import { useState, useRef, useEffect } from 'react';
import { chatbotApi } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  source?: string;
  suggestions?: any[];
  kb?: any[];
  timestamp: Date;
}

const SESSION_ID = `session_${Math.random().toString(36).slice(2)}`;

const SUGGESTED_QUESTIONS = [
  "How do I reset my password?",
  "VPN is not connecting, what should I do?",
  "My laptop is running very slow",
  "I can't print from my computer",
  "How do I request access to a system?",
  "Outlook isn't syncing my emails",
];

export default function ChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hi! I'm OpsDesk AI, your IT support assistant. I can help you troubleshoot issues, find solutions in our knowledge base, or create a ticket if needed. How can I help you today?",
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;

    setMessages(prev => [...prev, { role: 'user', content: msg, timestamp: new Date() }]);
    setInput('');
    setLoading(true);

    try {
      const res = await chatbotApi.send(SESSION_ID, msg);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.reply,
        source: res.source,
        suggestions: res.suggested_actions,
        kb: res.kb_results,
        timestamp: new Date(),
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I'm having trouble connecting to the server. Please ensure the backend is running on port 8000.",
        source: 'error',
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const sourceLabel: Record<string, string> = {
    ml: '🤖 ML',
    openai: '✨ GPT',
    rule_based: '📋 Rules',
    kb: '📚 KB',
    fallback: '💬',
    error: '⚠️',
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-lg">🤖</div>
          <div>
            <p className="font-semibold text-slate-800">OpsDesk AI Assistant</p>
            <p className="text-xs text-green-500">● Online — powered by ML + Knowledge Base</p>
          </div>
        </div>
        <button
          onClick={() => {
            chatbotApi.clearSession(SESSION_ID);
            setMessages([{
              role: 'assistant',
              content: "Session cleared! How can I help you?",
              timestamp: new Date(),
            }]);
          }}
          className="btn-secondary text-xs"
        >
          Clear Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} gap-3`}>
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs shrink-0 mt-1">AI</div>
            )}
            <div className={`max-w-lg ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
              <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-sm'
                  : 'bg-white border border-slate-200 text-slate-700 rounded-tl-sm shadow-sm'
              }`}>
                {msg.content}
              </div>

              {/* KB Results */}
              {msg.kb && msg.kb.length > 0 && (
                <div className="mt-1 space-y-1">
                  {msg.kb.map((r: any, j: number) => (
                    <div key={j} className="bg-blue-50 border border-blue-100 rounded-lg px-3 py-2 text-xs text-blue-700">
                      📚 <span className="font-medium">{r.category}</span>: {(r.text_clean || '').slice(0, 80)}...
                      <span className="ml-1 text-blue-400">({Math.round(r.similarity * 100)}% match)</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Suggested Actions */}
              {msg.suggestions && msg.suggestions.length > 0 && (
                <div className="flex gap-2 mt-1 flex-wrap">
                  {msg.suggestions.map((s: any, j: number) => (
                    <button key={j} className="text-xs bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 px-3 py-1 rounded-full transition-colors">
                      {s.label}
                    </button>
                  ))}
                </div>
              )}

              <p className="text-xs text-slate-400 px-1">
                {msg.role === 'assistant' && msg.source && (
                  <span className="mr-2">{sourceLabel[msg.source] || msg.source}</span>
                )}
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>

            {msg.role === 'user' && (
              <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-xs font-semibold text-slate-600 shrink-0 mt-1">U</div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex justify-start gap-3">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs shrink-0">AI</div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
              <div className="flex gap-1 items-center">
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick Suggestions (only at start) */}
      {messages.length <= 1 && (
        <div className="px-6 pb-2">
          <p className="text-xs text-slate-400 mb-2">Suggested questions:</p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.map(q => (
              <button key={q} onClick={() => sendMessage(q)}
                className="text-xs bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 px-3 py-1.5 rounded-full transition-colors">
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="px-6 py-4 bg-white border-t border-slate-200">
        <div className="flex gap-3">
          <input
            className="input flex-1"
            placeholder="Ask about any IT issue..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
            disabled={loading}
          />
          <button onClick={() => sendMessage()} disabled={!input.trim() || loading} className="btn-primary px-5">
            {loading ? '⏳' : '➤'}
          </button>
        </div>
        <p className="text-xs text-slate-400 mt-2 text-center">
          Powered by ML Knowledge Base + rule-based NLP. Connect OpenAI in settings for GPT-4 responses.
        </p>
      </div>
    </div>
  );
}
