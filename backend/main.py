from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import uuid
import datetime
import os
import subprocess
import re
import shutil
from fastapi import Request, Response
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse, HTMLResponse
import httpx
import websockets

httpx_client = httpx.AsyncClient()


from utils.project_indexer import generate_project_structure

from schemas.events import AgentEvent, UserPrompt
from memory.persistence import init_db, log_event, create_or_update_project, get_projects, delete_project, add_chat_message, get_chat_history
from pydantic import BaseModel
from typing import Dict, Any, List

IS_DEMO_MODE = os.getenv("NEXT_PUBLIC_IS_DEMO", "false").lower() == "true" or os.getenv("IS_DEMO", "false").lower() == "true"

async def cleanup_worker():
    while True:
        try:
            await asyncio.sleep(3600) # Check every hour
            workspace_dir = os.path.join(os.path.dirname(__file__), "workspace")
            if not os.path.exists(workspace_dir):
                continue
                
            is_demo = os.getenv("IS_DEMO", "false").lower() == "true"
            now = datetime.datetime.now().timestamp()
            
            for proj_folder in os.listdir(workspace_dir):
                proj_path = os.path.join(workspace_dir, proj_folder)
                if not os.path.isdir(proj_path):
                    continue
                
                mtime = os.path.getmtime(proj_path)
                age_hours = (now - mtime) / 3600.0
                
                threshold = float(os.getenv("CLEANUP_HOURS", 1.0 if is_demo else 24.0))
                
                if age_hours > threshold:
                    if is_demo:
                        print(f"Demo Mode Cleanup: Wiping entire old project {proj_folder} to save space.")
                        shutil.rmtree(proj_path, ignore_errors=True)
                    else:
                        node_modules = os.path.join(proj_path, "node_modules")
                        next_cache = os.path.join(proj_path, ".next")
                        
                        if os.path.exists(node_modules):
                            shutil.rmtree(node_modules, ignore_errors=True)
                        if os.path.exists(next_cache):
                            shutil.rmtree(next_cache, ignore_errors=True)
        except Exception as e:
            print(f"Cleanup worker error: {e}")
            await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(cleanup_worker())
    mem_task = asyncio.create_task(memory_cleanup_worker())
    yield
    task.cancel()
    mem_task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections: Dict[WebSocket, str] = {}
active_processes: Dict[str, Any] = {}
active_ports: Dict[str, str] = {}
last_active_timestamps: Dict[str, float] = {}

async def memory_cleanup_worker():
    import time
    while True:
        try:
            await asyncio.sleep(60)
            now = time.time()
            to_kill = []
            for sess_id, proc in list(active_processes.items()):
                last_active = last_active_timestamps.get(sess_id, now)
                if now - last_active > 600: # 10 minutes
                    to_kill.append(sess_id)
            
            for sess_id in to_kill:
                print(f"[Memory Cleanup] Terminating idle server for {sess_id}...")
                try:
                    proc = active_processes[sess_id]
                    proc.terminate()
                except Exception:
                    pass
                if sess_id in active_processes:
                    del active_processes[sess_id]
                if sess_id in active_ports:
                    del active_ports[sess_id]
                if sess_id in last_active_timestamps:
                    del last_active_timestamps[sess_id]
        except Exception as e:
            print(f"Memory cleanup worker error: {e}")

class SettingsSchema(BaseModel):
    models: Dict[str, str] = {}
    api_keys: Dict[str, str] = {}
    general: Dict[str, Any] = {}

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "memory", "settings.json")

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"models": {}, "api_keys": {}, "general": {}}

def save_settings(settings: dict):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

@app.get("/api/settings")
async def get_settings():
    settings = load_settings()
    
    # Inject environment API keys so the frontend knows keys are configured (especially for Web/Demo version)
    env_keys = {
        "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
        "gemini": os.getenv("GEMINI_API_KEY", ""),
        "openai": os.getenv("OPENAI_API_KEY", ""),
        "groq": os.getenv("GROQ_API_KEY", "")
    }
    
    if "api_keys" not in settings:
        settings["api_keys"] = {}
        
    for k, v in env_keys.items():
        if v and not settings["api_keys"].get(k):
            settings["api_keys"][k] = "Set via Environment Variable"
            
    return settings

@app.post("/api/settings")
async def update_settings(settings: SettingsSchema):
    save_settings(settings.model_dump())
    return {"status": "success"}

@app.get("/api/models")
async def get_models():
    return {
        "gemini": [
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-pro"
        ],
        "groq": [
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768"
        ],
        "openai": [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ]
    }

class RenameProjectSchema(BaseModel):
    name: str

@app.get("/api/projects")
async def api_get_projects():
    return await get_projects()

@app.get("/api/projects/{project_id}")
async def api_get_project(project_id: str):
    history = await get_chat_history(project_id)
    
    # Filter out duplicate "I've finished building..." messages so only the latest one shows
    filtered_history = []
    seen_finished = False
    for msg in reversed(history):
        if msg["content"] and "I've finished building your app" in msg["content"]:
            if not seen_finished:
                filtered_history.append(msg)
                seen_finished = True
        else:
            filtered_history.append(msg)
    filtered_history.reverse()
    
    return {"id": project_id, "chat_history": filtered_history}

@app.delete("/api/projects/{project_id}")
async def api_delete_project(project_id: str):
    await delete_project(project_id)
    return {"status": "success"}

@app.post("/api/projects/{project_id}/rename")
async def api_rename_project(project_id: str, data: RenameProjectSchema):
    # Retrieve current workspace path, updating name
    projects = await get_projects()
    proj = next((p for p in projects if p["id"] == project_id), None)
    if proj:
        await create_or_update_project(project_id, data.name, proj["workspace_path"])
    return {"status": "success"}

class WriteFileSchema(BaseModel):
    path: str
    content: str

class GithubSyncSchema(BaseModel):
    repo_name: str
    description: str = ""
    visibility: str = "private"

@app.api_route("/preview/{session_id}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
@app.api_route("/preview/{session_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_preview(session_id: str, request: Request, path: str = ""):
    import time
    last_active_timestamps[session_id] = time.time()
    
    port = active_ports.get(session_id)
    if not port:
        return Response(content="Server not running", status_code=502)
    
    raw_path = request.url.path
    proxy_host = "127.0.0.1"
    url = f"http://{proxy_host}:{port}{raw_path}"
    
    query_string = request.url.query
    if query_string:
        url += f"?{query_string}"
        
    headers = dict(request.headers)
    headers.pop("host", None)
    
    try:
        req = httpx_client.build_request(
            request.method,
            url,
            headers=headers,
            content=await request.body()
        )
        response = await httpx_client.send(req, stream=True)
        resp = StreamingResponse(
            response.aiter_raw(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        samesite_val = "none" if IS_DEMO_MODE else "lax"
        secure_val = True if IS_DEMO_MODE else False
        resp.set_cookie(key="preview_session", value=session_id, path="/", samesite=samesite_val, secure=secure_val)
        return resp
    except Exception as e:
        if "127.0.0.1" in url:
            try:
                url_ipv6 = url.replace("127.0.0.1", "[::1]")
                req = httpx_client.build_request(request.method, url_ipv6, headers=headers, content=await request.body())
                response = await httpx_client.send(req, stream=True)
                resp = StreamingResponse(response.aiter_raw(), status_code=response.status_code, headers=dict(response.headers))
                resp.set_cookie(key="preview_session", value=session_id, path="/", samesite="none", secure=True)
                return resp
            except Exception as e2:
                return {"error": f"Proxy error: {str(e2)}"}
        return {"error": f"Proxy error: {str(e)}"}

@app.get("/api/projects/{project_id}/files")
async def api_get_project_files(project_id: str):
    workspace_dir = os.path.join(os.path.dirname(__file__), "workspace", f"app_{project_id}")
    if not os.path.exists(workspace_dir):
        return {"files": []}
    
    file_tree = []
    for root, dirs, files in os.walk(workspace_dir):
        # Skip hidden/build dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ["node_modules", "dist", "public", "build"]]
        for file in files:
            if file.startswith('.') or file in ["package-lock.json", "pnpm-lock.yaml"]: continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, workspace_dir)
            # Use forward slashes for paths in the API response
            rel_path = rel_path.replace("\\", "/")
            file_tree.append(rel_path)
            
    return {"files": sorted(file_tree)}

@app.get("/api/projects/{project_id}/files/read")
async def api_read_project_file(project_id: str, path: str):
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "workspace", f"app_{project_id}"))
    file_path = os.path.abspath(os.path.join(workspace_dir, path))
    if not file_path.startswith(workspace_dir):
        return {"error": "Access denied: Path traversal detected."}
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/projects/{project_id}/sandpack")
async def api_sandpack_files(project_id: str):
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "workspace", f"app_{project_id}"))
    if not os.path.exists(workspace_dir):
        return {"files": {}}
    
    sandpack_files = {}
    for root, dirs, files in os.walk(workspace_dir):
        # Skip hidden/build dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ["node_modules", "dist", "public", "build"]]
        for file in files:
            if file.startswith('.') or file in ["package-lock.json", "pnpm-lock.yaml"]: continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, workspace_dir)
            rel_path = rel_path.replace("\\", "/")
            
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    sandpack_files[f"/{rel_path}"] = f.read()
            except Exception:
                pass # skip binary/unreadable files
                
    return {"files": sandpack_files}

@app.post("/api/projects/{project_id}/files/write")
async def api_write_project_file(project_id: str, data: WriteFileSchema):
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "workspace", f"app_{project_id}"))
    file_path = os.path.abspath(os.path.join(workspace_dir, data.path))
    if not file_path.startswith(workspace_dir):
        return {"error": "Access denied: Path traversal detected."}
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data.content)
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/projects/{project_id}/download")
async def api_download_project(project_id: str):
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "workspace", f"app_{project_id}"))
    if not os.path.exists(workspace_dir):
        return {"error": "Project not found"}
    
    zip_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "workspace", f"app_{project_id}.zip"))
    
    try:
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', workspace_dir)
        return FileResponse(path=zip_path, filename=f"project_{project_id}.zip", media_type='application/zip')
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/projects/{project_id}/github")
async def api_github_sync(project_id: str, data: GithubSyncSchema):
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "workspace", f"app_{project_id}"))
    if not os.path.exists(workspace_dir):
        return {"error": "Project not found"}
    
    import subprocess
    import asyncio
    try:
        # Initialize git if not already initialized
        if not os.path.exists(os.path.join(workspace_dir, ".git")):
            await asyncio.to_thread(subprocess.run, ["git", "init"], cwd=workspace_dir, check=True, capture_output=True)
            await asyncio.to_thread(subprocess.run, ["git", "add", "."], cwd=workspace_dir, check=True, capture_output=True)
            await asyncio.to_thread(subprocess.run, ["git", "commit", "-m", "Initial commit from AgentForge"], cwd=workspace_dir, check=True, capture_output=True)
            await asyncio.to_thread(subprocess.run, ["git", "branch", "-M", "main"], cwd=workspace_dir, check=True, capture_output=True)
        
        # Check if gh CLI is installed
        try:
            await asyncio.to_thread(subprocess.run, ["gh", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {"error": "GitHub CLI (gh) is not installed or not in PATH. Please install it to use this feature."}

        # Check if already authenticated with gh
        auth_status = await asyncio.to_thread(subprocess.run, ["gh", "auth", "status"], capture_output=True)
        if auth_status.returncode != 0:
            return {"error": "Not authenticated with GitHub CLI. Please run 'gh auth login' in your terminal."}

        # Create the repository using gh CLI
        cmd = [
            "gh", "repo", "create", data.repo_name,
            f"--{data.visibility}",
            "--source=.",
            "--remote=origin",
            "--push"
        ]
        
        if data.description:
            cmd.extend(["--description", data.description])

        result = await asyncio.to_thread(subprocess.run, cmd, cwd=workspace_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            # If it fails, maybe it already exists and we just need to push
            if "graphql error: Name already exists on this account" in result.stderr or "already exists" in result.stderr:
                return {"error": f"Repository '{data.repo_name}' already exists on your GitHub account."}
            return {"error": f"Failed to create repository: {result.stderr.strip()}"}

        return {"status": "success", "message": "Successfully synced to GitHub!"}
        
    except subprocess.CalledProcessError as e:
        return {"error": f"Git command failed: {e.stderr.decode('utf-8') if e.stderr else str(e)}"}
    except Exception as e:
        return {"error": str(e)}

async def broadcast_event(event: AgentEvent, target_session_id: str = None):
    for connection, sess_id in list(active_connections.items()):
        if target_session_id is None or sess_id == target_session_id:
            try:
                print(f"Broadcasting event: {event.agent} - {event.status} to {sess_id}")
                await connection.send_text(event.model_dump_json())
            except Exception as e:
                print(f"Failed to send to connection: {e}")

async def stream_subprocess_output(stream, agent_name: str, status_type: str, session_id: str = None):
    while True:
        line = await stream.readline()
        if not line:
            break
        text = line.decode('utf-8', errors='ignore').strip()
        if text:
            event = AgentEvent(
                agent=agent_name,
                status=status_type,
                data={"log": text},
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )
            await broadcast_event(event, session_id)

import socket

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

async def stop_dev_server(session_id: str):
    global active_processes, active_ports
    if session_id in active_processes:
        try:
            proc = active_processes[session_id]
            import platform
            if platform.system() == "Windows":
                subprocess.run(f"taskkill /F /T /PID {proc.pid}", shell=True, capture_output=True)
            else:
                proc.terminate()
                proc.kill()
        except:
            pass
        del active_processes[session_id]
        
    if session_id in active_ports:
        del active_ports[session_id]

async def stop_all_dev_servers():
    global active_processes, active_ports
    for sid in list(active_processes.keys()):
        await stop_dev_server(sid)
        
    # Aggressive memory cleanup for Free Tier constraints
    try:
        import platform
        if platform.system() == "Windows":
            subprocess.run("taskkill /F /IM node.exe", shell=True, capture_output=True)
        else:
            subprocess.run("pkill -f node", shell=True, capture_output=True)
            subprocess.run("pkill -f next-server", shell=True, capture_output=True)
    except Exception as e:
        print(f"Aggressive node cleanup failed: {e}")

async def start_dev_server(session_id: str, workspace_dir: str):
    global active_processes, active_ports
    is_already_running = False
    if session_id in active_processes:
        try:
            proc = active_processes[session_id]
            if proc.poll() is None:
                is_already_running = True
        except:
            pass
            
        if not is_already_running:
            await stop_dev_server(session_id)

    import shutil
    npm_path = shutil.which("pnpm") or ("pnpm.cmd" if os.name == "nt" else "pnpm")
    vite_cache = os.path.join(workspace_dir, "node_modules", ".vite")
    if os.path.exists(vite_cache):
        try:
            shutil.rmtree(vite_cache)
        except:
            pass
            
    # Ensure all required TypeScript types are added if their corresponding packages are in dependencies
    pkg_path = os.path.join(workspace_dir, "package.json")
    pkg_changed = False
    pkg_data = {}
    
    if os.path.exists(pkg_path):
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
            
            deps = pkg_data.get("dependencies", {})
            dev_deps = pkg_data.get("devDependencies", {})
            
            type_mapping = {
                "better-sqlite3": "@types/better-sqlite3",
                "bcryptjs": "@types/bcryptjs",
                "jsonwebtoken": "@types/jsonwebtoken",
                "bcrypt": "@types/bcrypt",
                "pg": "@types/pg",
                "uuid": "@types/uuid",
                "sqlite3": "@types/sqlite3",
                "cors": "@types/cors",
                "express": "@types/express",
            }
            
            for dep_name, type_name in type_mapping.items():
                if dep_name in deps and type_name not in dev_deps and type_name not in deps:
                    dev_deps[type_name] = "latest"
                    pkg_changed = True
            
            if "scripts" in pkg_data and "dev" in pkg_data["scripts"]:
                dev_script = pkg_data["scripts"]["dev"]
                if "node " in dev_script and "node --watch" not in dev_script and "nodemon" not in dev_script:
                    pkg_data["scripts"]["dev"] = dev_script.replace("node ", "node --watch ")
                    pkg_changed = True

            if pkg_changed:
                pkg_data["devDependencies"] = dev_deps
                with open(pkg_path, "w", encoding="utf-8") as f:
                    json.dump(pkg_data, f, indent=2)
                print("Updated package.json devDependencies to include missing TypeScript types.")
        except Exception as e:
            print(f"Failed to check/update package.json types: {e}")

    # Check if package.json has changed since the last successful install
    installed_pkg_path = os.path.join(workspace_dir, ".package-installed.json")
    need_install = not os.path.exists(os.path.join(workspace_dir, "node_modules"))
    
    if not need_install and os.path.exists(pkg_path):
        if os.path.exists(installed_pkg_path):
            try:
                with open(installed_pkg_path, "r", encoding="utf-8") as f:
                    installed_pkg_data = json.load(f)
                
                current_deps = pkg_data.get("dependencies", {})
                current_dev_deps = pkg_data.get("devDependencies", {})
                installed_deps = installed_pkg_data.get("dependencies", {})
                installed_dev_deps = installed_pkg_data.get("devDependencies", {})
                
                if current_deps != installed_deps or current_dev_deps != installed_dev_deps:
                    need_install = True
                    print("package.json dependencies changed. Triggering pnpm install.")
            except Exception:
                need_install = True
        else:
            need_install = True

    # Phase 1: Install dependencies
    if not need_install:
        install_event = AgentEvent(
            agent="system",
            status="server_log",
            data={"log": "> Dependencies unchanged. Skipping pnpm install to save time..."},
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        await broadcast_event(install_event, session_id)
    else:
        install_event = AgentEvent(
            agent="system",
            status="server_log",
            data={"log": "> Running pnpm install..."},
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        await broadcast_event(install_event, session_id)
        
        nice_cmd = ["nice", "-n", "19"] if os.name != "nt" else []
        
        has_pnpm_lock = os.path.exists(os.path.join(workspace_dir, "pnpm-lock.yaml"))
        pnpm_path = shutil.which("pnpm")
        
        if has_pnpm_lock and pnpm_path:
            cmd_args = nice_cmd + [pnpm_path, "install", "--no-frozen-lockfile", "--reporter=append-only"]
        else:
            cmd_args = nice_cmd + [npm_path, "install", "--no-audit", "--no-fund", "--legacy-peer-deps"]
            
        install_process = await asyncio.create_subprocess_exec(
            *cmd_args,
            cwd=workspace_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        asyncio.create_task(stream_subprocess_output(install_process.stdout, "system", "server_log", session_id))
        asyncio.create_task(stream_subprocess_output(install_process.stderr, "system", "server_log", session_id))
        
        install_code = await install_process.wait()
        if install_code != 0:
            print(f"Primary install failed with exit code {install_code}. Falling back to npm install...")
            fallback_args = nice_cmd + [npm_path, "install", "--no-audit", "--no-fund", "--legacy-peer-deps"]
            fallback_process = await asyncio.create_subprocess_exec(
                *fallback_args,
                cwd=workspace_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            asyncio.create_task(stream_subprocess_output(fallback_process.stdout, "system", "server_log", session_id))
            asyncio.create_task(stream_subprocess_output(fallback_process.stderr, "system", "server_log", session_id))
            install_code = await fallback_process.wait()
            
        if install_code != 0:
            err_event = AgentEvent(
                agent="system",
                status="error",
                data={"error": f"Dependencies install failed with exit code {install_code}. Please check the server logs."},
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )
            await broadcast_event(err_event, session_id)
            await log_event(session_id, "system", "error", err_event.data)
            return {"source": "system", "error": "Dependency installation failed."}
            
        # Write the installed package.json marker
        if os.path.exists(pkg_path):
            try:
                shutil.copy2(pkg_path, installed_pkg_path)
            except Exception:
                pass
        
    if is_already_running:
        port = active_ports.get(session_id)
        if port:
            ready_event = AgentEvent(
                agent="system",
                status="server_ready",
                data={"url": f"/preview/{session_id}/"},
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )
            await broadcast_event(ready_event, session_id)
            await log_event(session_id, "system", "server_ready", ready_event.data)
        return None

    recovery_error = None
    import time
    last_active_timestamps[session_id] = time.time()
    
    # Phase 2: Start server
    start_msg_event = AgentEvent(
        agent="system",
        status="server_log",
        data={"log": "> Starting development server..."},
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    await broadcast_event(start_msg_event, session_id)
    
    port_val = get_free_port()
    
    # Ensure next.config.mjs supports basePath for Next.js projects
    if os.path.exists(os.path.join(workspace_dir, "package.json")):
        try:
            config_path_mjs = os.path.join(workspace_dir, "next.config.mjs")
            config_path_js = os.path.join(workspace_dir, "next.config.js")
            config_content = """/** @type {import('next').NextConfig} */
const nextConfig = {
    basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',
};
export default nextConfig;
"""
            js_content = """/** @type {import('next').NextConfig} */
const nextConfig = {
    basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',
};
module.exports = nextConfig;
"""
            if os.path.exists(config_path_mjs):
                with open(config_path_mjs, "w") as f:
                    f.write(config_content)
            elif os.path.exists(config_path_js):
                with open(config_path_js, "w") as f:
                    f.write(js_content)
            else:
                # Default to .mjs if neither exists
                with open(config_path_mjs, "w") as f:
                    f.write(config_content)
        except Exception as e:
            print(f"[Warning] Failed to update next.config: {e}")
            
    # Dynamically determine the start script
    start_script = "dev"
    if pkg_data.get("scripts"):
        if "dev" not in pkg_data["scripts"] and "start" in pkg_data["scripts"]:
            start_script = "start"

    # Set up environment variables to force unbuffered output and skip telemetry
    env = os.environ.copy()
    env["CI"] = "true"
    env["FORCE_COLOR"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    env["PORT"] = str(port_val)
    env["NEXT_TELEMETRY_DISABLED"] = "1"
    env["NEXT_PUBLIC_BASE_PATH"] = f"/preview/{session_id}"

    process = await asyncio.create_subprocess_exec(
        npm_path, "run", start_script,
        cwd=workspace_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    active_processes[session_id] = process
    
    port_queue = asyncio.Queue()
    from collections import deque
    server_logs = deque(maxlen=30)
    
    async def stream_and_parse(stream, agent_name: str, status_type: str):
        import re
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode('utf-8', errors='ignore').strip()
            if text:
                server_logs.append(text)
                event = AgentEvent(
                    agent=agent_name,
                    status=status_type,
                    data={"log": text},
                    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
                )
                await broadcast_event(event, session_id)
                # Skip log_event here to avoid spamming the database, we'll log errors on timeout
                
                clean_text = re.sub(r'\x1b\[[0-9;]*m', '', text)
                clean_text = clean_text.replace('\u001b', '')
                
                # Check for any line that looks like it has the URL
                match = re.search(r'http://(?:localhost|127\.0\.0\.1|0\.0\.0\.0):(\d+)', clean_text)
                if match:
                    port_str = match.group(1)
                    if port_str.startswith('517') or port_str.startswith('3000') or 'Local:' in clean_text or 'Vite' in clean_text:
                        active_ports[session_id] = port_str
                        await port_queue.put(port_str)
                    elif session_id not in active_ports or active_ports[session_id] == str(port_val):
                        active_ports[session_id] = port_str
                        await port_queue.put(port_str)
                elif "ready on port" in clean_text.lower() or "server running on port" in clean_text.lower() or "listening on port" in clean_text.lower():
                    if session_id not in active_ports or active_ports[session_id] == str(port_val):
                        active_ports[session_id] = str(port_val)
                        await port_queue.put(str(port_val))

    asyncio.create_task(stream_and_parse(process.stdout, "system", "server_log"))
    asyncio.create_task(stream_and_parse(process.stderr, "system", "server_log"))
    
    try:
        port = await asyncio.wait_for(port_queue.get(), timeout=90.0)
        ready_event = AgentEvent(
            agent="system",
            status="server_ready",
            data={"url": f"/preview/{session_id}/"},
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        await broadcast_event(ready_event, session_id)
        await log_event(session_id, "system", "server_ready", ready_event.data)
        return recovery_error
    except asyncio.TimeoutError:
        error_msg = "Server failed to start or output a URL within 90 seconds."
        if server_logs:
            error_msg += f"\n\nLast Server Logs:\n" + "\n".join(server_logs)
            
        err_event = AgentEvent(
            agent="system",
            status="error",
            data={"error": error_msg},
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        try:
            process.terminate()
        except ProcessLookupError:
            pass
        await broadcast_event(err_event, session_id)
        await log_event(session_id, "system", "error", err_event.data)
        return recovery_error or {"source": "system", "error": "Dev server timed out."}

@app.websocket("/ws")
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
                prompt = payload.get("prompt")
                
                # Default project name from first 20 chars of prompt
                project_name = prompt[:20] + "..." if len(prompt) > 20 else prompt
                workspace_dir = os.path.join(os.path.dirname(__file__), "workspace", f"app_{session_id}")
                
                # Persist project and user message
                await create_or_update_project(session_id, project_name, workspace_dir)
                await add_chat_message(session_id, "user", prompt)
                
                async def run_pipeline_task():
                    from workflows.pipeline import create_pipeline
                    pipeline = create_pipeline()
                    
                    state = {
                        "user_prompt": prompt,
                        "session_id": session_id,
                        "workspace_dir": workspace_dir,
                        "messages": [],
                        "plan": {},
                        "execution_order": [],
                        "current_step_idx": 0,
                        "validation_errors": {},
                        "retry_counts": {},
                        "last_active_agent": ""
                    }
                    
                    max_retries = 2
                    retries = 0
                    
                    while retries <= max_retries:
                        try:
                            start_event = AgentEvent(
                                agent="supervisor",
                                status="working",
                                data={"message": "Supervisor is analyzing the request and planning tasks..." if retries == 0 else f"Auto Error Recovery (Attempt {retries}/{max_retries})..."},
                                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
                            )
                            await broadcast_event(start_event, session_id)
                            
                            async def my_stream_callback(agent_name: str, token: str):
                                event = AgentEvent(
                                    agent=agent_name,
                                    status="streaming",
                                    data={"token": token},
                                    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
                                )
                                await broadcast_event(event, session_id)
                                
                            async for event_chunk in pipeline.astream(state, config={"configurable": {"stream_callback": my_stream_callback, "workspace_dir": workspace_dir}}):
                                for node_name, updated_state in event_chunk.items():
                                    # Update our outer state with the latest graph state
                                    state = updated_state
                                    
                                    # Announce completion of the current node
                                    event = AgentEvent(
                                        agent=node_name,
                                        status="finished",
                                        data={"message": f"{node_name.capitalize()} completed its task."},
                                        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
                                    )
                                    await broadcast_event(event, session_id)
                                    await log_event(session_id, node_name, "finished", event.data)
                                    
                                    # Predict and announce the next node so the UI shows the correct animation
                                    order = updated_state.get("execution_order", [])
                                    idx = updated_state.get("current_step_idx", 0)
                                    next_agent = "finish"
                                    
                                    if node_name == "database":
                                        next_agent = "supervisor"
                                    elif node_name in ["backend", "frontend"]:
                                        next_agent = "validator"
                                    elif node_name == "validator":
                                        next_agent = "supervisor"
                                    elif node_name == "supervisor":
                                        if idx < len(order): 
                                            next_agent = order[idx].lower()
                                        else: 
                                            next_agent = "finish"
                                        
                                    if next_agent != "finish":
                                        next_event = AgentEvent(
                                            agent=next_agent,
                                            status="working",
                                            data={"message": f"{next_agent.capitalize()} is now working..."},
                                            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
                                        )
                                        await broadcast_event(next_event, session_id)
                                        await log_event(session_id, next_agent, "working", next_event.data)

                            # Finished all steps! (Outside astream loop)
                            if os.path.exists(workspace_dir):
                                # Save assistant message
                                chat_msg = "I've finished building your app! Starting local dev server..." if retries == 0 else "Applied fixes! Verifying build..."
                                await add_chat_message(session_id, "assistant", chat_msg)
                                
                                chat_event = AgentEvent(
                                    agent="assistant",
                                    status="chat_message",
                                    data={"message": chat_msg},
                                    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
                                )
                                await broadcast_event(chat_event, session_id)
                                
                                # Generate/Update project structure index
                                generate_project_structure(workspace_dir)
                                
                                start_event = AgentEvent(
                                    agent="system",
                                    status="server_starting",
                                    data={"message": "Installing dependencies and starting local dev server..."},
                                    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
                                )
                                await broadcast_event(start_event, session_id)
                                
                                # This will return an error dict if vite build fails
                                recovery_error = await start_dev_server(session_id, workspace_dir)
                                
                                if recovery_error and recovery_error.get("source") in ["frontend", "backend"]:
                                    # We hit a recoverable error!
                                    retries += 1
                                    if retries <= max_retries:
                                        # Loop continues with updated state
                                        state["validation_errors"] = {recovery_error["source"]: recovery_error["error"]}
                                        state["execution_order"] = [recovery_error["source"]]
                                        state["current_step_idx"] = 0
                                        if "retry_counts" not in state:
                                            state["retry_counts"] = {}
                                        state["retry_counts"][recovery_error["source"]] = retries
                                        # while-loop continues
                                    else:
                                        # Max retries exceeded
                                        await add_chat_message(session_id, "assistant", "I tried to auto-fix the code, but the errors persist. You can check the code editor to fix it manually.")
                                        retries = max_retries + 1 # Force exit while loop
                                else:
                                    # Success! Or unrecoverable system error (like pnpm missing)
                                    retries = max_retries + 1 # Force exit while loop
                            else:
                                retries = max_retries + 1 # Break if workspace_dir somehow missing
                                            
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                            
                            err_msg = str(e)
                            try:
                                import tenacity
                                if isinstance(e, tenacity.RetryError):
                                    actual_err = e.last_attempt.exception()
                                    if actual_err:
                                        err_msg = str(actual_err)
                                        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                                            err_msg = "Google Gemini API Quota Exceeded! You have hit the hard limit for your API key (e.g. 500 requests/day). Please wait or try a different key."
                            except:
                                pass
                                
                            err_event = AgentEvent(
                                agent="system",
                                status="error",
                                data={"error": err_msg},
                                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
                            )
                            await broadcast_event(err_event, session_id)
                            break # Break out of retries on fatal python exception

                
                asyncio.create_task(run_pipeline_task())
                
            elif payload.get("type") == "start_server":
                session_id = payload.get("session_id")
                if session_id:
                    workspace_dir = os.path.join(os.path.dirname(__file__), "workspace", f"app_{session_id}")
                    if os.path.exists(workspace_dir):
                        start_event = AgentEvent(
                            agent="system",
                            status="server_starting",
                            data={"message": "Waking up previous project and starting dev server..."},
                            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
                        )
                        await broadcast_event(start_event, session_id)
                        asyncio.create_task(start_dev_server(session_id, workspace_dir))
                        
    except WebSocketDisconnect:
        sess_id = active_connections.get(websocket)
        if sess_id:
            # We explicitly do NOT kill the dev server here!
            # The test script exits when it receives 'server_ready',
            # so the dev server must stay alive for the preview proxy.
            # It will be cleaned up by stop_all_dev_servers() on the next run.
            pass
        if websocket in active_connections:
            del active_connections[websocket]
 
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def catch_all_proxy(path: str, request: Request):
    session_id = request.cookies.get("preview_session")
    
    if not session_id:
        referer = request.headers.get("referer", "")
        if "/preview/" in referer:
            try:
                parts = referer.split("/preview/")
                if len(parts) > 1:
                    session_id = parts[1].split("/")[0]
            except Exception:
                pass
                
    print(f"[DEBUG] catch_all_proxy path={path}, initial_session_id={session_id}, len(active_ports)={len(active_ports)}")
    if not session_id and len(active_ports) == 1:
        session_id = list(active_ports.keys())[0]
        
    if session_id and session_id in active_ports:
        port = active_ports[session_id]
        proxy_host = "127.0.0.1"
        url = f"http://{proxy_host}:{port}{request.url.path}"
        print(f"[DEBUG] catch_all_proxy proxing to {url}")
        
        query_string = request.url.query
        if query_string:
            url += f"?{query_string}"
            
        headers = dict(request.headers)
        headers["host"] = f"{proxy_host}:{port}"
        # Some frameworks (like Next.js) strictly validate Origin
        if "origin" in headers:
            headers["origin"] = f"http://{proxy_host}:{port}"
        if "referer" in headers:
            headers["referer"] = headers["referer"].replace(request.url.netloc, f"{proxy_host}:{port}")
        
        try:
            req = httpx_client.build_request(
                request.method,
                url,
                headers=headers,
                content=await request.body()
            )
            response = await httpx_client.send(req, stream=True)
            return StreamingResponse(
                response.aiter_raw(),
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except Exception as e:
            if "127.0.0.1" in url:
                try:
                    url_ipv6 = url.replace("127.0.0.1", "[::1]")
                    req = httpx_client.build_request(request.method, url_ipv6, headers=headers, content=await request.body())
                    response = await httpx_client.send(req, stream=True)
                    return StreamingResponse(response.aiter_raw(), status_code=response.status_code, headers=dict(response.headers))
                except Exception:
                    pass
            print(f"[DEBUG] catch_all_proxy error: {e}")
            
    return JSONResponse({"error": "Not Found", "path": path}, status_code=404)

@app.websocket("/preview/{session_id}/{path:path}")
async def proxy_preview_websocket(websocket: WebSocket, session_id: str, path: str):
    import time
    last_active_timestamps[session_id] = time.time()
    
    port = active_ports.get(session_id)
    if not port:
        await websocket.close(code=1011)
        return
        
    raw_path = websocket.url.path
    proxy_host = "127.0.0.1"
    url = f"ws://{proxy_host}:{port}{raw_path}"
    
    query_string = websocket.url.query
    if query_string:
        url += f"?{query_string}"
        
    try:
        await websocket.accept()
        
        ws_headers = {}
        ws_headers["Host"] = f"{proxy_host}:{port}"
        if "origin" in websocket.headers:
            ws_headers["Origin"] = f"http://{proxy_host}:{port}"
            
        import inspect
        sig = inspect.signature(websockets.connect)
        connect_kwargs = {}
        if "additional_headers" in sig.parameters:
            connect_kwargs["additional_headers"] = ws_headers
        else:
            connect_kwargs["extra_headers"] = ws_headers

        async with websockets.connect(url, **connect_kwargs) as target_ws:
            async def forward_to_target():
                try:
                    while True:
                        msg = await websocket.receive()
                        last_active_timestamps[session_id] = time.time()
                        if "text" in msg and msg["text"] is not None:
                            await target_ws.send(msg["text"])
                        elif "bytes" in msg and msg["bytes"] is not None:
                            await target_ws.send(msg["bytes"])
                except Exception:
                    pass

            async def forward_from_target():
                try:
                    while True:
                        msg = await target_ws.recv()
                        last_active_timestamps[session_id] = time.time()
                        if isinstance(msg, str):
                            await websocket.send_text(msg)
                        else:
                            await websocket.send_bytes(msg)
                except Exception:
                    pass
            
            await asyncio.gather(
                forward_to_target(),
                forward_from_target()
            )
            try:
                await websocket.close()
            except Exception:
                pass
    except Exception as e:
        print(f"[WS Proxy Error] {e}")
        try:
            await websocket.close(code=1011)
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("BACKEND_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
