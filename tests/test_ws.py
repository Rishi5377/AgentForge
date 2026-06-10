import asyncio
import websockets
import json

async def test_generation():
    uri = "ws://localhost:8001/ws"
    async with websockets.connect(uri) as websocket:
        payload = {"type": "user_prompt", "prompt": "Build a stopwatch"}
        await websocket.send(json.dumps(payload))
        print(f"> Sent: {payload}")
        while True:
            response = await websocket.recv()
            print(f"< Received event")
            try:
                data = json.loads(response)
                print(data)
                if data.get("status") == "error":
                    break
                if data.get("agent") == "assembler" and data.get("status") == "finished":
                    break
            except Exception:
                pass

asyncio.run(test_generation())
