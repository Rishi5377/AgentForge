import sqlite3
import json
import os

db_path = 'c:/Users/lenovo/Downloads/AgentForge/backend/memory/memory.db'

try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Let's check table name first
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print(f"Tables in db: {tables}")
    
    # We assume 'event_logs' based on persistence.py
    if ('event_logs',) in tables:
        cur.execute("SELECT session_id, agent, data, timestamp FROM event_logs WHERE status='error' ORDER BY timestamp DESC LIMIT 50")
        rows = cur.fetchall()
        print(f"Found {len(rows)} error logs")
        
        for r in rows:
            try:
                data = json.loads(r[2])
                error_msg = data.get('error', str(data))
                # Truncate for display if very long
                if len(error_msg) > 500:
                    error_msg = error_msg[:500] + "..."
                print(f"[{r[3]}] Session: {r[0]} | Agent: {r[1]} | Error: {error_msg}")
            except Exception as e:
                print(f"Error parsing data: {r[2]} - {e}")
except Exception as e:
    print(f"Database error: {e}")
