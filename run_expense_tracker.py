import os
import asyncio
import websockets
import json
import sys

PROMPT = """# Personal Expense Tracker

Build a single-page expense tracking application.

Features:
- Add income and expense transactions.
- Edit and delete transactions.
- Display total income, total expenses, and current balance.
- Categorize transactions.
- Search and filter transactions.
- Store data locally.
- Responsive design for desktop and mobile.
- Clean and modern user interface.
"""

async def run_test():
    port = os.getenv("PORT", os.getenv("BACKEND_PORT", 8001))
    uri = f"ws://127.0.0.1:{port}/ws"
    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            prompt_event = {
                "type": "user_prompt",
                "prompt": PROMPT,
                "session_id": "test_expense_tracker"
            }
            await websocket.send(json.dumps(prompt_event))
            print("Sent expense tracker prompt...")
            
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                
                agent = data.get("agent")
                status = data.get("status")
                
                if status == "streaming":
                    print(data.get("data", {}).get("token", ""), end="", flush=True)
                elif status in ["working", "finished", "server_log", "server_starting"]:
                    msg = data.get('data', {}).get('message', '')
                    log = data.get('data', {}).get('log', '')
                    print(f"\n[{agent.upper()}] {msg} {log}")
                elif status == "error":
                    print(f"\n[ERROR] {data.get('data', {}).get('error', '')}")
                    break
                elif status == "server_ready":
                    print(f"\n[SUCCESS] Server ready at {data.get('data', {}).get('url')}")
                    break
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
