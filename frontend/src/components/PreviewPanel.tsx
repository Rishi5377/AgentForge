import React, { useState, useEffect } from 'react';
import { Play, Save, ExternalLink, RefreshCw, Monitor, Tablet, Smartphone } from 'lucide-react';

const GithubIcon = ({ size = 24, className = '' }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);
import FileExplorer from './FileExplorer';
import CodeEditor from './CodeEditor';
import GitHubSyncModal from './GitHubSyncModal';

const isDemo = process.env.NEXT_PUBLIC_IS_DEMO === 'true';

interface PreviewPanelProps {
  activeSessionId?: string | null;
  serverUrl?: string | null;
  serverLogs?: string | null;
  pipelineError?: string | null;
  hasStarted?: boolean;
}

export default function PreviewPanel({ activeSessionId, serverUrl, serverLogs, pipelineError, hasStarted }: PreviewPanelProps) {
  const [activeTab, setActiveTab] = useState<'preview' | 'code' | 'console'>('preview');
  const [deviceMode, setDeviceMode] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [iframeKey, setIframeKey] = useState(0);

  const [files, setFiles] = useState<string[]>([]);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isGithubModalOpen, setIsGithubModalOpen] = useState(false);



  // Fetch files when active tab is code
  useEffect(() => {
    if (activeTab === 'code' && activeSessionId) {
      const apiUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001").replace('wss://', 'https://').replace('ws://', 'http://');
      fetch(`${apiUrl}/api/projects/${activeSessionId}/files`)
        .then(res => res.json())
        .then(data => {
          if (data.files) setFiles(data.files);
        })
        .catch(console.error);
    }
  }, [activeTab, activeSessionId]);

  // Read active file
  useEffect(() => {
    if (activeFile && activeSessionId) {
      const apiUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001").replace('wss://', 'https://').replace('ws://', 'http://');
      fetch(`${apiUrl}/api/projects/${activeSessionId}/files/read?path=${encodeURIComponent(activeFile)}`)
        .then(res => res.json())
        .then(data => {
          if (data.content !== undefined) setFileContent(data.content);
        })
        .catch(console.error);
    }
  }, [activeFile, activeSessionId]);

  const handleSaveFile = async () => {
    if (!activeFile || !activeSessionId) return;
    setIsSaving(true);
    try {
      const apiUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001").replace('wss://', 'https://').replace('ws://', 'http://');
      await fetch(`${apiUrl}/api/projects/${activeSessionId}/files/write`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: activeFile, content: fileContent })
      });
    } catch (e) {
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadProject = async () => {
    if (!activeSessionId) return;
    setIsDownloading(true);
    try {
      const apiUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001").replace('wss://', 'https://').replace('ws://', 'http://');
      const response = await fetch(`${apiUrl}/api/projects/${activeSessionId}/download`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `project_${activeSessionId}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        console.error("Download failed");
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <section className="flex flex-col flex-1 h-full bg-lovable-cream">
      <header className="flex items-center justify-between p-4 bg-lovable-cream border-b border-lovable-border z-20">
        <div className="flex gap-4 text-[15px] font-medium items-center">
          <button 
            className={`pb-1 transition-colors ${activeTab === 'preview' ? 'text-lovable-charcoal border-b-2 border-lovable-charcoal' : 'text-lovable-muted hover:text-lovable-charcoal'}`}
            onClick={() => setActiveTab('preview')}
          >
            Preview
          </button>
          <button 
            className={`pb-1 transition-colors ${activeTab === 'code' ? 'text-lovable-charcoal border-b-2 border-lovable-charcoal' : 'text-lovable-muted hover:text-lovable-charcoal'}`}
            onClick={() => setActiveTab('code')}
          >
            Code
          </button>
          <button 
            className={`pb-1 transition-colors ${activeTab === 'console' ? 'text-lovable-charcoal border-b-2 border-lovable-charcoal' : 'text-lovable-muted hover:text-lovable-charcoal'}`}
            onClick={() => setActiveTab('console')}
          >
            Console
          </button>
          
          {serverUrl && activeTab === 'preview' && (
            <div className="flex items-center gap-1 ml-2">
              <button 
                onClick={() => {
                  const fullUrl = serverUrl.startsWith('/preview/') ? `${(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001').replace('wss://', 'https://').replace('ws://', 'http://').replace(/\/$/, '') || window.location.origin}${serverUrl}` : serverUrl;
                  window.open(fullUrl, '_blank');
                }}
                className="p-1.5 text-lovable-muted hover:text-lovable-charcoal hover:bg-white radius-lovable-standard transition-colors shadow-lovable"
                title="Open in new tab"
              >
                <ExternalLink size={16} />
              </button>
              <button 
                onClick={() => setIframeKey(prev => prev + 1)}
                className="p-1.5 text-lovable-muted hover:text-lovable-charcoal hover:bg-white radius-lovable-standard transition-colors shadow-lovable"
                title="Refresh preview"
              >
                <RefreshCw size={16} />
              </button>
            </div>
          )}
          
          {activeTab === 'preview' && (
            <div className="flex items-center ml-4 bg-white border border-lovable-border rounded-lg shadow-lovable p-0.5">
              <button 
                onClick={() => setDeviceMode('desktop')}
                className={`p-1.5 rounded-md transition-colors ${deviceMode === 'desktop' ? 'bg-lovable-border text-lovable-charcoal' : 'text-lovable-muted hover:text-lovable-charcoal'}`}
                title="Desktop"
              >
                <Monitor size={14} />
              </button>
              <button 
                onClick={() => setDeviceMode('tablet')}
                className={`p-1.5 rounded-md transition-colors ${deviceMode === 'tablet' ? 'bg-lovable-border text-lovable-charcoal' : 'text-lovable-muted hover:text-lovable-charcoal'}`}
                title="Tablet"
              >
                <Tablet size={14} />
              </button>
              <button 
                onClick={() => setDeviceMode('mobile')}
                className={`p-1.5 rounded-md transition-colors ${deviceMode === 'mobile' ? 'bg-lovable-border text-lovable-charcoal' : 'text-lovable-muted hover:text-lovable-charcoal'}`}
                title="Mobile"
              >
                <Smartphone size={14} />
              </button>
            </div>
          )}
        </div>
        <div className="flex gap-3">
          {activeTab === 'code' && activeFile && (
            <button 
              onClick={handleSaveFile}
              disabled={isSaving}
              className="flex items-center gap-2 px-4 py-2 text-[14px] bg-lovable-surface border border-lovable-border hover:bg-lovable-border radius-lovable-pill transition-colors text-lovable-charcoal shadow-lovable disabled:opacity-50"
            >
              <Save size={14} /> {isSaving ? 'Saving...' : 'Save File'}
            </button>
          )}
          {activeTab !== 'code' && (
            <>
              <button 
                onClick={handleDownloadProject}
                disabled={isDownloading}
                className="flex items-center gap-2 px-4 py-2 text-[14px] bg-lovable-surface border border-lovable-border hover:bg-lovable-border radius-lovable-pill transition-colors text-lovable-charcoal shadow-lovable disabled:opacity-50"
              >
                <Save size={14} /> {isDownloading ? 'Downloading...' : 'Download Project'}
              </button>
              {!isDemo && (
                <button 
                  onClick={() => setIsGithubModalOpen(true)}
                  disabled={!activeSessionId}
                  className="flex items-center gap-2 px-4 py-2 text-[14px] bg-[#2a2a35] hover:bg-[#3a3a45] radius-lovable-pill transition-colors text-white shadow-lovable disabled:opacity-50"
                >
                  <GithubIcon size={14} /> GitHub Log
                </button>
              )}
            </>
          )}

        </div>
      </header>

      <div className="flex-1 overflow-hidden relative p-4 flex">
        {activeTab === 'preview' && (
          <div className="w-full h-full flex flex-col items-center overflow-y-auto">
            <div 
              className={`bg-white rounded-xl shadow-lovable border border-lovable-border flex flex-col overflow-hidden transition-all duration-300 ${
                deviceMode === 'desktop' ? 'w-full h-full' : 
                deviceMode === 'tablet' ? 'w-[768px] h-[1024px] max-h-full' : 
                'w-[375px] h-[812px] max-h-full'
              }`}
            >
              {serverUrl ? (
                <iframe 
                  key={iframeKey}
                  src={serverUrl.startsWith('/preview/') ? `${(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001').replace('wss://', 'https://').replace('ws://', 'http://').replace(/\/$/, '') || window.location.origin}${serverUrl}` : serverUrl} 
                  className="w-full h-full border-none"
                  title="Preview"
                  sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
                />
            ) : pipelineError ? (
              <div className="flex items-center justify-center h-full flex-col p-8 text-center bg-lovable-surface">
                <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mb-4 border border-red-100">
                  <span className="text-red-500 text-2xl">⚠️</span>
                </div>
                <p className="mb-2 font-medium text-red-600">Pipeline Generation Failed</p>
                <p className="text-[13px] text-lovable-muted">{pipelineError}</p>
              </div>
            ) : hasStarted ? (
              <div className="flex items-center justify-center h-full flex-col bg-lovable-surface">
                <div className="w-8 h-8 border-2 border-lovable-border border-t-lovable-charcoal rounded-full animate-spin mb-4" />
                <p className="mb-2 font-medium text-lovable-charcoal">Preview Not Ready</p>
                <p className="text-[13px] text-lovable-muted">Waiting for AgentForge to start the local dev server...</p>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full flex-col bg-lovable-surface">
                <p className="mb-2 font-medium text-lovable-charcoal">Ready to Build</p>
                <p className="text-[13px] text-lovable-muted">Send a prompt to start generating your app.</p>
              </div>
            )}
            </div>
          </div>
        )}

        {activeTab === 'code' && (
          <div className="w-full h-full bg-lovable-surface rounded-xl shadow-lovable border border-lovable-border flex overflow-hidden">
            <FileExplorer 
              files={files}
              activeFile={activeFile}
              onSelectFile={setActiveFile}
            />
            <div className="flex-1 bg-lovable-cream flex flex-col relative">
              {activeFile ? (
                <>
                  <div className="h-10 border-b border-lovable-border flex items-center px-4 bg-lovable-surface text-sm font-medium text-lovable-charcoal shrink-0">
                    {activeFile.split('/').pop()}
                  </div>
                  <CodeEditor 
                    content={fileContent}
                    onChange={(val) => setFileContent(val || '')}
                    language={activeFile.endsWith('.ts') || activeFile.endsWith('.tsx') ? 'typescript' : 
                              activeFile.endsWith('.css') ? 'css' : 
                              activeFile.endsWith('.json') ? 'json' : 
                              activeFile.endsWith('.html') ? 'html' : 'javascript'}
                  />
                </>
              ) : (
                <div className="flex items-center justify-center h-full text-lovable-muted text-sm">
                  Select a file to view code
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'console' && (
          <div className="w-full p-6 overflow-y-auto h-full text-[13px] font-mono text-lovable-muted bg-lovable-surface rounded-xl shadow-lovable border border-lovable-border whitespace-pre-wrap">
            {serverLogs || "No logs available yet."}
          </div>
        )}
      </div>

      <GitHubSyncModal 
        isOpen={isGithubModalOpen} 
        onClose={() => setIsGithubModalOpen(false)} 
        projectId={activeSessionId || ""} 
      />
    </section>
  );
}
