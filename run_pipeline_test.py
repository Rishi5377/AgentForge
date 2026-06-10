import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure backend modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

# Load env variables
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', '.env')))

from workflows.pipeline import create_pipeline, GraphState

async def test_app(prompt: str, session_id: str):
    pipeline = create_pipeline()
    state = GraphState({
        "user_prompt": prompt,
        "session_id": session_id,
        "workspace_dir": os.path.abspath(f"workspace_{session_id}"),
        "messages": [],
        "plan": {},
        "execution_order": [],
        "current_step_idx": 0,
        "validation_errors": {},
        "retry_counts": {},
        "next_worker": "",
        "last_active_agent": "",
        "qa_retry_count": 0
    })
    
    print(f"\n==== Starting test: {session_id} ====")
    print(f"Prompt: {prompt}")
    
    try:
        async for event in pipeline.astream(state):
            for k, v in event.items():
                print(f"-> Node {k} finished.")
                if "validation_errors" in v and v["validation_errors"].get("qa"):
                    print(f"QA Error: {v['validation_errors']['qa']}")
    except Exception as e:
        print(f"Pipeline error: {e}")
        
    print(f"==== Finished test: {session_id} ====\n")

async def main():
    print("Testing Expense Tracker...")
    prompt1 = """Build a personal expense tracker web application.
Requirements: User signup and login, Dashboard showing Total income, Total expenses, Current balance. Add income/expense transactions. Categories: Food, Transport, Entertainment, Bills, Other. Monthly expense chart, Transaction history table, Search and filter transactions, Edit and delete transactions. Mobile responsive design, Dark mode support.
Technical Requirements: React frontend, Node.js + Express backend, SQLite database, REST APIs.
Generate: Database schema, API endpoints, Frontend pages, Complete source code."""
    await test_app(prompt1, "expense_tracker_test")
    
    print("Testing To-Do Teams...")
    prompt2 = """Build a task management application.
Features: User registration/login, Create teams, Invite members, Create tasks, Assign tasks to members, Task status (To Do, In Progress, Done), Due dates, Comments on tasks, Filter tasks by user/status, Team dashboard.
Technical Requirements: React, Node.js + Express, SQLite.
Generate: Database schema, API endpoints, Frontend pages, Complete source code."""
    await test_app(prompt2, "todo_teams_test")

if __name__ == "__main__":
    asyncio.run(main())
