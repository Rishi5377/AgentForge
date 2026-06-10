import sqlite3
import json
import os

db_path = 'c:/Users/lenovo/Downloads/AgentForge/backend/memory/agentforge.db'

try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT session_id, agent, data, timestamp FROM task_logs WHERE status='error' ORDER BY timestamp DESC LIMIT 50")
    rows = cur.fetchall()
    
    print(f"Found {len(rows)} error logs in agentforge.db\n")
    
    for r in rows:
        try:
            data = json.loads(r[2])
            error_msg = data.get('error', str(data))
            if len(error_msg) > 1000:
                error_msg = error_msg[:1000] + "...\n[TRUNCATED]"
            print(f"[{r[3]}] Session: {r[0]} | Agent: {r[1]}\nError:\n{error_msg}\n{'-'*60}")
        except Exception as e:
            print(f"Error parsing data: {r[2]} - {e}")
except Exception as e:
    print(f"Database error: {e}")
