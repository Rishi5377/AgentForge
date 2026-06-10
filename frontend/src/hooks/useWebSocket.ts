import { useState, useEffect, useCallback, useRef } from 'react';
import { AgentEvent } from '@/lib/types';

export function useWebSocket(url: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [messages, setMessages] = useState<AgentEvent[]>([]);
  const [streamingContent, setStreamingContent] = useState<Record<string, string>>({});
  const [isConnected, setIsConnected] = useState(false);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);

  // Load from localStorage only after mounting on the client to avoid SSR hydration mismatch
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const cached = localStorage.getItem('agentforge_messages');
      if (cached) {
        try {
          setMessages(JSON.parse(cached));
        } catch {
          // ignore
        }
      }
    }
  }, []);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket Connected');
        
        // Keep-alive heartbeat to prevent HF Spaces / Nginx from dropping the connection
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
        
        (ws as any)._pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        try {
          const data: AgentEvent = JSON.parse(event.data);
          
          if (data.status === 'streaming') {
            setStreamingContent(prev => ({
              ...prev,
              [data.agent]: (prev[data.agent] || '') + data.data.token
            }));
            return;
          }
          
          if (data.status === 'working' || data.status === 'started') {
            setStreamingContent(prev => ({...prev, [data.agent]: ''}));
          }

          setMessages((prev) => {
            const next = [...prev, data];
            if (typeof window !== 'undefined') {
              try {
                // To prevent QuotaExceededError, truncate large strings in the data payload before saving to localStorage
                const minimalNext = next.map(msg => {
                  const newMsg = { ...msg, data: { ...msg.data } };
                  if (newMsg.data) {
                    for (const key in newMsg.data) {
                      if (typeof newMsg.data[key] === 'string' && newMsg.data[key].length > 500) {
                        newMsg.data[key] = newMsg.data[key].substring(0, 500) + "... [truncated]";
                      }
                    }
                  }
                  return newMsg;
                });
                localStorage.setItem('agentforge_messages', JSON.stringify(minimalNext));
              } catch (e) {
                console.warn('Failed to persist messages to localStorage', e);
              }
            }
            return next;
          });
        } catch (e) {
          console.error('Error parsing WebSocket message', e);
        }
      };

      ws.onclose = () => {
        if ((ws as any)._pingInterval) clearInterval((ws as any)._pingInterval);
        setIsConnected(false);
        console.log('WebSocket Disconnected. Reconnecting in 3s...');
        reconnectTimeout.current = setTimeout(connect, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket Error:', error);
        ws.close();
      };

      setSocket(ws);
    } catch (error) {
      console.error('Failed to connect WebSocket', error);
    }
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (socket) socket.close();
    };
  }, [connect]);

  const sendMessage = useCallback(
    (type: string, payload: any) => {
      if (socket && isConnected) {
        socket.send(JSON.stringify({ type, ...payload }));
      } else {
        console.warn('Cannot send message: WebSocket is not connected');
      }
    },
    [socket, isConnected]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('agentforge_messages');
    }
  }, []);

  return { messages, isConnected, streamingContent, sendMessage, clearMessages };
}
