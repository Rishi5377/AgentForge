"use client";
import Navbar from '@/components/Navbar';
import { useEffect, useState } from 'react';

export default function Dashboard() {
  const [status, setStatus] = useState('Loading...');

  useEffect(() => {
    fetch('/api/subscription').then(res => res.json()).then(data => setStatus(data.status));
  }, []);

  return (
    <main className="min-h-screen bg-[var(--bg)]">
      <Navbar />
      <div className="max-w-5xl mx-auto p-12">
        <h1 className="text-4xl font-bold mb-8">Dashboard</h1>
        <div className="p-8 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <h2 className="text-lg font-semibold mb-2">Subscription Status</h2>
          <div className="px-4 py-2 bg-slate-100 rounded-full inline-block font-mono text-sm">{status}</div>
        </div>
      </div>
    </main>
  );
}