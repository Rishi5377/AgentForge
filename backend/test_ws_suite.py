import asyncio
import websockets
import json
import uuid

# Test cases
TESTS = [
    {
        "id": "test1_expense_tracker",
        "prompt": """Easy Test #1: Personal Expense Tracker

Build a personal expense tracker web application.

Requirements:

User signup and login
Dashboard showing:
Total income
Total expenses
Current balance
Add income transactions
Add expense transactions
Categories:
Food
Transport
Entertainment
Bills
Other
Monthly expense chart
Transaction history table
Search and filter transactions
Edit and delete transactions
Mobile responsive design
Dark mode support

Technical Requirements:

React frontend
Node.js + Express backend
PostgreSQL database
JWT authentication
REST APIs

Generate:

Database schema
API endpoints
Frontend pages
Folder structure
Complete source code
Setup instructions"""
    },
    {
        "id": "test2_todo_teams",
        "prompt": """Easy Test #2: To-Do App With Teams

Build a task management application.

Features:

User registration/login
Create teams
Invite members
Create tasks
Assign tasks to members
Task status (To Do, In Progress, Done)
Due dates
Comments on tasks
Filter tasks by user/status
Team dashboard

Technical Requirements:

React
Node.js + Express
PostgreSQL

Generate:

Database schema
API endpoints
Frontend pages
Complete source code"""
    },
    {
        "id": "test3_library_mgmt",
        "prompt": """Easy Test #3: Library Management System

Build a book tracking application.

Features:

Authentication (Admin and User roles)
Admin can:
Add books (Title, Author, ISBN, Quantity)
Edit/Delete books
View all users
User can:
Search books
Borrow books
Return books
View personal borrowing history
Dashboard showing available books

Technical Requirements:

React
Node.js + Express
PostgreSQL

Generate:

Database schema
API endpoints
Frontend pages
Complete source code"""
    }
]

async def run_test(test):
    uri = "ws://localhost:8001/ws"
    session_id = test["id"] + "_" + str(uuid.uuid4())[:6]
    
    print(f"Starting test: {test['id']} (Session: {session_id})")
    
    try:
        async with websockets.connect(uri) as websocket:
            payload = {
                "type": "user_prompt",
                "prompt": test["prompt"],
                "session_id": session_id
            }
            await websocket.send(json.dumps(payload))
            
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                agent = data.get("agent")
                status = data.get("status")
                log = data.get("data", {}).get("log", "")
                error = data.get("data", {}).get("error", "")
                
                if log:
                    print(f"[{agent}] {log}")
                elif error:
                    print(f"[{agent}] ERROR: {error}")
                else:
                    msg = data.get("data", {}).get("message", "")
                    if msg:
                        print(f"[{agent}] {msg}")
                
                if status == "server_ready":
                    url = data.get("data", {}).get("url")
                    print(f"\n✅ SUCCESS! Server is ready at: {url}")
                    break
                
                if status == "error" and agent == "system" and "Dev server timed out" in str(data):
                    print(f"\n❌ FAILED! {data}")
                    break
                    
                if status == "error" and agent == "system" and "Max retries exceeded" in str(data):
                     print(f"\n❌ FAILED AUTO RECOVERY MAX EXCEEDED!")
                     break
                     
    except Exception as e:
        print(f"Connection error: {e}")

async def main():
    for test in TESTS:
        await run_test(test)

if __name__ == "__main__":
    asyncio.run(main())
