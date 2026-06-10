import React, { useMemo, useState } from 'react';
import { ChevronRight, ChevronDown, Folder, FileCode, FileImage, FileText, Settings } from 'lucide-react';

const getFileIcon = (filename: string, size: number = 14) => {
  const name = filename.toLowerCase();
  if (name.endsWith('.ts') || name.endsWith('.tsx') || name.endsWith('.js') || name.endsWith('.jsx')) {
    const isTS = name.endsWith('.ts') || name.endsWith('.tsx');
    return <FileCode size={size} className={isTS ? "text-blue-500" : "text-yellow-500"} />;
  }
  if (name.endsWith('.json')) return <FileCode size={size} className="text-green-500" />;
  if (name.endsWith('.css')) return <FileCode size={size} className="text-blue-400" />;
  if (name.endsWith('.html')) return <FileCode size={size} className="text-orange-500" />;
  if (name.endsWith('.svg') || name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.ico')) {
    return <FileImage size={size} className="text-purple-400" />;
  }
  if (name.includes('config') || name === 'package.json') {
    return <Settings size={size} className="text-gray-500" />;
  }
  return <FileText size={size} className="text-lovable-muted" />;
};

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: { [key: string]: FileNode };
}

interface FileExplorerProps {
  files: string[];
  activeFile: string | null;
  onSelectFile: (path: string) => void;
}

export default function FileExplorer({ files, activeFile, onSelectFile }: FileExplorerProps) {
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set(['src']));

  const fileTree = useMemo(() => {
    const root: FileNode = { name: 'root', path: '', type: 'directory', children: {} };
    files.forEach(filePath => {
      const parts = filePath.split('/');
      let current = root;
      let currentPath = '';
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        currentPath = currentPath ? `${currentPath}/${part}` : part;
        if (!current.children![part]) {
          current.children![part] = {
            name: part,
            path: currentPath,
            type: i === parts.length - 1 ? 'file' : 'directory',
            ...(i < parts.length - 1 ? { children: {} } : {})
          };
        }
        current = current.children![part];
      }
    });
    return root.children || {};
  }, [files]);

  const toggleDir = (path: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const next = new Set(expandedDirs);
    if (next.has(path)) next.delete(path);
    else next.add(path);
    setExpandedDirs(next);
  };

  const renderNode = (node: FileNode, depth = 0) => {
    const isExpanded = expandedDirs.has(node.path);
    const isActive = activeFile === node.path;

    if (node.type === 'directory') {
      return (
        <div key={node.path}>
          <div 
            className={`flex items-center gap-1 py-1 px-2 cursor-pointer transition-colors text-sm hover:bg-black/5 dark:hover:bg-white/10 text-lovable-charcoal rounded-md`}
            style={{ paddingLeft: `${depth * 12 + 8}px` }}
            onClick={(e) => toggleDir(node.path, e)}
          >
            {isExpanded ? <ChevronDown size={14} className="text-lovable-muted" /> : <ChevronRight size={14} className="text-lovable-muted" />}
            <Folder size={14} className="text-lovable-charcoal" />
            <span className="truncate">{node.name}</span>
          </div>
          {isExpanded && node.children && (
            <div>
              {Object.values(node.children)
                .sort((a, b) => {
                  if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
                  return a.name.localeCompare(b.name);
                })
                .map(child => renderNode(child, depth + 1))}
            </div>
          )}
        </div>
      );
    }

    return (
      <div 
        key={node.path}
        className={`flex items-center gap-2 py-1 px-2 cursor-pointer transition-colors text-sm rounded-md ${isActive ? 'bg-lovable-charcoal/10 text-lovable-charcoal font-medium' : 'hover:bg-black/5 dark:hover:bg-white/10 text-lovable-muted hover:text-lovable-charcoal'}`}
        style={{ paddingLeft: `${depth * 12 + 24}px` }}
        onClick={() => onSelectFile(node.path)}
      >
        {getFileIcon(node.name)}
        <span className="truncate">{node.name}</span>
      </div>
    );
  };

  if (files.length === 0) {
    return <div className="p-4 text-sm text-lovable-muted text-center">No files to display</div>;
  }

  return (
    <div className="flex flex-col h-full bg-lovable-surface border-r border-lovable-border overflow-y-auto w-64 flex-shrink-0 pt-2 pb-4">
      <div className="px-4 py-2 text-xs font-semibold uppercase tracking-wider text-lovable-muted">
        Explorer
      </div>
      <div className="px-2">
        {Object.values(fileTree)
          .sort((a, b) => {
            if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
            return a.name.localeCompare(b.name);
          })
          .map(node => renderNode(node, 0))}
      </div>
    </div>
  );
}
