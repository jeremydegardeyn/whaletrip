import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'WhaleTrip — Whale Watching Travel Planner',
  description: 'Discover whale watching opportunities worldwide with AI-powered travel planning.',
  icons: { icon: '/favicon.ico' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
