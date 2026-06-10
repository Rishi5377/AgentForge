import React from 'react';
import { Home, Grid, Settings, Moon, Sun, X } from 'lucide-react';

interface AppSidebarProps {
  currentView: 'home' | 'projects' | 'workspace';
  onNavigate: (view: 'home' | 'projects') => void;
  onOpenSettings: () => void;
  onClose: () => void;
}

export default function AppSidebar({ currentView, onNavigate, onOpenSettings, onClose }: AppSidebarProps) {
  return (
    <div className="w-64 h-full bg-lovable-cream border-r border-lovable-border flex flex-col flex-shrink-0 text-lovable-muted relative shadow-2xl">
      <button 
        onClick={onClose}
        className="absolute top-4 right-4 p-1.5 hover:bg-white rounded-md transition-colors text-lovable-muted border border-transparent hover:border-lovable-border"
        title="Close Drawer"
      >
        <X size={16} />
      </button>

      <div className="p-6 pb-2 border-b border-lovable-border">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-lg bg-lovable-charcoal flex items-center justify-center text-white font-bold text-xl">
            A
          </div>
          <span className="font-semibold text-lg text-lovable-charcoal">AgentForge</span>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        <div className="text-xs font-semibold uppercase tracking-wider text-lovable-muted px-2 py-2 mb-1">
          Navigation
        </div>
        
        <button
          onClick={() => {
            onNavigate('home');
            onClose();
          }}
          className={`w-full flex items-center gap-3 px-3 py-2.5 radius-lovable-standard cursor-pointer transition-colors ${
            currentView === 'home' 
              ? 'bg-lovable-surface shadow-lovable border border-lovable-border text-lovable-charcoal font-medium' 
              : 'hover:bg-lovable-surface/50 hover:text-lovable-charcoal text-lovable-muted border border-transparent'
          }`}
        >
          <Home size={18} className={currentView === 'home' ? 'text-lovable-charcoal' : 'text-lovable-muted'} />
          Home
        </button>

        <button
          onClick={() => {
            onNavigate('projects');
            onClose();
          }}
          className={`w-full flex items-center gap-3 px-3 py-2.5 radius-lovable-standard cursor-pointer transition-colors ${
            currentView === 'projects' || currentView === 'workspace'
              ? 'bg-lovable-surface shadow-lovable border border-lovable-border text-lovable-charcoal font-medium' 
              : 'hover:bg-lovable-surface/50 hover:text-lovable-charcoal text-lovable-muted border border-transparent'
          }`}
        >
          <Grid size={18} className={(currentView === 'projects' || currentView === 'workspace') ? 'text-lovable-charcoal' : 'text-lovable-muted'} />
          Projects
        </button>

        <button
          onClick={() => {
            onOpenSettings();
            onClose();
          }}
          className="w-full flex items-center gap-3 px-3 py-2.5 radius-lovable-standard cursor-pointer transition-colors hover:bg-lovable-surface/50 hover:text-lovable-charcoal text-lovable-muted border border-transparent"
        >
          <Settings size={18} className="text-lovable-muted" />
          Settings
        </button>
      </div>
    </div>
  );
}
