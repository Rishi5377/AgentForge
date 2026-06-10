import React, { useState } from 'react';
import { Brain, FileCode, Code, ChevronRight, ChevronDown, CheckCircle2 } from 'lucide-react';

interface ChatMessageProps {
  content: string;
}

export default function ChatMessage({ content }: ChatMessageProps) {
  // If no special tags, just return the text
  if (!content.includes('<thinking>') && !content.includes('<file') && !content.includes('<edit')) {
    return <>{content}</>;
  }

  // Parse the content into blocks (text and XML blocks)
  const blocks: { type: 'text' | 'thinking' | 'file' | 'edit'; content: string; path?: string }[] = [];
  
  let currentText = '';
  let i = 0;
  
  while (i < content.length) {
    if (content.substring(i).startsWith('<thinking>')) {
      if (currentText.trim()) blocks.push({ type: 'text', content: currentText });
      currentText = '';
      const endIndex = content.indexOf('</thinking>', i);
      if (endIndex !== -1) {
        blocks.push({ type: 'thinking', content: content.substring(i + 10, endIndex).trim() });
        i = endIndex + 11;
      } else {
        // Unclosed tag
        blocks.push({ type: 'thinking', content: content.substring(i + 10).trim() });
        break;
      }
    } else if (content.substring(i).startsWith('<file path="')) {
      if (currentText.trim()) blocks.push({ type: 'text', content: currentText });
      currentText = '';
      const pathStart = i + 12;
      const pathEnd = content.indexOf('">', pathStart);
      if (pathEnd !== -1) {
        const path = content.substring(pathStart, pathEnd);
        const contentStart = pathEnd + 2;
        const endIndex = content.indexOf('</file>', contentStart);
        if (endIndex !== -1) {
          blocks.push({ type: 'file', path, content: content.substring(contentStart, endIndex).trim() });
          i = endIndex + 7;
        } else {
          blocks.push({ type: 'file', path, content: content.substring(contentStart).trim() });
          break;
        }
      } else {
        currentText += content[i];
        i++;
      }
    } else if (content.substring(i).startsWith('<edit path="')) {
      if (currentText.trim()) blocks.push({ type: 'text', content: currentText });
      currentText = '';
      const pathStart = i + 12;
      const pathEnd = content.indexOf('">', pathStart);
      if (pathEnd !== -1) {
        const path = content.substring(pathStart, pathEnd);
        const contentStart = pathEnd + 2;
        const endIndex = content.indexOf('</edit>', contentStart);
        if (endIndex !== -1) {
          blocks.push({ type: 'edit', path, content: content.substring(contentStart, endIndex).trim() });
          i = endIndex + 7;
        } else {
          blocks.push({ type: 'edit', path, content: content.substring(contentStart).trim() });
          break;
        }
      } else {
        currentText += content[i];
        i++;
      }
    } else {
      currentText += content[i];
      i++;
    }
  }
  
  if (currentText.trim()) {
    blocks.push({ type: 'text', content: currentText });
  }

  return (
    <div className="flex flex-col gap-3">
      {blocks.map((block, index) => {
        if (block.type === 'text') {
          return <span key={index}>{block.content}</span>;
        }
        
        if (block.type === 'thinking') {
          return <ThinkingBlock key={index} content={block.content} />;
        }

        if (block.type === 'file') {
          return (
            <div key={index} className="flex items-center justify-between bg-lovable-cream border border-lovable-border rounded-lg p-3 my-1">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white rounded-md border border-lovable-border shadow-sm">
                  <FileCode size={16} className="text-lovable-primary" />
                </div>
                <div>
                  <div className="text-[13px] font-semibold text-lovable-charcoal">Write File</div>
                  <div className="text-[12px] text-lovable-muted font-mono">{block.path}</div>
                </div>
              </div>
              <CheckCircle2 size={16} className="text-green-500" />
            </div>
          );
        }

        if (block.type === 'edit') {
          return (
            <div key={index} className="flex items-center justify-between bg-lovable-cream border border-lovable-border rounded-lg p-3 my-1">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white rounded-md border border-lovable-border shadow-sm">
                  <Code size={16} className="text-amber-500" />
                </div>
                <div>
                  <div className="text-[13px] font-semibold text-lovable-charcoal">Patch File</div>
                  <div className="text-[12px] text-lovable-muted font-mono">{block.path}</div>
                </div>
              </div>
              <CheckCircle2 size={16} className="text-green-500" />
            </div>
          );
        }
      })}
    </div>
  );
}

function ThinkingBlock({ content }: { content: string }) {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="border border-lovable-border rounded-lg overflow-hidden my-1 bg-white">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2 p-3 text-[13px] font-medium text-lovable-charcoal hover:bg-lovable-cream transition-colors text-left"
      >
        {isOpen ? <ChevronDown size={14} className="text-lovable-muted" /> : <ChevronRight size={14} className="text-lovable-muted" />}
        <Brain size={14} className="text-lovable-muted" />
        Agent Thinking Process
      </button>
      {isOpen && (
        <div className="p-3 border-t border-lovable-border bg-lovable-cream text-[13px] text-lovable-muted whitespace-pre-wrap font-mono">
          {content}
        </div>
      )}
    </div>
  );
}
