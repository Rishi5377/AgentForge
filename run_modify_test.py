import asyncio
import websockets
import json
import sys

PROMPT = """Improve the user experience of the Personal Expense Tracker.

Add the following features:
- Dark mode toggle.
- Toast notifications for actions (e.g. adding or deleting a transaction).
- Confirmation dialogs before deletion.
- Empty states when no transactions exist.
- Loading and error states.
- Smooth animations and transitions (use framer-motion if helpful).
"""

async def run_test():
    uri = "ws://localhost:8002/ws"
    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            prompt_event = {
                "type": "user_prompt",
                "prompt": PROMPT,
                "session_id": "test_expense_tracker"
            }
            await websocket.send(json.dumps(prompt_event))
            print("Sent modification prompt...")
            
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
