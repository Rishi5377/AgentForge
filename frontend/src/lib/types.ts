export interface AgentEvent {
  type: string;
  agent: string;
  status: 'started' | 'working' | 'completed' | 'finished' | 'skipped' | 'error' | 'server_ready' | 'server_log' | 'server_error' | 'streaming' | 'server_starting' | 'chat_message';
  data: any;
  timestamp: string;
}

export interface WebSocketMessage {
  type: string;
  payload: any;
}
