'use client';

import { useState, useEffect } from 'react';
import { knowledgeApi } from '@/lib/api';

export default function KnowledgePage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [articles, setArticles] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    knowledgeApi.articles().then(r => setArticles(r.articles || [])).catch(() => {});
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const res = await knowledgeApi.search(query);
      setResults(res.results || []);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-800">Knowledge Base</h1>
        <p className="text-sm text-slate-500 mt-0.5">Semantic search over resolved tickets and IT guides</p>
      </div>

      {/* Search */}
      <div className="card p-5">
        <p className="text-sm font-semibold text-slate-700 mb-3">🔍 Search Knowledge Base</p>
        <div className="flex gap-3">
          <input className="input flex-1" placeholder="e.g. VPN connection timeout, password reset, slow laptop..."
            value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleSearch(); }} />
          <button onClick={handleSearch} disabled={!query.trim() || searching} className="btn-primary px-6">
            {searching ? '⏳' : 'Search'}
          </button>
        </div>

        {results.length > 0 && (
          <div className="mt-4 space-y-3">
            <p className="text-xs font-semibold text-slate-500">{results.length} results</p>
            {results.map((r, i) => (
              <div key={i} className="border border-slate-200 rounded-xl p-4 hover:border-blue-200 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="badge bg-blue-100 text-blue-700">{r.category}</span>
                      <span className="text-xs text-slate-400">{r.ticket_id}</span>
                    </div>
                    <p className="text-sm text-slate-700">{(r.text_clean || '').slice(0, 200)}...</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-semibold text-blue-600">{Math.round((r.similarity || 0) * 100)}%</p>
                    <p className="text-xs text-slate-400">match</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        {results.length === 0 && query && !searching && (
          <p className="text-sm text-slate-400 mt-3">No results found. Try different keywords.</p>
        )}
      </div>

      {/* Featured Articles */}
      <div>
        <p className="text-sm font-semibold text-slate-700 mb-3">📖 Featured Articles</p>
        <div className="grid grid-cols-3 gap-4">
          {articles.map(a => (
            <div key={a.id} className="card p-4 hover:shadow-md transition-shadow cursor-pointer">
              <span className="badge bg-indigo-100 text-indigo-700 mb-2">{a.category}</span>
              <p className="text-sm font-medium text-slate-800 mt-1">{a.title}</p>
              <p className="text-xs text-slate-500 mt-1">{a.body}</p>
              <div className="flex items-center justify-between mt-3 text-xs text-slate-400">
                <span>👁 {a.view_count} views</span>
                <span>👍 {a.helpful_count} helpful</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick FAQ */}
      <div className="card p-5">
        <p className="text-sm font-semibold text-slate-700 mb-4">❓ Frequently Asked</p>
        <div className="space-y-3">
          {[
            { q: 'How long does a password reset take?', a: 'Instant via self-service portal. Manual reset by IT team takes up to 1 business hour.' },
            { q: 'What is the SLA for Critical tickets?', a: 'Critical issues must be acknowledged within 15 minutes and resolved within 2 hours.' },
            { q: 'Can I install software myself?', a: 'Pre-approved software is available in the Software Center. Others require an IT approval ticket.' },
            { q: 'Who do I contact for cloud access issues?', a: 'Cloud & infrastructure issues are handled by Emma Brown. Submit a ticket with category: Cloud.' },
          ].map((item, i) => (
            <details key={i} className="group">
              <summary className="text-sm font-medium text-slate-700 cursor-pointer hover:text-blue-600 list-none flex items-center justify-between py-2 border-b border-slate-100">
                {item.q}
                <span className="text-slate-400 group-open:rotate-180 transition-transform">▾</span>
              </summary>
              <p className="text-sm text-slate-500 pt-2 pb-1">{item.a}</p>
            </details>
          ))}
        </div>
      </div>
    </div>
  );
}
