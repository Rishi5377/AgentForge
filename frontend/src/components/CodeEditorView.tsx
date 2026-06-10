import React, { useState, useEffect } from 'react';
import FileExplorer from './FileExplorer';
import CodeEditor from './CodeEditor';

interface CodeEditorViewProps {
  activeSessionId: string | null;
}

export default function CodeEditorView({ activeSessionId }: CodeEditorViewProps) {
  const [files, setFiles] = useState<string[]>([]);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);

  // Fetch file list when session changes
  useEffect(() => {
    if (activeSessionId) {
      const apiUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001").replace('wss://', 'https://').replace('ws://', 'http://');
      fetch(`${apiUrl}/api/projects/${activeSessionId}/files`)
        .then(res => res.json())
        .then(data => {
          if (data.files) {
            setFiles(data.files);
          }
        })
        .catch(err => console.error("Error fetching files", err));
    } else {
      setFiles([]);
      setActiveFile(null);
      setFileContent('');
    }
  }, [activeSessionId]);

  // Fetch file content when active file changes
  useEffect(() => {
    if (activeSessionId && activeFile) {
      const apiUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001").replace('wss://', 'https://').replace('ws://', 'http://');
      fetch(`${apiUrl}/api/projects/${activeSessionId}/files/read?path=${encodeURIComponent(activeFile)}`)
        .then(res => res.json())
        .then(data => {
          if (data.content !== undefined) {
            setFileContent(data.content);
          }
        })
        .catch(err => console.error("Error reading file", err));
    } else {
      setFileContent('');
    }
  }, [activeSessionId, activeFile]);

  const handleContentChange = (newContent: string | undefined) => {
    if (newContent !== undefined) {
      setFileContent(newContent);
    }
  };

  const saveFile = async () => {
    if (!activeSessionId || !activeFile) return;
    setIsSaving(true);
    try {
      const apiUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001").replace('wss://', 'https://').replace('ws://', 'http://');
      await fetch(`${apiUrl}/api/projects/${activeSessionId}/files/write`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: activeFile,
          content: fileContent
        })
      });
    } catch (err) {
      console.error("Error writing file", err);
    } finally {
      setIsSaving(false);
    }
  };

  // Keyboard shortcut for saving (Cmd+S or Ctrl+S)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        saveFile();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [fileContent, activeFile, activeSessionId]);

  // Determine language based on file extension
  const getLanguage = (filename: string | null) => {
    if (!filename) return 'text';
    if (filename.endsWith('.ts') || filename.endsWith('.tsx')) return 'typescript';
    if (filename.endsWith('.js') || filename.endsWith('.jsx')) return 'javascript';
    if (filename.endsWith('.html')) return 'html';
    if (filename.endsWith('.css')) return 'css';
    if (filename.endsWith('.json')) return 'json';
    if (filename.endsWith('.md')) return 'markdown';
    return 'text';
  };

  return (
    <div className="flex w-full h-full bg-lovable-surface overflow-hidden">
      <FileExplorer 
        files={files} 
        activeFile={activeFile} 
        onSelectFile={setActiveFile} 
      />
      
      <div className="flex-1 flex flex-col h-full bg-lovable-cream">
        {/* File Header Tab */}
        <div className="h-10 bg-lovable-cream border-b border-lovable-border flex items-center px-4 justify-between shrink-0">
          <div className="flex items-center">
            {activeFile ? (
              <div className="flex items-center gap-2 px-3 py-1 bg-lovable-surface border border-lovable-border border-b-0 rounded-t-md text-sm font-medium text-lovable-charcoal mt-1 relative top-[1px]">
                {activeFile.split('/').pop()}
              </div>
            ) : (
              <span className="text-sm text-lovable-muted">No file selected</span>
            )}
          </div>
          
          {activeFile && (
            <button 
              onClick={saveFile}
              disabled={isSaving}
              className="text-xs px-2 py-1 bg-lovable-surface border border-lovable-border rounded hover:bg-black/5 dark:hover:bg-white/10 text-lovable-charcoal transition-colors disabled:opacity-50"
            >
              {isSaving ? 'Saving...' : 'Save (⌘S)'}
            </button>
          )}
        </div>

        {/* Editor Area */}
        {activeFile ? (
          <div className="flex-1 w-full bg-lovable-surface relative">
            <CodeEditor 
              content={fileContent} 
              onChange={handleContentChange}
              language={getLanguage(activeFile)}
            />
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-lovable-muted bg-lovable-surface">
            <p>Select a file from the explorer to view code.</p>
          </div>
        )}
      </div>
    </div>
  );
}
