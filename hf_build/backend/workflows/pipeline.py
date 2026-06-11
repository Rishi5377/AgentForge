from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing import TypedDict, Dict, Any, Annotated
from agents.supervisor import generate_task_plan
from agents.validator import ValidatorAgent
import json
import shutil
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, Field

from llm.llm_client import get_backend_model, get_frontend_model, get_database_model
from utils.project_indexer import generate_project_structure

class ReplacementChunk(BaseModel):
    start_line: int = Field(description="Starting line number of the chunk (1-indexed).")
    end_line: int = Field(description="Ending line number of the chunk (1-indexed).")
    target_content: str = Field(description="The exact string content currently in the file to replace.")
    replacement_content: str = Field(description="The new content to replace the target_content with.")

class FileEdit(BaseModel):
    filepath: str = Field(description="The relative path to the file in the workspace (e.g. 'src/App.tsx')")
    content: str = Field(default="", description="The complete content of the file. You MUST provide the full file contents, even when editing existing files.")
    is_edit: bool = Field(default=False)
    search_block: str = Field(default="")
    replace_block: str = Field(default="")

class AgentOutput(BaseModel):
    files: list[FileEdit]

class GraphState(TypedDict):
    user_prompt: str
    session_id: str
    workspace_dir: str
    messages: Annotated[list, add_messages]
    plan: dict
    execution_order: list
    current_step_idx: int
    validation_errors: dict
    retry_counts: dict
    next_worker: str
    last_active_agent: str
    qa_retry_count: int

async def run_supervisor(state: GraphState):
    if not state.get("plan"):
        plan_obj = await generate_task_plan(state.get("user_prompt", ""), state)
        plan_dict = plan_obj.model_dump()
        state["plan"] = plan_dict
        state["execution_order"] = plan_dict.get("execution_order", [])
        state["current_step_idx"] = 0
        
        # Instantiate boilerplate template
        import os
        from utils.template_engine import TemplateEngine
        workspace_dir = state.get("workspace_dir")
        if workspace_dir:
            template_name = plan_dict.get("project_template", "react-tailwind")
            if template_name and template_name.lower() != "none":
                try:
                    from utils.template_engine import TemplateEngine
                except ImportError:
                    from backend.utils.template_engine import TemplateEngine
                
                templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
                engine = TemplateEngine(templates_dir)
                # Only instantiate if directory does not exist or is empty
                import asyncio
                if not os.path.exists(workspace_dir) or not os.listdir(workspace_dir):
                    try:
                        await asyncio.to_thread(engine.instantiate_template, template_name, workspace_dir, project_name=os.path.basename(workspace_dir))
                    except ValueError:
                        os.makedirs(workspace_dir, exist_ok=True)
            
            # Inject pre-baked UI blocks from assembly plan
            assembly_plan = plan_dict.get("assembly_plan", [])
            if assembly_plan:
                await asyncio.to_thread(engine.copy_blocks, assembly_plan, workspace_dir)
                
            # Inject pre-baked backend modules from backend assembly plan
            backend_assembly_plan = plan_dict.get("backend_assembly_plan", [])
            if backend_assembly_plan:
                await asyncio.to_thread(engine.copy_backend_blocks, backend_assembly_plan, workspace_dir)
                
    return state

def _load_prompt(filename: str) -> str:
    import os
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', filename)
    if os.path.exists(prompt_path):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def db_prompt_modifier(state: GraphState):
    tasks_str = state.get("plan", {}).get("agent_tasks", {}).get("database", "")
    user_prompt = state.get("user_prompt", "")
    base_prompt = _load_prompt('database.txt')
    return f"{base_prompt}\n\nYou are a Database Architect. Implement the following database schema tasks.\nIMPORTANT: Do NOT prefix file paths with the project or template name. Write directly to the root (e.g., 'src/schema.ts').\n\nOriginal User Request: {user_prompt}\n\nTask: {tasks_str}"

def backend_prompt_modifier(state: GraphState):
    tasks_str = state.get("plan", {}).get("agent_tasks", {}).get("backend", "")
    user_prompt = state.get("user_prompt", "")
    template = state.get("plan", {}).get("project_template", "react-tailwind")
    error = state.get("validation_errors", {}).get("backend", "")
    err_str = f"\nURGENT LINTER ERROR:\nYour previous code failed to compile. You are in RECOVERY MODE. You MUST fix the following build error. ONLY apply the minimal changes needed to fix the error. DO NOT rewrite the entire logic.\n{error}\n" if error else ""
    base_prompt = _load_prompt('backend.txt')
    framework_prompt = _load_prompt(f'frameworks/{template}.txt')
    return f"{base_prompt}\n{framework_prompt}\n\nYou are a Senior Backend Node.js Engineer. Implement the backend.\nIMPORTANT: Do NOT prefix file paths with the project or template name '{template}'. Write directly to the root (e.g., 'src/index.ts').\nCRITICAL: If you modify package.json, you MUST keep ALL existing dependencies and devDependencies from the provided context. Do not delete React or Vite!\n\nOriginal User Request: {user_prompt}\n\nTask: {tasks_str}\nProject Template: {template}\n{err_str}"

def frontend_prompt_modifier(state: GraphState):
    tasks_str = state.get("plan", {}).get("agent_tasks", {}).get("frontend", "")
    user_prompt = state.get("user_prompt", "")
    template = state.get("plan", {}).get("project_template", "react-tailwind")
    error = state.get("validation_errors", {}).get("frontend", "")
    err_str = f"\nURGENT LINTER ERROR:\nYour previous code failed to compile. You are in RECOVERY MODE. You MUST fix the following build error. ONLY apply the minimal changes needed to fix the error. Remove unused variables/imports as instructed. DO NOT rewrite the entire logic.\n{error}\n" if error else ""
    
    design_guidelines = ""
    import os
    workspace_dir = state.get("workspace_dir")
    if workspace_dir:
        design_path = os.path.join(workspace_dir, "DESIGN.md")
        if os.path.exists(design_path):
            with open(design_path, "r", encoding="utf-8") as f:
                design_content = f.read()
            design_guidelines = f"\n\n### MANDATORY DESIGN SYSTEM GUIDELINES\nYou MUST strictly follow these design guidelines for all UI elements:\n{design_content}\n"

    base_prompt = _load_prompt('frontend.txt')
    framework_prompt = _load_prompt(f'frameworks/{template}.txt')
    return f"{base_prompt}\n{framework_prompt}\n\nYou are a Senior React Developer. Implement the frontend.\nIMPORTANT: Do NOT prefix file paths with the project or template name '{template}'. Write directly to the root (e.g., 'src/App.tsx' or 'src/App.jsx').\nCRITICAL: If you modify package.json, you MUST keep ALL existing dependencies and devDependencies from the provided context.\n\nOriginal User Request: {user_prompt}\n\nTask: {tasks_str}\nProject Template: {template}\n{err_str}{design_guidelines}"

async def mark_db_active(state: GraphState):
    return {"last_active_agent": "database"}

async def mark_backend_active(state: GraphState):
    return {"last_active_agent": "backend"}

async def mark_frontend_active(state: GraphState):
    return {"last_active_agent": "frontend"}

async def advance_step(state: GraphState):
    return {"current_step_idx": state.get("current_step_idx", 0) + 1}

def qa_prompt_modifier(state: GraphState):
    user_prompt = state.get("user_prompt", "")
    template = state.get("plan", {}).get("project_template", "react-tailwind")
    error = state.get("validation_errors", {}).get("qa", "")
    base_prompt = _load_prompt('qa.txt')
    framework_prompt = _load_prompt(f'frameworks/{template}.txt')
    return f"{base_prompt}\n{framework_prompt}\n\nProject Template: {template}\nOriginal User Request: {user_prompt}\n\nURGENT COMPILER ERROR:\n{error}\n"

async def run_tests_node(state: GraphState):
    import subprocess
    import os
    import re
    import asyncio
    workspace_dir = state.get("workspace_dir")
    
    if "qa_retry_count" not in state:
        state["qa_retry_count"] = 0
        
    if "validation_errors" not in state:
        state["validation_errors"] = {}
        
    print(f"\n--- Running QA Test pass #{state['qa_retry_count'] + 1} ---")
    
    qa_env = os.environ.copy()
    qa_env["NODE_OPTIONS"] = "--max-old-space-size=4096"
    qa_env["NEXT_TELEMETRY_DISABLED"] = "1"

    pnpm_path = shutil.which("pnpm") or "pnpm"
    npm_path = shutil.which("npm") or "npm"
    npx_path = shutil.which("npx") or "npx"

    nice_prefix = "nice -n 19 " if os.name != "nt" else ""
    if os.path.exists(os.path.join(workspace_dir, "prisma", "schema.prisma")):
        await asyncio.to_thread(subprocess.run, f'{nice_prefix}"{npx_path}" prisma format', shell=True, cwd=workspace_dir, capture_output=True, env=qa_env)
        await asyncio.to_thread(subprocess.run, f'{nice_prefix}"{npx_path}" prisma generate', shell=True, cwd=workspace_dir, capture_output=True, env=qa_env)
        
    print("Installing dependencies before test...")
    nice_prefix = "nice -n 19 " if os.name != "nt" else ""
    pnpm_path = shutil.which("pnpm") or "pnpm"
    npm_path = shutil.which("npm") or "npm"
    npx_path = shutil.which("npx") or "npx"
    
    # Optimize installation speed: forcefully use pnpm by default
    install_res = await asyncio.to_thread(subprocess.run, f'{nice_prefix}"{pnpm_path}" install --no-frozen-lockfile --prefer-offline --reporter=silent', shell=True, cwd=workspace_dir, capture_output=True, text=True, env=qa_env)
        
    if install_res.returncode != 0:
        print(f"pnpm install failed: {install_res.stderr} | {install_res.stdout}")
        print("Falling back to npm install...")
        install_res = await asyncio.to_thread(subprocess.run, f'{nice_prefix}"{npm_path}" install --no-audit --no-fund --legacy-peer-deps --loglevel=error', shell=True, cwd=workspace_dir, capture_output=True, text=True, env=qa_env)
        if install_res.returncode != 0:
            print(f"Fallback npm install also failed: {install_res.stderr} | {install_res.stdout}")
        
    result = await asyncio.to_thread(subprocess.run, f'{nice_prefix}"{npx_path}" -p typescript tsc --noEmit', shell=True, cwd=workspace_dir, capture_output=True, text=True, env=qa_env)
    
    if result.returncode == 0:
        print("QA Test Passed! No errors.")
        state["validation_errors"]["qa"] = ""
    else:
        print("QA Test Failed. Parsing errors...")
        full_err = result.stdout + "\n" + result.stderr
        
        filtered_lines = []
        for line in full_err.split("\n"):
            if re.search(r'(error TS|Type error|SyntaxError|PrismaClient)', line, re.IGNORECASE):
                filtered_lines.append(line.strip())
            elif re.search(r'^src/.*(ts|tsx|js|jsx)[\(:]', line):
                filtered_lines.append(line.strip())
                
        if not filtered_lines:
            filtered_lines = full_err.split("\n")[:20]
            
        error_str = "\n".join(filtered_lines)
        state["validation_errors"]["qa"] = error_str
        state["qa_retry_count"] += 1
        print(f"QA Filtered Errors:\n{error_str}")
        
    return state

def route_worker(state: GraphState) -> str:
    order = state.get("execution_order", [])
    idx = state.get("current_step_idx", 0)
    if idx < len(order):
        worker = order[idx].lower()
        if worker in ["database", "backend", "frontend"]:
            return worker
    return "finish"

def apply_file_edit(workspace_dir: str, file_edit: FileEdit):
    import os
    full_path = os.path.abspath(os.path.join(workspace_dir, file_edit.filepath))
    if not full_path.startswith(os.path.abspath(workspace_dir)):
        return # Path traversal protection

    if file_edit.filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.webp')):
        print(f"Skipping binary image file write for {file_edit.filepath}")
        return # Block writing text contents to binary image files

    if file_edit.is_edit:
        if not os.path.exists(full_path):
            raise ValueError(f"Cannot edit file {file_edit.filepath}: File does not exist.")
        
        with open(full_path, "r", encoding="utf-8") as f:
            file_data = f.read()
            
        if file_edit.search_block in file_data:
            file_data = file_data.replace(file_edit.search_block, file_edit.replace_block)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file_data)
        else:
            raise ValueError(f"Search block not found in {file_edit.filepath}. Ensure you match the existing code exactly, including indentation and whitespace.")
    else:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if file_edit.content:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file_edit.content)

def extract_xml_files(content) -> list[FileEdit]:
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                text_parts.append(block["text"])
            elif isinstance(block, str):
                text_parts.append(block)
        content = "".join(text_parts)
    elif not isinstance(content, str):
        content = str(content)
        
    import re
    files = []
    
    # 1. Parse <file> blocks
    file_pattern = r'<file\s+path=["\']([^"\']+)["\']>(.*?)</file>'
    for match in re.finditer(file_pattern, content, re.DOTALL):
        filepath = match.group(1).strip()
        file_content = match.group(2).strip()
        if file_content.startswith("```"):
            lines = file_content.split("\n")
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"): lines = lines[:-1]
            file_content = "\n".join(lines).strip()
        files.append(FileEdit(filepath=filepath, content=file_content))
        
    # 2. Parse <edit> blocks
    edit_pattern = r'<edit\s+path=["\']([^"\']+)["\']>(.*?)</edit>'
    for match in re.finditer(edit_pattern, content, re.DOTALL):
        filepath = match.group(1).strip()
        edit_content = match.group(2)
        search_match = re.search(r'<search>(.*?)</search>', edit_content, re.DOTALL)
        replace_match = re.search(r'<replace>(.*?)</replace>', edit_content, re.DOTALL)
        
        if search_match and replace_match:
            search_block = search_match.group(1).strip("\n")
            replace_block = replace_match.group(1).strip("\n")
            files.append(FileEdit(filepath=filepath, is_edit=True, search_block=search_block, replace_block=replace_block))

    return files

def create_single_shot_agent(model, prompt_func):
    from google.genai.errors import ClientError
    import tenacity
    
    def retry_if_api_error(exception):
        if isinstance(exception, ClientError) and exception.code in [429, 500, 502, 503, 504]:
            return True
        if "429" in str(exception) or "RESOURCE_EXHAUSTED" in str(exception):
            return True
        return False

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30), retry=tenacity.retry_if_exception(retry_if_api_error))
    async def invoke_with_retry(messages):
        return await model.ainvoke(messages)

    async def agent_node(state: GraphState, config: RunnableConfig):
        system_prompt = prompt_func(state)
        
        # Inject context for files to edit
        files_to_edit = state.get("plan", {}).get("files_to_edit", [])
        workspace_dir = state.get("workspace_dir")
        
        if workspace_dir:
            import os
            import re
            context_str = "\n\n### EXISTING FILE CONTENTS FOR EDITING ###\n"
            
            # If there's an error, try to extract file paths from the error log so the agent can see them
            active_errors = state.get("validation_errors", {}).values()
            for active_error in active_errors:
                if active_error:
                    # Match typical compiler outputs like src/App.tsx(1,8) or src/file.ts:10
                    error_files = re.findall(r'([a-zA-Z0-9_/\.\-]+\.[a-zA-Z0-9]+)[\(:]', str(active_error))
                    for ef in set(error_files):
                        if ef not in files_to_edit:
                            files_to_edit.append(ef)
            
            # ALWAYS inject package.json so agents don't overwrite it blindly
            pkg_path = os.path.join(workspace_dir, "package.json")
            if os.path.exists(pkg_path):
                try:
                    with open(pkg_path, "r", encoding="utf-8") as f:
                        context_str += f"\n--- package.json ---\n{f.read()}\n"
                except Exception:
                    pass
            
            # SMART CONTEXT: Inject explicitly required files + reusable components to save quota while maintaining quality
            struct_path = os.path.join(workspace_dir, "project_structure.md")
            if os.path.exists(struct_path):
                try:
                    with open(struct_path, "r", encoding="utf-8") as f:
                        context_str += f"\n### PROJECT STRUCTURE ###\n{f.read()}\n"
                except Exception:
                    pass
            
            for root, dirs, files in os.walk(workspace_dir):
                dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", "build", ".vite", ".next", ".swc", "public"]]
                for f in files:
                    if f.endswith(('.js', '.jsx', '.ts', '.tsx', '.css', '.html', '.sql', '.md')):
                        rel_path = os.path.relpath(os.path.join(root, f), workspace_dir).replace('\\', '/')
                        if rel_path == "package.json": continue
                        
                        # Inject if it's explicitly edited, a reusable component/utility, or a core layout file
                        path_parts = rel_path.split('/')
                        is_reusable = "components" in path_parts or "lib" in path_parts or "utils" in path_parts or "backend_blocks" in path_parts
                        is_route = "app" in path_parts or "pages" in path_parts or "routes" in path_parts or "views" in path_parts or "hooks" in path_parts
                        is_core = rel_path in ["src/App.tsx", "src/index.css", "src/app/layout.tsx", "src/app/globals.css", "src/lib/db.ts", "server.js", "src/server.js"]
                        
                        if rel_path in files_to_edit or is_reusable or is_core or is_route:
                            full_path = os.path.join(root, f)
                            try:
                                with open(full_path, "r", encoding="utf-8") as file_obj:
                                    content = file_obj.read()
                                context_str += f"\n--- {rel_path} ---\n{content}\n"
                            except Exception:
                                pass

        messages = [
            SystemMessage(content=system_prompt + context_str),
            HumanMessage(content="Please implement the required files using the <file> XML tags.")
        ]
        
        result = await invoke_with_retry(messages)
        parsed_files = extract_xml_files(result.content) if result else []
        
        edit_errors = []
        if parsed_files and workspace_dir:
            for file_edit in parsed_files:
                try:
                    apply_file_edit(workspace_dir, file_edit)
                except ValueError as e:
                    edit_errors.append(str(e))
                        
        from langchain_core.messages import AIMessage
        if edit_errors:
            return {"messages": [AIMessage(content=f"Failed to write some files: {edit_errors}")], "validation_errors": {"general": "\n".join(edit_errors)}}
        return {"messages": [AIMessage(content=f"Wrote {len(parsed_files)} files.")]}
        
    return agent_node


def create_dynamic_backend_agent(model, prompt_func):
    from google.genai.errors import ClientError
    import tenacity
    import asyncio
    
    def retry_if_api_error(exception):
        if isinstance(exception, ClientError) and exception.code in [429, 500, 502, 503, 504]:
            return True
        if "429" in str(exception) or "RESOURCE_EXHAUSTED" in str(exception):
            return True
        return False

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30), retry=tenacity.retry_if_exception(retry_if_api_error))
    async def invoke_with_retry(messages):
        return await model.ainvoke(messages)

    async def agent_node(state: GraphState, config: RunnableConfig):
        system_prompt = prompt_func(state)
        complexity = state.get("plan", {}).get("complexity", "EASY").upper()
        
        files_to_edit = state.get("plan", {}).get("files_to_edit", [])
        workspace_dir = state.get("workspace_dir")
        
        context_str = ""
        if workspace_dir:
            import os
            import re
            context_str = "\n\n### EXISTING FILE CONTENTS FOR EDITING ###\n"
            active_errors = state.get("validation_errors", {}).values()
            for active_error in active_errors:
                if active_error:
                    error_files = re.findall(r'([a-zA-Z0-9_/\.\-]+\.[a-zA-Z0-9]+)[\(:]', str(active_error))
                    for ef in set(error_files):
                        if ef not in files_to_edit:
                            files_to_edit.append(ef)
            
            pkg_path = os.path.join(workspace_dir, "package.json")
            if os.path.exists(pkg_path):
                try:
                    with open(pkg_path, "r", encoding="utf-8") as f:
                        context_str += f"\n--- package.json ---\n{f.read()}\n"
                except Exception:
                    pass
            
            struct_path = os.path.join(workspace_dir, "project_structure.md")
            if os.path.exists(struct_path):
                try:
                    with open(struct_path, "r", encoding="utf-8") as f:
                        context_str += f"\n### PROJECT STRUCTURE ###\n{f.read()}\n"
                except Exception:
                    pass
            
            for root, dirs, files in os.walk(workspace_dir):
                dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", "build", ".vite", ".next", ".swc", "public"]]
                for f in files:
                    if f.endswith(('.js', '.jsx', '.ts', '.tsx', '.css', '.html', '.sql', '.md')):
                        rel_path = os.path.relpath(os.path.join(root, f), workspace_dir).replace('\\', '/')
                        if rel_path == "package.json": continue
                        path_parts = rel_path.split('/')
                        is_reusable = "components" in path_parts or "lib" in path_parts or "utils" in path_parts or "backend_blocks" in path_parts
                        is_route = "app" in path_parts or "pages" in path_parts or "routes" in path_parts or "views" in path_parts or "hooks" in path_parts
                        is_core = rel_path in ["src/App.tsx", "src/index.css", "src/app/layout.tsx", "src/app/globals.css", "src/lib/db.ts", "server.js", "src/server.js"]
                        if rel_path in files_to_edit or is_reusable or is_core or is_route:
                            full_path = os.path.join(root, f)
                            try:
                                with open(full_path, "r", encoding="utf-8") as file_obj:
                                    content = file_obj.read()
                                context_str += f"\n--- {rel_path} ---\n{content}\n"
                            except Exception:
                                pass

        is_recovery = bool(state.get("validation_errors", {}).get("backend", ""))
        
        if is_recovery or complexity in ["EASY", "MODIFICATION"]:
            messages = [
                SystemMessage(content=system_prompt + context_str),
                HumanMessage(content="Please implement the required files using the <file> XML tags. If in recovery, fix the errors.")
            ]
            result = await invoke_with_retry(messages)
            parsed_files = extract_xml_files(result.content) if result else []
            edit_errors = []
            if parsed_files and workspace_dir:
                for file_edit in parsed_files:
                    try:
                        apply_file_edit(workspace_dir, file_edit)
                    except ValueError as e:
                        edit_errors.append(str(e))
            from langchain_core.messages import AIMessage
            if edit_errors:
                return {"messages": [AIMessage(content=f"Failed: {edit_errors}")], "validation_errors": {"backend": "\n".join(edit_errors)}}
            return {"messages": [AIMessage(content=f"Wrote {len(parsed_files)} backend files.")]}
        else:
            print("[BACKEND] Running Phase 1 (Database Models & Utils)...")
            msg_1 = [
                SystemMessage(content=system_prompt + context_str),
                HumanMessage(content="Phase 1: Please implement the core database models, schemas, and shared utilities. DO NOT implement the API routes yet. Use the <file> XML tags.")
            ]
            res_1 = await invoke_with_retry(msg_1)
            parsed_1 = extract_xml_files(res_1.content) if res_1 else []
            phase1_summaries = []
            edit_errors = []
            if parsed_1 and workspace_dir:
                for file_edit in parsed_1:
                    try:
                        apply_file_edit(workspace_dir, file_edit)
                        phase1_summaries.append(f"--- {file_edit.filepath} ---\n{file_edit.content}\n")
                    except ValueError as e:
                        edit_errors.append(str(e))
            
            print("[BACKEND] Sleeping to respect RPM limit...")
            await asyncio.sleep(6)
            
            if edit_errors:
                from langchain_core.messages import AIMessage
                return {"messages": [AIMessage(content=f"Failed Phase 1: {edit_errors}")], "validation_errors": {"backend": "\n".join(edit_errors)}}
            
            print("[BACKEND] Running Phase 2 (API Routes)...")
            phase2_context = "\n\n### PHASE 1 OUTPUT ###\n" + "".join(phase1_summaries)
            msg_2 = [
                SystemMessage(content=system_prompt + context_str + phase2_context),
                HumanMessage(content="Phase 2: Now implement the actual API routes and controllers that use the models from Phase 1. Use the <file> XML tags.")
            ]
            res_2 = await invoke_with_retry(msg_2)
            parsed_2 = extract_xml_files(res_2.content) if res_2 else []
            if parsed_2 and workspace_dir:
                for file_edit in parsed_2:
                    try:
                        apply_file_edit(workspace_dir, file_edit)
                    except ValueError as e:
                        edit_errors.append(str(e))
            
            from langchain_core.messages import AIMessage
            if edit_errors:
                return {"messages": [AIMessage(content=f"Failed Phase 2: {edit_errors}")], "validation_errors": {"backend": "\n".join(edit_errors)}}
            return {"messages": [AIMessage(content=f"Wrote {len(parsed_1)+len(parsed_2)} backend files over 2 phases.")]}
    return agent_node


def create_dynamic_frontend_agent(model, prompt_func):
    from google.genai.errors import ClientError
    import tenacity
    import asyncio
    
    def retry_if_api_error(exception):
        if isinstance(exception, ClientError) and exception.code in [429, 500, 502, 503, 504]:
            return True
        if "429" in str(exception) or "RESOURCE_EXHAUSTED" in str(exception):
            return True
        return False

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30), retry=tenacity.retry_if_exception(retry_if_api_error))
    async def invoke_with_retry(messages):
        return await model.ainvoke(messages)

    async def agent_node(state: GraphState, config: RunnableConfig):
        system_prompt = prompt_func(state)
        complexity = state.get("plan", {}).get("complexity", "EASY").upper()
        
        files_to_edit = state.get("plan", {}).get("files_to_edit", [])
        workspace_dir = state.get("workspace_dir")
        
        context_str = ""
        if workspace_dir:
            import os
            import re
            context_str = "\n\n### EXISTING FILE CONTENTS FOR EDITING ###\n"
            active_errors = state.get("validation_errors", {}).values()
            for active_error in active_errors:
                if active_error:
                    error_files = re.findall(r'([a-zA-Z0-9_/\.\-]+\.[a-zA-Z0-9]+)[\(:]', str(active_error))
                    for ef in set(error_files):
                        if ef not in files_to_edit:
                            files_to_edit.append(ef)
            
            pkg_path = os.path.join(workspace_dir, "package.json")
            if os.path.exists(pkg_path):
                try:
                    with open(pkg_path, "r", encoding="utf-8") as f:
                        context_str += f"\n--- package.json ---\n{f.read()}\n"
                except Exception:
                    pass
            
            struct_path = os.path.join(workspace_dir, "project_structure.md")
            if os.path.exists(struct_path):
                try:
                    with open(struct_path, "r", encoding="utf-8") as f:
                        context_str += f"\n### PROJECT STRUCTURE ###\n{f.read()}\n"
                except Exception:
                    pass
            
            for root, dirs, files in os.walk(workspace_dir):
                dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", "build", ".vite", ".next", ".swc", "public"]]
                for f in files:
                    if f.endswith(('.js', '.jsx', '.ts', '.tsx', '.css', '.html', '.sql', '.md')):
                        rel_path = os.path.relpath(os.path.join(root, f), workspace_dir).replace('\\', '/')
                        if rel_path == "package.json": continue
                        path_parts = rel_path.split('/')
                        is_reusable = "components" in path_parts or "lib" in path_parts or "utils" in path_parts or "backend_blocks" in path_parts
                        is_route = "app" in path_parts or "pages" in path_parts or "routes" in path_parts or "views" in path_parts or "hooks" in path_parts
                        is_core = rel_path in ["src/App.tsx", "src/index.css", "src/app/layout.tsx", "src/app/globals.css", "src/lib/db.ts", "server.js", "src/server.js"]
                        if rel_path in files_to_edit or is_reusable or is_core or is_route:
                            full_path = os.path.join(root, f)
                            try:
                                with open(full_path, "r", encoding="utf-8") as file_obj:
                                    content = file_obj.read()
                                context_str += f"\n--- {rel_path} ---\n{content}\n"
                            except Exception:
                                pass

        is_recovery = bool(state.get("validation_errors", {}).get("frontend", ""))
        
        if is_recovery or complexity in ["EASY", "MODIFICATION"]:
            messages = [
                SystemMessage(content=system_prompt + context_str),
                HumanMessage(content="Please implement the required files using the <file> XML tags.")
            ]
            result = await invoke_with_retry(messages)
            parsed_files = extract_xml_files(result.content) if result else []
            edit_errors = []
            if parsed_files and workspace_dir:
                for file_edit in parsed_files:
                    try:
                        apply_file_edit(workspace_dir, file_edit)
                    except ValueError as e:
                        edit_errors.append(str(e))
            from langchain_core.messages import AIMessage
            if edit_errors:
                return {"messages": [AIMessage(content=f"Failed: {edit_errors}")], "validation_errors": {"frontend": "\n".join(edit_errors)}}
            return {"messages": [AIMessage(content=f"Wrote {len(parsed_files)} frontend files.")]}
            
        elif complexity == "MEDIUM":
            print("[FRONTEND] Running Phase 1 (Layout & Components)...")
            msg_1 = [
                SystemMessage(content=system_prompt + context_str),
                HumanMessage(content="Phase 1: Please implement the required layout, configuration files, and generic reusable UI components. Use the <file> XML tags.")
            ]
            res_1 = await invoke_with_retry(msg_1)
            parsed_1 = extract_xml_files(res_1.content) if res_1 else []
            phase1_summaries = []
            edit_errors = []
            if parsed_1 and workspace_dir:
                for file_edit in parsed_1:
                    try:
                        apply_file_edit(workspace_dir, file_edit)
                        phase1_summaries.append(f"--- {file_edit.filepath} ---\n{file_edit.content}\n")
                    except ValueError as e:
                        edit_errors.append(str(e))
            
            print("[FRONTEND] Sleeping to respect RPM limit...")
            await asyncio.sleep(6)
            
            if edit_errors:
                from langchain_core.messages import AIMessage
                return {"messages": [AIMessage(content=f"Failed Phase 1: {edit_errors}")], "validation_errors": {"frontend": "\n".join(edit_errors)}}

            print("[FRONTEND] Running Phase 2 (Route Pages)...")
            phase2_context = "\n\n### PHASE 1 OUTPUT ###\n" + "".join(phase1_summaries)
            msg_2 = [
                SystemMessage(content=system_prompt + context_str + phase2_context),
                HumanMessage(content="Phase 2: Now implement the actual application route pages. Use the <file> XML tags.")
            ]
            res_2 = await invoke_with_retry(msg_2)
            parsed_2 = extract_xml_files(res_2.content) if res_2 else []
            if parsed_2 and workspace_dir:
                for file_edit in parsed_2:
                    try:
                        apply_file_edit(workspace_dir, file_edit)
                    except ValueError as e:
                        edit_errors.append(str(e))
                    
            from langchain_core.messages import AIMessage
            if edit_errors:
                return {"messages": [AIMessage(content=f"Failed Phase 2: {edit_errors}")], "validation_errors": {"frontend": "\n".join(edit_errors)}}
            return {"messages": [AIMessage(content=f"Wrote {len(parsed_1)+len(parsed_2)} frontend files over 2 phases.")]}
            
        else: # HARD
            print("[FRONTEND] Running Phase 1 (Core Shell & Config)...")
            msg_1 = [
                SystemMessage(content=system_prompt + context_str),
                HumanMessage(content="Phase 1: Please implement the core shell, package.json updates, global CSS, layout components, and router configuration. Use the <file> XML tags.")
            ]
            res_1 = await invoke_with_retry(msg_1)
            parsed_1 = extract_xml_files(res_1.content) if res_1 else []
            phase1_summaries = []
            edit_errors = []
            if parsed_1 and workspace_dir:
                for file_edit in parsed_1:
                    try:
                        apply_file_edit(workspace_dir, file_edit)
                        phase1_summaries.append(f"--- {file_edit.filepath} ---\n{file_edit.content}\n")
                    except ValueError as e:
                        edit_errors.append(str(e))
            
            print("[FRONTEND] Sleeping to respect RPM limit...")
            await asyncio.sleep(6)
            
            if edit_errors:
                from langchain_core.messages import AIMessage
                return {"messages": [AIMessage(content=f"Failed Phase 1: {edit_errors}")], "validation_errors": {"frontend": "\n".join(edit_errors)}}
            
            print("[FRONTEND] Running Phase 2 (Reusable Components)...")
            phase2_context = "\n\n### PHASE 1 OUTPUT ###\n" + "".join(phase1_summaries)
            msg_2 = [
                SystemMessage(content=system_prompt + context_str + phase2_context),
                HumanMessage(content="Phase 2: Now implement generic reusable UI components (cards, buttons, inputs). DO NOT write the main pages yet. Use the <file> XML tags.")
            ]
            res_2 = await invoke_with_retry(msg_2)
            parsed_2 = extract_xml_files(res_2.content) if res_2 else []
            phase2_summaries = []
            if parsed_2 and workspace_dir:
                for file_edit in parsed_2:
                    try:
                        apply_file_edit(workspace_dir, file_edit)
                        phase2_summaries.append(f"--- {file_edit.filepath} ---\n{file_edit.content}\n")
                    except ValueError as e:
                        edit_errors.append(str(e))
            
            print("[FRONTEND] Sleeping to respect RPM limit...")
            await asyncio.sleep(6)
            
            if edit_errors:
                from langchain_core.messages import AIMessage
                return {"messages": [AIMessage(content=f"Failed Phase 2: {edit_errors}")], "validation_errors": {"frontend": "\n".join(edit_errors)}}
            
            print("[FRONTEND] Running Phase 3 (Route Pages)...")
            phase3_context = phase2_context + "\n\n### PHASE 2 OUTPUT ###\n" + "".join(phase2_summaries)
            msg_3 = [
                SystemMessage(content=system_prompt + context_str + phase3_context),
                HumanMessage(content="Phase 3: Now implement the actual application route pages and hook them up. Use the <file> XML tags.")
            ]
            res_3 = await invoke_with_retry(msg_3)
            parsed_3 = extract_xml_files(res_3.content) if res_3 else []
            if parsed_3 and workspace_dir:
                for file_edit in parsed_3:
                    try:
                        apply_file_edit(workspace_dir, file_edit)
                    except ValueError as e:
                        edit_errors.append(str(e))
                        
            from langchain_core.messages import AIMessage
            if edit_errors:
                return {"messages": [AIMessage(content=f"Failed Phase 3: {edit_errors}")], "validation_errors": {"frontend": "\n".join(edit_errors)}}
            return {"messages": [AIMessage(content=f"Wrote {len(parsed_1)+len(parsed_2)+len(parsed_3)} frontend files over 3 phases.")]}
    return agent_node


def create_pipeline():
    workflow = StateGraph(GraphState)
    
    workflow.add_node("supervisor", run_supervisor)
    
    # Custom agents
    db_agent = create_single_shot_agent(get_database_model(), prompt_func=db_prompt_modifier)
    backend_agent = create_dynamic_backend_agent(get_backend_model(), prompt_func=backend_prompt_modifier)
    frontend_agent = create_dynamic_frontend_agent(get_frontend_model(), prompt_func=frontend_prompt_modifier)
    
    # Wrappers to track state
    async def db_node(state: GraphState, config: RunnableConfig):
        await mark_db_active(state)
        res = await db_agent(state, config)
        if not res.get("validation_errors", {}).get("database"):
            res["current_step_idx"] = state.get("current_step_idx", 0) + 1
        res["last_active_agent"] = "database"
        return res

    async def backend_node(state: GraphState, config: RunnableConfig):
        await mark_backend_active(state)
        res = await backend_agent(state, config)
        if not res.get("validation_errors", {}).get("backend"):
            res["current_step_idx"] = state.get("current_step_idx", 0) + 1
        res["last_active_agent"] = "backend"
        return res

    async def frontend_node(state: GraphState, config: RunnableConfig):
        await mark_frontend_active(state)
        res = await frontend_agent(state, config)
        if not res.get("validation_errors", {}).get("frontend"):
            res["current_step_idx"] = state.get("current_step_idx", 0) + 1
        res["last_active_agent"] = "frontend"
        return res

    workflow.add_node("database", db_node)
    workflow.add_node("backend", backend_node)
    workflow.add_node("frontend", frontend_node)
    workflow.add_node("run_tests", run_tests_node)
    
    qa_agent = create_single_shot_agent(get_backend_model(), prompt_func=qa_prompt_modifier)
    async def qa_agent_node(state: GraphState, config: RunnableConfig):
        return await qa_agent(state, config)
        
    workflow.add_node("qa_agent", qa_agent_node)
    
    workflow.set_entry_point("supervisor")
    
    workflow.add_conditional_edges(
        "supervisor",
        route_worker,
        {
            "database": "database",
            "backend": "backend",
            "frontend": "frontend",
            "finish": "run_tests"
        }
    )
    
    def qa_router(state: GraphState) -> str:
        err = state.get("validation_errors", {}).get("qa", "")
        retries = state.get("qa_retry_count", 0)
        if err:
            if retries < 3:
                return "qa_agent"
            else:
                return "__end__"
        else:
            return "__end__"
            
    workflow.add_conditional_edges("run_tests", qa_router, {
        "qa_agent": "qa_agent",
        "__end__": "__end__"
    })
    
    workflow.add_edge("database", "supervisor")
    workflow.add_edge("backend", "supervisor")
    workflow.add_edge("frontend", "supervisor")
    workflow.add_edge("qa_agent", "run_tests")
    
    return workflow.compile()
