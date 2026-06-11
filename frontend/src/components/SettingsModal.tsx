import React, { useState, useEffect, useMemo } from 'react';
import { X, Settings as SettingsIcon, Key, Globe } from 'lucide-react';

// Design tokens based on CSS variables to sync with theme
const tokens = {
  colors: {
    cream: 'var(--color-lovable-cream)',
    charcoal: 'var(--color-lovable-charcoal)',
    surface: 'var(--color-lovable-surface)',
    mutedGray: 'var(--color-lovable-muted)',
    borderPassive: 'var(--color-lovable-border)',
    borderInteractive: 'var(--color-lovable-muted)',
    focusRing: 'rgba(59,130,246,0.5)',
  },
  shadows: {
    primaryButton: 'rgba(255,255,255,0.2) 0px 0.5px 0px 0px inset, rgba(0,0,0,0.2) 0px 0px 0px 0.5px inset, rgba(0,0,0,0.05) 0px 1px 2px 0px',
    focus: 'rgba(0,0,0,0.1) 0px 4px 12px'
  }
};

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const isDemo = process.env.NEXT_PUBLIC_IS_DEMO === 'true';
  const [username, setUsername] = useState('');
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [availableModels, setAvailableModels] = useState<any>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const API_URL = (process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001').replace('wss://', 'https://').replace('ws://', 'http://');
    if (isOpen) {
      // Fetch available models
      fetch(`${API_URL}/api/models`)
        .then(res => res.json())
        .then(data => setAvailableModels(data))
        .catch(e => console.warn("Could not fetch models", e));

      // Fetch local username
      const savedUser = localStorage.getItem('agentforge_username');
      if (savedUser) setUsername(savedUser);

      // Fetch existing settings and try to populate the simplified view
      fetch(`${API_URL}/api/settings`)
        .then(res => res.json())
        .then(data => {
          if (data?.models?.supervisor_provider) {
            setProvider(data.models.supervisor_provider);
            setModel(data.models.supervisor_model || '');
          }
          if (data?.api_keys) {
            // Find the first api key that exists
            const existingKey = data.api_keys[data.models?.supervisor_provider || 'openai'];
            if (existingKey) setApiKey(existingKey);
          }
        })
        .catch(e => console.warn("Could not fetch settings", e));
    }
  }, [isOpen]);

  const currentModels = useMemo(() => {
    if (provider && availableModels[provider]) {
      return availableModels[provider];
    }
    // Fallbacks if API is unreachable
    if (provider === 'openai') return ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'];
    if (provider === 'anthropic') return ['claude-3-5-sonnet-latest', 'claude-3-opus-latest', 'claude-3-haiku-latest'];
    if (provider === 'gemini') return ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro', 'gemini 3.1 Flash-Lite', 'Gemini 3.5 Flash'];
    if (provider === 'groq') return ['llama3-70b-8192', 'mixtral-8x7b-32768'];
    return [];
  }, [provider, availableModels]);



  if (!isOpen) return null;

  const handleSave = async () => {
    setSaving(true);

    // Map the simplified global setting to all internal agents
    const agents = ['supervisor', 'frontend', 'backend', 'db', 'assembler'];
    const modelsObj: Record<string, string> = {};
    agents.forEach(agent => {
      modelsObj[`${agent}_provider`] = provider;
      modelsObj[`${agent}_model`] = model;
    });

    const settingsPayload = {
      models: modelsObj,
      api_keys: {
        [provider]: apiKey
      },
      general: {
        preview_port: 5173
      }
    };

    localStorage.setItem('agentforge_username', username);
    window.dispatchEvent(new Event('storage')); // Optional: if we listen for it, or just let page.tsx reload. Actually we can just let it be, but setting localStorage is enough for a page refresh or subsequent loads.

    try {
      const API_URL = (process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001').replace('wss://', 'https://').replace('ws://', 'http://');
      await fetch(`${API_URL}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settingsPayload)
      });
    } catch (e) {
      console.warn("Failed to save to backend, falling back to localStorage", e);
      localStorage.setItem('agentforge_settings', JSON.stringify(settingsPayload));
    }

    setSaving(false);
    onClose();
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(28,28,28,0.4)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div style={{
        backgroundColor: tokens.colors.cream,
        border: `1px solid ${tokens.colors.borderPassive}`,
        borderRadius: '16px',
        width: '500px',
        maxWidth: '90vw',
        display: 'flex',
        flexDirection: 'column',
        fontFamily: 'ui-sans-serif, system-ui, sans-serif',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
      }}>
        {/* Header */}
        <div style={{ padding: '20px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 600, color: tokens.colors.charcoal, letterSpacing: '-0.5px' }}>
              {isDemo ? 'Welcome to AgentForge Demo ✨' : 'Settings'}
            </h2>
            {isDemo && (
              <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: tokens.colors.mutedGray }}>
                Please provide an API key to experience the magic.
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: tokens.colors.mutedGray }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '0 24px 24px 24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>

          {/* Username */}
          {!isDemo && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '13px', fontWeight: 500, color: tokens.colors.charcoal, display: 'flex', alignItems: 'center', gap: '6px' }}>
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. rishi077"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: `1px solid ${tokens.colors.borderPassive}`,
                  backgroundColor: 'transparent',
                  color: tokens.colors.charcoal,
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                  boxSizing: 'border-box'
                }}
                onFocus={(e) => e.target.style.borderColor = tokens.colors.focusRing}
                onBlur={(e) => e.target.style.borderColor = tokens.colors.borderPassive}
              />
            </div>
          )}

          {/* API Type */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: tokens.colors.charcoal, fontSize: '14px', fontWeight: 600 }}>
              <SettingsIcon size={16} /> API Type
            </label>
            <select
              value={provider}
              onChange={e => {
                const newProvider = e.target.value;
                setProvider(newProvider);
                setModel(''); // Clear the model so the user can pick
                setApiKey(''); // Clear the API key so the user can enter the key for the new provider
              }}
              style={{
                width: '100%', padding: '10px 12px', borderRadius: '8px',
                border: `1px solid ${tokens.colors.borderPassive}`,
                backgroundColor: tokens.colors.surface,
                color: tokens.colors.charcoal,
                fontSize: '14px',
                outline: 'none',
                boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
              }}
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="gemini">Google Gemini</option>
              <option value="groq">Groq</option>
            </select>
            <p style={{ margin: 0, fontSize: '12px', color: tokens.colors.mutedGray }}>Select the AI provider</p>
          </div>

          {/* API Key */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: tokens.colors.charcoal, fontSize: '14px', fontWeight: 600 }}>
              <Key size={16} /> API Key
            </label>
            <input
              type="password"
              placeholder={`sk-...`}
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              style={{
                width: '100%', padding: '10px 12px', borderRadius: '8px',
                border: `1px solid ${tokens.colors.borderPassive}`,
                backgroundColor: tokens.colors.surface,
                color: tokens.colors.charcoal,
                fontSize: '14px',
                outline: 'none',
                boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                boxSizing: 'border-box'
              }}
            />
            <p style={{ margin: 0, fontSize: '12px', color: tokens.colors.mutedGray }}>Your API key will be saved in browser local storage</p>
          </div>

          {/* Model Name */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', position: 'relative' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: tokens.colors.charcoal, fontSize: '14px', fontWeight: 600 }}>
              <Globe size={16} /> Model
            </label>
            <input
              value={model}
              onChange={e => {
                setModel(e.target.value);
                setShowDropdown(true);
              }}
              onFocus={() => setShowDropdown(true)}
              onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
              placeholder="Select or type a model..."
              style={{
                width: '100%', padding: '10px 12px', borderRadius: '8px',
                border: `1px solid ${tokens.colors.borderPassive}`,
                backgroundColor: tokens.colors.surface,
                color: tokens.colors.charcoal,
                fontSize: '14px',
                outline: 'none',
                boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                boxSizing: 'border-box'
              }}
            />
            {showDropdown && currentModels.length > 0 && (
              <div style={{
                position: 'absolute', top: '70px', left: 0, right: 0,
                backgroundColor: tokens.colors.surface,
                border: `1px solid ${tokens.colors.borderPassive}`,
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                zIndex: 10,
                maxHeight: '150px',
                overflowY: 'auto'
              }}>
                {currentModels.map((m: string) => (
                  <div 
                    key={m}
                    onClick={() => {
                      setModel(m);
                      setShowDropdown(false);
                    }}
                    style={{
                      padding: '10px 12px', cursor: 'pointer', fontSize: '14px',
                      color: tokens.colors.charcoal,
                      borderBottom: `1px solid ${tokens.colors.borderPassive}33`
                    }}
                    onMouseEnter={e => e.currentTarget.style.backgroundColor = `${tokens.colors.charcoal}11`}
                    onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    {m}
                  </div>
                ))}
              </div>
            )}
            <p style={{ margin: 0, fontSize: '12px', color: tokens.colors.mutedGray }}>Select the specific model to use</p>
          </div>

        </div>

        {/* Footer */}
        <div style={{ padding: '20px 24px', borderTop: `1px solid ${tokens.colors.borderPassive}`, display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            onClick={onClose}
            style={{
              padding: '10px 16px', borderRadius: '8px', fontSize: '14px', fontWeight: 500,
              backgroundColor: 'transparent', color: tokens.colors.charcoal, border: 'none', cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            style={{
              padding: '10px 20px', borderRadius: '8px', fontSize: '14px', fontWeight: 500,
              backgroundColor: tokens.colors.charcoal,
              color: tokens.colors.cream,
              border: 'none',
              cursor: 'pointer',
              boxShadow: tokens.shadows.primaryButton,
              opacity: saving ? 0.8 : 1
            }}
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
