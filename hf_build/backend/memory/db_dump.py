import sqlite3
import json

db_path = r"c:\Users\lenovo\Downloads\AgentForge\backend\memory\agentforge.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT agent, status, timestamp, data FROM task_logs ORDER BY timestamp DESC LIMIT 10")
rows = c.fetchall()

print("LATEST DB EVENTS:")
for r in rows:
    print(f"[{r['timestamp']}] {r['agent']} - {r['status']}")
    print(f"Data: {r['data']}")
    print("-" * 40)
