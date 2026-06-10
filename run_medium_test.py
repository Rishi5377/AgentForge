import asyncio
import websockets
import json

PROMPT = """# Inventory Management System

Build a single-page inventory tracker.

Features:
- Add, edit, and remove products.
- Track stock quantities.
- Low-stock alerts.
- Product categories.
- Search and filtering.
- Inventory statistics dashboard.

Technical Requirements:
- Responsive design.
- Clean modern UI with glassmorphism, gradients, micro-animations.
- Component-based architecture.
- Data persistence using Local Storage.
"""

async def run_test():
    uri = "ws://localhost:8001/ws"
    try:
        async with websockets.connect(uri) as websocket:
            prompt_event = {
                "type": "user_prompt",
                "prompt": PROMPT,
                "session_id": "test_inventory_medium"
            }
            await websocket.send(json.dumps(prompt_event))
            print("Sent medium inventory prompt...")
            
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
