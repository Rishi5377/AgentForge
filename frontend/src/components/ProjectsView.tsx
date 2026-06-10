import React, { useState, useEffect } from 'react';
import { Search, Grid, List, ChevronDown, Clock, Link as LinkIcon, Lock, Globe, Edit2, Trash2, Star } from 'lucide-react';

interface Project {
  project_id: string;
  name: string;
  updated_at: string;
}

interface ProjectsViewProps {
  onSelectProject: (projectId: string, projectName: string) => void;
}

export default function ProjectsView({ onSelectProject }: ProjectsViewProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  const [favorites, setFavorites] = useState<string[]>([]);

  const fetchProjects = async () => {
    try {
      const apiUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001").replace('wss://', 'https://').replace('ws://', 'http://');
      const res = await fetch(`${apiUrl}/api/projects`);
      const data = await res.json();
      
      // Map the backend response to our Project interface
      if (Array.isArray(data)) {
        const formattedProjects = data.map((p: any) => ({
          project_id: p.id || p.project_id,
          name: p.name || p.id || p.project_id,
          updated_at: p.updated_at || new Date().toISOString()
        }));
        setProjects(formattedProjects);
      } else if (data && data.projects) {
        const formattedProjects = data.projects.map((p: any) => ({
          project_id: p.project_id,
          name: p.name || p.project_id,
          updated_at: p.updated_at || new Date().toISOString()
        }));
        setProjects(formattedProjects);
      }
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
    const saved = localStorage.getItem('agentforge_favorites');
    if (saved) setFavorites(JSON.parse(saved));
  }, []);

  const handleFavorite = (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    const newFavs = favorites.includes(projectId) ? favorites.filter(id => id !== projectId) : [...favorites, projectId];
    setFavorites(newFavs);
    localStorage.setItem('agentforge_favorites', JSON.stringify(newFavs));
  };

  const handleRename = async (e: React.MouseEvent, projectId: string, currentName: string) => {
    e.stopPropagation();
    const newName = prompt("Enter new project name:", currentName.replace("app_", ""));
    if (!newName) return;
    try {
      const apiUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001").replace('wss://', 'https://').replace('ws://', 'http://');
      await fetch(`${apiUrl}/api/projects/${projectId}/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName })
      });
      fetchProjects();
    } catch (err) {
      console.error("Failed to rename project:", err);
    }
  };

  const handleDelete = async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this project? This cannot be undone.")) return;
    try {
      const apiUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001").replace('wss://', 'https://').replace('ws://', 'http://');
      await fetch(`${apiUrl}/api/projects/${projectId}`, {
        method: 'DELETE'
      });
      fetchProjects();
    } catch (err) {
      console.error("Failed to delete project:", err);
    }
  };

  const filteredProjects = projects.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-full h-full flex flex-col bg-lovable-cream text-lovable-charcoal px-6 md:px-10 pb-6 md:pb-10 pt-20 overflow-y-auto animate-in fade-in duration-300">
      


      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3 mb-8">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-lovable-muted" />
          <input 
            type="text" 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search projects..."
            className="w-full bg-lovable-surface border border-lovable-border text-lovable-charcoal rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-lovable-charcoal transition-colors shadow-sm"
          />
        </div>

        <div className="flex items-center gap-3">
          <select className="bg-lovable-surface border border-lovable-border text-sm text-lovable-charcoal rounded-lg px-3 py-2 outline-none appearance-none cursor-pointer hover:border-lovable-charcoal transition-colors pr-8 relative shadow-sm">
            <option>Last edited</option>
            <option>Created</option>
            <option>Name</option>
          </select>
          
          <select className="bg-lovable-surface border border-lovable-border text-sm text-lovable-charcoal rounded-lg px-3 py-2 outline-none appearance-none cursor-pointer hover:border-lovable-charcoal transition-colors pr-8 shadow-sm">
            <option>Any visibility</option>
            <option>Private</option>
            <option>Public</option>
          </select>

          <select className="bg-lovable-surface border border-lovable-border text-sm text-lovable-charcoal rounded-lg px-3 py-2 outline-none appearance-none cursor-pointer hover:border-lovable-charcoal transition-colors pr-8 shadow-sm">
            <option>Any status</option>
            <option>Active</option>
            <option>Archived</option>
          </select>

          <select className="bg-lovable-surface border border-lovable-border text-sm text-lovable-charcoal rounded-lg px-3 py-2 outline-none appearance-none cursor-pointer hover:border-lovable-charcoal transition-colors pr-8 shadow-sm">
            <option>All creators</option>
            <option>Me</option>
          </select>

          <div className="flex items-center bg-lovable-surface border border-lovable-border rounded-lg p-1 ml-2 shadow-sm">
            <button className="p-1.5 bg-gray-100 dark:bg-gray-800 rounded-md text-lovable-charcoal shadow-sm"><Grid size={16} /></button>
            <button className="p-1.5 text-lovable-muted hover:text-lovable-charcoal rounded-md transition-colors"><List size={16} /></button>
          </div>
        </div>
      </div>

      {/* Grid */}
      <h2 className="text-sm font-semibold text-lovable-muted mb-4">Your Projects</h2>
      
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-4 border-lovable-charcoal/20 border-t-lovable-charcoal rounded-full animate-spin"></div>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="text-center py-20 text-lovable-muted border border-dashed border-lovable-border rounded-xl">
          <p>No projects found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredProjects.map((project) => (
            <div 
              key={project.project_id} 
              onClick={() => onSelectProject(project.project_id, project.name.replace("app_", ""))}
              className="bg-lovable-surface border border-lovable-border rounded-xl overflow-hidden group cursor-pointer hover:border-lovable-charcoal transition-colors flex flex-col shadow-sm"
            >
              <div className="aspect-[4/3] bg-lovable-cream relative flex items-center justify-center overflow-hidden">
                {/* Thumbnail placeholder - would ideally be an actual screenshot */}
                <div className="absolute inset-0 bg-gradient-to-br from-lovable-cream to-lovable-surface opacity-50"></div>
                <Globe className="text-lovable-muted w-12 h-12 opacity-50 group-hover:scale-110 transition-transform duration-500" />
                <div className="absolute top-3 right-3 bg-white/80 dark:bg-black/40 backdrop-blur-md px-2 py-1 rounded-md text-xs font-medium text-lovable-charcoal flex items-center gap-1 border border-lovable-border">
                  <Lock size={10} /> Private
                </div>
              </div>
              <div className="p-4 flex items-center justify-between gap-2">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-full bg-blue-500 flex-shrink-0 flex items-center justify-center text-xs overflow-hidden">
                     <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=rishi" alt="avatar" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm text-lovable-charcoal truncate group-hover:opacity-80 transition-opacity">
                      {project.name.replace("app_", "")}
                    </h3>
                    <p className="text-xs text-lovable-muted mt-0.5 truncate">
                      Updated {new Date(project.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                  <button 
                    onClick={(e) => handleFavorite(e, project.project_id)}
                    className="p-1.5 text-lovable-muted hover:text-yellow-500 hover:bg-yellow-50 dark:hover:bg-yellow-500/10 rounded-md transition-colors"
                    title="Favorite"
                  >
                    <Star size={14} className={favorites.includes(project.project_id) ? "fill-yellow-500 text-yellow-500" : ""} />
                  </button>
                  <button 
                    onClick={(e) => handleRename(e, project.project_id, project.name)}
                    className="p-1.5 text-lovable-muted hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-md transition-colors"
                    title="Edit"
                  >
                    <Edit2 size={14} />
                  </button>
                  <button 
                    onClick={(e) => handleDelete(e, project.project_id)}
                    className="p-1.5 text-lovable-muted hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-md transition-colors"
                    title="Delete"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
