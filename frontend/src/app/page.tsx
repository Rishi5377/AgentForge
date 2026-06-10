"use client";

import { useState, useMemo, useEffect } from "react";
import { Send, Settings, Menu, Globe, AlertTriangle, Rocket, Moon, Sun, Home as HomeIcon, ChevronDown, User } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useAgentAnimation } from "@/hooks/useAgentAnimation";
import AgentSprite from "@/components/AgentSprite";
import PreviewPanel from "@/components/PreviewPanel";
import SettingsModal from "@/components/SettingsModal";
import AppSidebar from "@/components/AppSidebar";
import StreamingCode from "@/components/StreamingCode";
import HomeView from "@/components/HomeView";
import ProjectsView from "@/components/ProjectsView";

import ChatMessage from "@/components/ChatMessage";

export default function Home() {
  const isDemo = process.env.NEXT_PUBLIC_IS_DEMO === 'true';
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001";
  const { messages, isConnected, streamingContent, sendMessage, clearMessages } = useWebSocket(`${wsUrl}/ws`);
  const [prompt, setPrompt] = useState("");
  const [chatHistory, setChatHistory] = useState<{role: 'user' | 'assistant', content: string}[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeProjectName, setActiveProjectName] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<'home' | 'projects' | 'workspace'>('home');
  const [username, setUsername] = useState('rishi077');

  useEffect(() => {
    const updateUsername = () => {
      const savedUser = localStorage.getItem('agentforge_username');
      if (savedUser) setUsername(savedUser);
    };
    
    updateUsername();
    window.addEventListener('storage', updateUsername);
    return () => window.removeEventListener('storage', updateUsername);
  }, []);
  
  // New UI states
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [leftPanelWidth, setLeftPanelWidth] = useState(400);
  const [isDragging, setIsDragging] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  const [hasApiKey, setHasApiKey] = useState(true);

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const newWidth = e.clientX;
      // Keep width between 300px and window.innerWidth - 300px
      if (newWidth > 300 && newWidth < window.innerWidth - 300) {
        setLeftPanelWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  // Check API keys on mount
  useEffect(() => {
    const API_URL = (process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001').replace('ws', 'http');
    fetch(`${API_URL}/api/settings`)
      .then(res => res.json())
      .then(data => {
        const keys = Object.values(data?.api_keys || {});
        if (keys.length === 0 || keys.every(k => !k)) {
          setHasApiKey(false);
        } else {
          setHasApiKey(true);
        }
      })
      .catch(() => {
        // Fallback to localStorage if backend unreachable
        const local = localStorage.getItem('agentforge_settings');
        if (local) {
          try {
            const parsed = JSON.parse(local);
            const keys = Object.values(parsed?.api_keys || {});
            setHasApiKey(keys.length > 0 && keys.some(k => !!k));
          } catch(e) {}
        }
      });
  }, [isSettingsOpen]); // Re-check when settings modal closes

  // Determine which agent is currently active based on the last message
  const activeAgent = useMemo(() => {
    if (messages.length === 0) return null;
    const lastMsg = messages[messages.length - 1];
    return lastMsg.status === 'started' || lastMsg.status === 'working' ? lastMsg.agent : null;
  }, [messages]);

  const { position, direction, state } = useAgentAnimation(activeAgent);

  // Extract server ready URL
  const serverUrl = useMemo(() => {
    const readyMessages = messages.filter(m => m.agent === 'system' && m.status === 'server_ready');
    if (readyMessages.length > 0) {
      return readyMessages[readyMessages.length - 1].data?.url;
    }
    return null;
  }, [messages]);

  // Extract server logs
  const serverLogs = useMemo(() => {
    return messages
      .filter(m => m.agent === 'system' && (m.status === 'server_log' || m.status === 'server_error'))
      .map(m => m.data?.log || '')
      .join('\n');
  }, [messages]);

  const pipelineError = useMemo(() => {
    const errorMessages = messages.filter(m => m.agent === 'system' && m.status === 'error');
    if (errorMessages.length > 0) {
      const data = errorMessages[errorMessages.length - 1].data;
      return typeof data === 'string' ? data : (data?.error || JSON.stringify(data));
    }
    return null;
  }, [messages]);

  const hasStarted = messages.length > 0;

  const handleSelectProject = async (id: string, name: string) => {
    setActiveSessionId(id);
    setActiveProjectName(name);
    setCurrentView('workspace');
    clearMessages();
    try {
      const apiUrl = wsUrl.replace("ws://", "http://").replace("wss://", "https://");
      const res = await fetch(`${apiUrl}/api/projects/${id}`);
      const data = await res.json();
      setChatHistory(data.chat_history || []);
      sendMessage("start_server", { session_id: id });
    } catch (e) {
      console.error(e);
    }
  };

  const handleNewProject = () => {
    setActiveSessionId(null);
    setActiveProjectName(null);
    setCurrentView('workspace');
    clearMessages();
    setChatHistory([]);
  };

  const handleSend = () => {
    if (!prompt.trim() || !hasApiKey) return;
    
    let currentSessionId = activeSessionId;
    if (!currentSessionId) {
      currentSessionId = crypto.randomUUID();
      setActiveSessionId(currentSessionId);
    }
    
    setChatHistory(prev => [...prev, { role: 'user', content: prompt }]);
    clearMessages();
    sendMessage("user_prompt", { prompt, session_id: currentSessionId });
    setPrompt("");
  };



  useEffect(() => {
    if (pipelineError) {
      setChatHistory(prev => {
        if (prev.length > 0 && prev[prev.length - 1].content.includes("Pipeline generation failed")) return prev;
        return [...prev, { role: 'assistant', content: `Pipeline generation failed:\n${pipelineError}` }];
      });
    }
  }, [pipelineError]);

  useEffect(() => {
    const latestMessage = messages[messages.length - 1];
    if (latestMessage?.status === 'chat_message') {
      const content = latestMessage.data?.message;
      if (content) {
        setChatHistory(prev => {
          if (prev.length > 0 && prev[prev.length - 1].content === content) return prev;
          return [...prev, { role: 'assistant', content }];
        });
      }
    }
  }, [messages]);

  return (
    <main className="flex h-screen w-full bg-lovable-cream text-lovable-charcoal font-sans overflow-hidden relative">
      
      {/* Global Top Navigation for Desktop Dashboard */}
      {currentView !== 'workspace' && (
        <header className="absolute top-0 left-0 w-full h-20 px-8 flex items-center justify-between z-40 bg-transparent pointer-events-none">
          <div className="flex items-center gap-4 pointer-events-auto">
            {!isDemo && (
              <button 
                onClick={() => setIsSidebarOpen(true)}
                className="p-2 hover:bg-black/5 dark:hover:bg-white/10 rounded-md transition-colors text-lovable-muted hover:text-lovable-charcoal"
                title="Open Menu"
              >
                <Menu size={24} />
              </button>
            )}
            {currentView === 'projects' && (
              <h1 className="text-xl font-bold text-lovable-charcoal">Projects</h1>
            )}
          </div>
          <div className="flex items-center gap-4 pointer-events-auto">
            {isDemo && (
              <a 
                href="https://github.com/Rishi5377/AgentForge"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 px-4 py-2 rounded-lg text-sm font-bold transition-colors shadow-md text-white"
              >
                Download Desktop App
              </a>
            )}
            {!isDemo && currentView === 'projects' && (
              <button 
                onClick={() => setCurrentView('home')}
                className="flex items-center gap-2 bg-lovable-charcoal hover:opacity-90 px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm text-lovable-cream"
              >
                Create
                <ChevronDown size={14} className="text-lovable-cream/70" />
              </button>
            )}
            <button 
              onClick={() => setIsDarkMode(!isDarkMode)}
              className="p-2 hover:bg-black/5 dark:hover:bg-white/10 rounded-md transition-colors text-lovable-muted hover:text-lovable-charcoal"
              title="Toggle Theme"
            >
              {isDarkMode ? <Sun size={24} /> : <Moon size={24} />}
            </button>
            <div 
              className="flex items-center gap-3 bg-lovable-surface border border-lovable-border rounded-full px-3 py-1.5 shadow-sm cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setIsSettingsOpen(true)}
              title="Settings"
            >
              {isDemo ? (
                <>
                  <Settings size={16} className="text-lovable-charcoal ml-1" />
                  <span className="text-sm font-medium pr-1">Settings</span>
                </>
              ) : (
                <>
                  <div className="w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs font-bold overflow-hidden">
                    <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${username}`} alt="avatar" />
                  </div>
                  <span className="text-sm font-medium">{username}</span>
                </>
              )}
            </div>
          </div>
        </header>
      )}

      {/* Global App Sidebar (Slideout Drawer) */}
      {!isDemo && isSidebarOpen && (
        <div className="absolute inset-y-0 left-0 z-50 shadow-2xl flex">
          <AppSidebar 
            currentView={currentView}
            onNavigate={(view) => setCurrentView(view)}
            onOpenSettings={() => setIsSettingsOpen(true)}
            onClose={() => setIsSidebarOpen(false)}
          />
          <div className="w-screen h-screen absolute left-64 bg-black/20" onClick={() => setIsSidebarOpen(false)} />
        </div>
      )}

      {currentView === 'home' && (
        <HomeView 
          username={username}
          onStartProject={(p) => {
            if (!hasApiKey) {
              // Just transition and populate if no API key yet
              setPrompt(p);
              handleNewProject();
              setCurrentView('workspace');
              return;
            }
            // Auto-send the prompt for a smooth experience
            const newSessionId = crypto.randomUUID();
            setActiveSessionId(newSessionId);
            setActiveProjectName(null);
            setCurrentView('workspace');
            clearMessages();
            setChatHistory([{ role: 'user', content: p }]);
            sendMessage("user_prompt", { prompt: p, session_id: newSessionId });
            setPrompt("");
          }} 
        />
      )}

      {currentView === 'projects' && (
        <ProjectsView 
          onSelectProject={handleSelectProject} 
        />
      )}

      {currentView === 'workspace' && (
        <>
          {/* Left Column: Chat Interface */}
      <section 
        className="flex flex-col h-full bg-lovable-surface flex-shrink-0 transition-colors duration-200"
        style={{ width: leftPanelWidth }}
      >
        
        {/* Header */}
        <header className="flex items-center justify-between p-4 border-b border-lovable-border">
          <div className="flex items-center gap-3">
            {!isDemo && (
              <button 
                onClick={() => setCurrentView('home')}
                className="p-1.5 hover:bg-lovable-cream rounded-md transition-colors text-lovable-muted"
                title="Go to Home"
              >
                <HomeIcon size={18} />
              </button>
            )}
            <h1 className="font-semibold text-sm">{activeProjectName || 'New App'}</h1>
          </div>
          <div className="flex gap-2 items-center">
            {isDemo && (
              <a 
                href="https://github.com/Rishi5377/AgentForge"
                target="_blank"
                rel="noreferrer"
                className="mr-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 px-3 py-1.5 rounded-lg shadow-sm transition-colors"
              >
                Get Desktop App
              </a>
            )}
            <button 
              onClick={() => setIsDarkMode(!isDarkMode)}
              className="p-1.5 hover:bg-lovable-cream rounded-md transition-colors text-lovable-muted"
            >
              {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            {!isDemo && (
              <button className="p-1.5 hover:bg-lovable-cream rounded-md transition-colors text-lovable-muted">
                <Globe size={18} />
              </button>
            )}
          </div>
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-chat-bg">
          
          {/* Dynamic AI Model Configuration Alert */}
          {!hasApiKey && (
            <div className="bg-[#FFF8E6] border border-[#FFE4A0] rounded-xl p-4 shadow-sm mb-4">
              <div className="flex items-center gap-2 text-[#B38000] font-semibold mb-1">
                <Settings size={16} /> AI Model Configuration Required
              </div>
              <p className="text-sm text-[#CC9900] mb-3">
                Please configure your API Key and model settings to get started
              </p>
              <button 
                onClick={() => setIsSettingsOpen(true)}
                className="bg-[#D9A300] hover:bg-[#B38000] text-white text-sm font-medium px-4 py-1.5 rounded-lg transition-colors shadow-sm"
              >
                Open Settings
              </button>
            </div>
          )}

          {chatHistory.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-[14px] leading-relaxed ${
                msg.role === 'user' 
                  ? 'bg-user-bubble text-user-text rounded-tr-sm' 
                  : 'bg-assistant-bubble text-assistant-text shadow-[0_2px_8px_rgba(0,0,0,0.04)] border border-black/[0.04] rounded-tl-sm'
              }`}>
                {msg.role === 'user' ? (
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                ) : (
                  <ChatMessage content={msg.content} />
                )}
              </div>
            </div>
          ))}

          {/* Live Agent Status */}
          {hasStarted && !serverUrl && !pipelineError && activeAgent && (
            <div className="flex flex-col gap-2 w-full">
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-xl p-3 bg-assistant-bubble text-assistant-text flex flex-col gap-1">
                  <div className="flex items-center gap-2 text-xs font-semibold text-lovable-muted uppercase tracking-wider">
                     <div className="w-1.5 h-1.5 bg-lovable-muted rounded-full animate-pulse" />
                     {activeAgent}
                  </div>
                  <div className="text-[13px] text-lovable-charcoal truncate max-w-full">
                     {messages[messages.length - 1]?.status || "Processing..."}
                  </div>
                </div>
              </div>
              
              {streamingContent[activeAgent] && (
                <StreamingCode agentName={activeAgent} content={streamingContent[activeAgent]} />
              )}
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-lovable-border bg-lovable-surface relative transition-colors duration-200">
          {/* Agent Character Pixel Stage */}
          <div className="absolute -top-32 left-0 w-full h-32 overflow-visible pointer-events-none px-4">
            {activeAgent && (
              <AgentSprite 
                agentName={activeAgent} 
                state={state} 
                direction={direction}
                position={position}
              />
            )}
          </div>

          <div className="relative">
            <textarea
              className="w-full bg-lovable-cream border border-lovable-border rounded-xl px-4 py-3 pr-12 text-[14px] focus:outline-none focus:border-lovable-charcoal resize-none placeholder-lovable-muted text-lovable-charcoal block"
              rows={2}
              placeholder="+ Describe the app you want..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <button 
              onClick={handleSend}
              disabled={!isConnected || !hasApiKey}
              className="absolute right-2 bottom-2 p-2 bg-white text-lovable-charcoal hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg border border-lovable-border transition-colors flex items-center justify-center shadow-sm"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </section>

      {/* Resize Handle */}
      <div 
        onMouseDown={handleMouseDown}
        className="w-1 cursor-col-resize hover:bg-lovable-charcoal/20 active:bg-lovable-charcoal/40 bg-lovable-border h-full z-50 flex-shrink-0 transition-colors"
      />

      {/* Right Column: Main Workspace */}
      <section 
        className="flex flex-col flex-1 h-full bg-lovable-cream overflow-hidden"
        style={{ pointerEvents: isDragging ? 'none' : 'auto' }}
      >
        {/* Workspace Content */}
        <div className="flex-1 relative overflow-hidden">
          {!hasStarted ? (
            /* Empty State */
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-8 transition-colors duration-200">
              <div className="bg-lovable-surface p-4 rounded-2xl shadow-lovable border border-lovable-border mb-6">
                <Rocket size={48} className="text-lovable-charcoal" />
              </div>
              <h2 className="text-2xl font-bold text-lovable-charcoal mb-3">Start Building Your Project</h2>
              <p className="text-lovable-muted max-w-md">
                Describe the app you want to create in the left chat box, and AI will generate complete project code for you.
              </p>
            </div>
          ) : (
            /* Active State */
            <div className="w-full h-full">
              <PreviewPanel 
                activeSessionId={activeSessionId}
                serverUrl={serverUrl} 
                serverLogs={serverLogs} 
                pipelineError={pipelineError}
                hasStarted={hasStarted}
              />
            </div>
          )}
        </div>
      </section>
        </>
      )}

      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
    </main>
  );
}
