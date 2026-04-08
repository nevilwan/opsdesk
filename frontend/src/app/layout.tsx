import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'OpsDesk AI — IT Operations Platform',
  description: 'AI-powered IT helpdesk automation — ticket classification, intelligent routing, and predictive analytics',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
