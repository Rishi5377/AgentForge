"use client";
import Link from 'next/link';

export default function Navbar() {
  return (
    <nav className="flex items-center justify-between p-6 bg-white/50 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
      <div className="text-xl font-bold text-blue-600">AgentForge</div>
      <div className="flex gap-6">
        <Link href="/" className="hover:text-blue-600 transition-colors">Home</Link>
        <Link href="/dashboard" className="hover:text-blue-600 transition-colors">Dashboard</Link>
      </div>
    </nav>
  );
}