'use client';

import { useState } from 'react';
import Sidebar from '@/components/shared/Sidebar';
import DashboardPage from '@/components/dashboard/DashboardPage';
import TicketsPage from '@/components/tickets/TicketsPage';
import AnalyticsPage from '@/components/analytics/AnalyticsPage';
import ChatbotPage from '@/components/chatbot/ChatbotPage';
import KnowledgePage from '@/components/knowledge/KnowledgePage';

type Page = 'dashboard' | 'tickets' | 'analytics' | 'chatbot' | 'knowledge';

export default function Home() {
  const [activePage, setActivePage] = useState<Page>('dashboard');

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':  return <DashboardPage />;
      case 'tickets':    return <TicketsPage />;
      case 'analytics':  return <AnalyticsPage />;
      case 'chatbot':    return <ChatbotPage />;
      case 'knowledge':  return <KnowledgePage />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar activePage={activePage} onNavigate={(p) => setActivePage(p as Page)} />
      <main className="flex-1 overflow-auto">
        {renderPage()}
      </main>
    </div>
  );
}
