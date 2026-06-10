import React, { useEffect, useRef } from 'react';

interface StreamingCodeProps {
  agentName: string;
  content: string;
}

export default function StreamingCode({ agentName, content }: StreamingCodeProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [content]);

  if (!content) return null;

  return (
    <div className="w-full flex flex-col mt-2 max-w-[80%] ml-auto">
      <div className="flex items-center justify-between bg-neutral-800 px-3 py-2 rounded-t-xl border border-lovable-border border-b-0">
        <div className="flex items-center gap-2">
           <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
           <span className="text-xs font-medium text-gray-300 tracking-wide uppercase">{agentName} Output</span>
        </div>
        <div className="flex gap-1.5">
          <div className="w-2 h-2 rounded-full bg-red-500"></div>
          <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
          <div className="w-2 h-2 rounded-full bg-green-500"></div>
        </div>
      </div>
      <div 
        ref={scrollRef}
        className="bg-[#1e1e1e] p-4 rounded-b-xl border border-lovable-border overflow-y-auto max-h-[300px] shadow-lovable"
      >
        <pre className="text-[13px] font-mono text-gray-300 whitespace-pre-wrap break-all leading-relaxed">
          {content}
          <span className="animate-pulse inline-block ml-1 w-2 h-4 bg-gray-400 align-middle"></span>
        </pre>
      </div>
    </div>
  );
}
