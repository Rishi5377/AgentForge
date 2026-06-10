import asyncio
import websockets
import json
import os

PROMPT = """# Social Media Platform

Build a full-stack social media application.

Pages:
- Home Feed
- Login/Register
- User Profile
- Post Details
- Notifications
- Settings

Features:
- User authentication.
- Create, edit, and delete posts.
- Upload images.
- Like and comment on posts.
- Follow and unfollow users.
- User profiles.
- Search users and posts.
- Notification system.

Technical Requirements:
- Database persistence.
- Responsive design.
- Role-based access control.
"""

async def run_test():
    uri = "ws://localhost:8001/ws"
    try:
        async with websockets.connect(uri) as websocket:
            prompt_event = {
                "type": "user_prompt",
                "prompt": PROMPT,
                "session_id": "test_social_media_limits"
            }
            await websocket.send(json.dumps(prompt_event))
            print("Sent extreme prompt...")
            
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                
                agent = data.get("agent")
                status = data.get("status")
                
                if status == "streaming":
                    print(data.get("data", {}).get("token", ""), end="", flush=True)
                elif status in ["working", "finished", "server_log", "server_starting"]:
                    print(f"\n[{agent.upper()}] {data.get('data', {}).get('message', '')} {data.get('data', {}).get('log', '')}")
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
