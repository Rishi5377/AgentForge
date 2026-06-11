import os
import sqlite3
from datetime import datetime

db_path = r"c:\Users\lenovo\Downloads\AgentForge\backend\agentforge.db"
workspace_dir = r"c:\Users\lenovo\Downloads\AgentForge\backend\workspace"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ensure table exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT,
        workspace_path TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

folders = [d for d in os.listdir(workspace_dir) if os.path.isdir(os.path.join(workspace_dir, d))]

count = 0
for folder in folders:
    if folder.startswith("app_"):
        project_id = folder.replace("app_", "", 1)
        name = project_id
    elif folder.startswith("workspace_"):
        project_id = folder
        name = folder.replace("workspace_", "").replace("_test", "")
    else:
        continue
    
    path = os.path.join(workspace_dir, folder)
    
    try:
        cursor.execute('''
            INSERT INTO projects (id, name, workspace_path, updated_at) 
            VALUES (?, ?, ?, ?)
        ''', (project_id, name, path, datetime.now().isoformat()))
        count += 1
    except sqlite3.IntegrityError:
        # Already exists
        pass

conn.commit()
conn.close()
print(f"Done syncing! Added {count} existing projects to the database.")
