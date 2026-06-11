import aiosqlite
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'agentforge.db')

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                agent TEXT,
                status TEXT,
                data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT,
                workspace_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        ''')
        await db.commit()

async def log_event(session_id: str, agent: str, status: str, data: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO task_logs (session_id, agent, status, data) VALUES (?, ?, ?, ?)',
            (session_id, agent, status, json.dumps(data))
        )
        await db.commit()

async def create_or_update_project(project_id: str, name: str, workspace_path: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO projects (id, name, workspace_path, updated_at) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET name = excluded.name, updated_at = CURRENT_TIMESTAMP
        ''', (project_id, name, workspace_path))
        await db.commit()

async def get_projects():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM projects ORDER BY updated_at DESC') as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def delete_project(project_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        await db.commit()

async def add_chat_message(project_id: str, role: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO chat_messages (project_id, role, content) VALUES (?, ?, ?)',
            (project_id, role, content)
        )
        await db.commit()

async def get_chat_history(project_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT role, content FROM chat_messages WHERE project_id = ? ORDER BY timestamp ASC', (project_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
