import React, { useState } from 'react';
import { Monitor, Smartphone, PenTool, PlayCircle, BarChart2, Plus, LogOut, RefreshCw } from 'lucide-react';

interface HomeViewProps {
  onStartProject: (prompt: string) => void;
  username: string;
}

export default function HomeView({ onStartProject, username }: HomeViewProps) {
  const isDemo = process.env.NEXT_PUBLIC_IS_DEMO === 'true';
  const [prompt, setPrompt] = useState("");

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (prompt.trim()) {
        onStartProject(prompt);
      }
    }
  };

  const actionButtons = [
    { icon: Monitor, label: "Website", onClick: () => setPrompt("Create a landing page for ") },
    { icon: Smartphone, label: "Mobile", onClick: () => setPrompt("Create a mobile app screen for ") },
    { icon: PenTool, label: "Design", onClick: () => setPrompt("Design a UI component for ") },
    { icon: PlayCircle, label: "Animation", onClick: () => setPrompt("Create an animated ") },
    { icon: BarChart2, label: "Data Visualization", onClick: () => setPrompt("Create a dashboard with charts for ") },
  ];

  const examplePrompts = [
    "Startup pitch deck",
    "Retail sales dashboard",
    "Startup analytics dashboard"
  ];

  return (
    <div className="w-full h-full flex flex-col items-center justify-center bg-lovable-cream text-lovable-charcoal p-8 animate-in fade-in duration-500">
      
      {/* Workspace Selector */}
      <div className="absolute top-8 left-1/2 -translate-x-1/2">
        <div className="flex items-center gap-2 bg-lovable-surface px-4 py-2 rounded-full text-sm font-medium transition-colors border border-lovable-border shadow-lovable cursor-pointer hover:bg-gray-50 dark:hover:bg-white/5">
          {isDemo ? (
            <>
              <Monitor size={16} className="text-blue-500" />
              Demo Workspace
            </>
          ) : (
            <>
              <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center text-xs overflow-hidden">
                <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${username}`} alt="avatar" />
              </div>
              {username}'s Workspace
              <span className="text-lovable-muted ml-1">v</span>
            </>
          )}
        </div>
      </div>

      <div className="w-full max-w-3xl flex flex-col items-center mt-12">
        <h1 className="text-2xl md:text-3xl font-semibold mb-8 tracking-tight">
          {isDemo ? "Hi there, what do you want to make?" : `Hi @${username}, what do you want to make?`}
        </h1>

        <div className="w-full relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
          <div className="relative w-full bg-lovable-surface border border-lovable-border rounded-xl flex items-center p-3 shadow-2xl">
            <button className="p-2 text-lovable-muted hover:text-lovable-charcoal transition-colors">
              <Plus size={20} />
            </button>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe what you want to build..."
              className="flex-1 bg-transparent border-none outline-none resize-none px-3 py-2 text-lovable-charcoal placeholder-lovable-muted min-h-[56px] max-h-[200px]"
              rows={2}
            />
            <div className="flex items-center gap-2 pr-2">
              <button 
                onClick={() => prompt.trim() && onStartProject(prompt)}
                disabled={!prompt.trim()}
                className="p-2 bg-lovable-charcoal hover:opacity-90 disabled:bg-lovable-border disabled:text-lovable-muted text-lovable-cream rounded-lg transition-colors ml-1"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
              </button>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-center gap-6 mt-8 flex-wrap">
          {actionButtons.map((btn, i) => (
            <button 
              key={i}
              onClick={btn.onClick}
              className="flex flex-col items-center gap-2 text-lovable-muted hover:text-lovable-charcoal group transition-colors"
            >
              <div className="w-12 h-12 rounded-xl bg-lovable-surface border border-lovable-border shadow-sm group-hover:border-lovable-charcoal flex items-center justify-center transition-all">
                <btn.icon size={20} />
              </div>
              <span className="text-xs font-medium">{btn.label}</span>
            </button>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center">
          <p className="text-xs text-lovable-muted flex items-center gap-2 mb-4">
            Try an example prompt <RefreshCw size={12} className="cursor-pointer hover:text-lovable-charcoal" />
          </p>
          <div className="flex items-center gap-3 flex-wrap justify-center">
            {examplePrompts.map((p, i) => (
              <button 
                key={i}
                onClick={() => setPrompt(p)}
                className="px-4 py-2 rounded-lg border border-lovable-border bg-lovable-surface hover:bg-gray-50 text-sm text-lovable-charcoal transition-colors shadow-sm"
              >
                {p}
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
