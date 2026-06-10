import asyncio
import websockets
import json

PROMPT = """# E-Commerce Store

Build a full-stack e-commerce application.

Pages:
- Home
- Product Listing
- Product Details
- Cart
- Checkout
- Order History
- Admin Dashboard

Features:
- User authentication.
- Product catalog management.
- Shopping cart.
- Inventory management.
- Order tracking.
- Wishlist.
- Customer profiles.

Technical Requirements:
- Database-backed storage.
- Responsive UI.
- Secure checkout flow.
- Clean modern UI with glassmorphism, gradients, micro-animations.
"""

async def run_test():
    uri = "ws://localhost:8001/ws"
    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            prompt_event = {
                "type": "user_prompt",
                "prompt": PROMPT,
                "session_id": "test_ecommerce_hard"
            }
            await websocket.send(json.dumps(prompt_event))
            print("Sent hard ecommerce prompt...")
            
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
