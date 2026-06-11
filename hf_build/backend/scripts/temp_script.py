import sqlite3
import json

conn = sqlite3.connect('memory/agentforge.db')
c = conn.cursor()
c.execute("SELECT data FROM task_logs WHERE session_id='75dd7689-b972-4abb-b561-5c3d4554fd6e' AND status='server_log' ORDER BY id ASC;")
for row in c.fetchall():
    print(row[0])
