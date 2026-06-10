import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';

interface CodeEditorProps {
  content: string;
  onChange: (value: string | undefined) => void;
  language?: string;
  readOnly?: boolean;
}

export default function CodeEditor({ content, onChange, language = 'typescript', readOnly = false }: CodeEditorProps) {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Check initial state
    setIsDark(document.documentElement.classList.contains('dark'));
    
    // Observer for class changes on html element
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          setIsDark(document.documentElement.classList.contains('dark'));
        }
      });
    });
    
    observer.observe(document.documentElement, { attributes: true });
    return () => observer.disconnect();
  }, []);
  return (
    <div className="w-full h-full flex-1">
      <Editor
        height="100%"
        language={language}
        value={content}
        onChange={onChange}
        theme={isDark ? "vs-dark" : "light"}
        options={{
          minimap: { enabled: false },
          fontSize: 13,
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
          wordWrap: 'on',
          readOnly: readOnly,
          padding: { top: 16, bottom: 16 },
          scrollBeyondLastLine: false,
          smoothScrolling: true,
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          formatOnPaste: true,
          renderLineHighlight: 'all',
          lineHeight: 21,
          suggest: {
            showKeywords: false,
            showSnippets: false,
          }
        }}
      />
    </div>
  );
}
