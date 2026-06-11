import os
import re

path = r'C:\Users\lenovo\Downloads\AgentForge\backend\main.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update broadcast_event calls
text = text.replace('await broadcast_event(install_event)', 'await broadcast_event(install_event, session_id)')
text = text.replace('await broadcast_event(build_event)', 'await broadcast_event(build_event, session_id)')
text = text.replace('await broadcast_event(err_event)', 'await broadcast_event(err_event, session_id)')
text = text.replace('await broadcast_event(start_msg_event)', 'await broadcast_event(start_msg_event, session_id)')
text = text.replace('await broadcast_event(event)', 'await broadcast_event(event, session_id)')
text = text.replace('await broadcast_event(start_event)', 'await broadcast_event(start_event, session_id)')
text = text.replace('await broadcast_event(next_event)', 'await broadcast_event(next_event, session_id)')
text = text.replace('await broadcast_event(ready_event)', 'await broadcast_event(ready_event, session_id)')

# 2. Pass session_id to stream_subprocess_output
text = text.replace(
    'asyncio.create_task(stream_subprocess_output(install_process.stdout, "system", "server_log"))',
    'asyncio.create_task(stream_subprocess_output(install_process.stdout, "system", "server_log", session_id))'
)
text = text.replace(
    'asyncio.create_task(stream_subprocess_output(install_process.stderr, "system", "server_error"))',
    'asyncio.create_task(stream_subprocess_output(install_process.stderr, "system", "server_error", session_id))'
)
text = text.replace(
    'asyncio.create_task(stream_subprocess_output(process.stderr, "system", "server_error"))',
    'asyncio.create_task(stream_subprocess_output(process.stderr, "system", "server_error", session_id))'
)

# 3. Update websocket connection logic
ws_old = '''@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            if payload.get("type") == "user_prompt":
                prompt = payload.get("prompt")
                session_id = payload.get("session_id")
                if not session_id:
                    session_id = str(uuid.uuid4())'''

ws_new = '''@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # active_connections tracks mapping from websocket to session_id
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            session_id = payload.get("session_id")
            if not session_id:
                session_id = str(uuid.uuid4())
            active_connections[websocket] = session_id
            
            if payload.get("type") == "user_prompt":
                prompt = payload.get("prompt")'''

text = text.replace(ws_old, ws_new)

# 4. Update websocket disconnect
dc_old = '''    except WebSocketDisconnect:
        active_connections.remove(websocket)'''
dc_new = '''    except WebSocketDisconnect:
        sess_id = active_connections.get(websocket)
        if sess_id:
            # Kill processes tied to session
            if sess_id in active_processes:
                try:
                    import psutil
                    parent = psutil.Process(active_processes[sess_id].pid)
                    for child in parent.children(recursive=True):
                        child.kill()
                    parent.kill()
                except:
                    pass
                del active_processes[sess_id]
        if websocket in active_connections:
            del active_connections[websocket]'''
text = text.replace(dc_old, dc_new)

# 5. Fix current_dev_process -> active_processes inside start_dev_server
sdv_old = '''async def start_dev_server(session_id: str, workspace_dir: str):
    global current_dev_process
    if current_dev_process:
        try:
            import psutil
            parent = psutil.Process(current_dev_process.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except:
            pass
        current_dev_process = None'''

sdv_new = '''import socket

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

async def start_dev_server(session_id: str, workspace_dir: str):
    global active_processes
    if session_id in active_processes:
        try:
            import psutil
            parent = psutil.Process(active_processes[session_id].pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except:
            pass
        del active_processes[session_id]'''
text = text.replace(sdv_old, sdv_new)

# 6. Update process spawn to pass dynamic port
spwn_old = '''    process = await asyncio.create_subprocess_exec(
        npm_path, "run", "dev",
        cwd=workspace_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    current_dev_process = process
    
    port_queue = asyncio.Queue()'''

spwn_new = '''    port_val = get_free_port()
    process = await asyncio.create_subprocess_exec(
        npm_path, "run", "dev", "--", "--port", str(port_val),
        cwd=workspace_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    active_processes[session_id] = process
    
    port_queue = asyncio.Queue()'''
text = text.replace(spwn_old, spwn_new)

# 7. Also allow the port regex to pick up the requested port as a fallback
prt_old = '''                if "Local:" in clean_text and "http://localhost:" in clean_text:
                    match = re.search(r'http://localhost:(\d+)', clean_text)
                    if match:
                        await port_queue.put(match.group(1))'''

prt_new = '''                if "Local:" in clean_text and "http://localhost:" in clean_text:
                    match = re.search(r'http://localhost:(\d+)', clean_text)
                    if match:
                        await port_queue.put(match.group(1))
                elif "http://localhost:" in clean_text:
                    await port_queue.put(str(port_val))'''
text = text.replace(prt_old, prt_new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("main.py rewritten successfully!")
