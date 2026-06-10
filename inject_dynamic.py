import re

file_path = r"c:\Users\lenovo\Downloads\AgentForge\backend\workflows\pipeline.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We want to find the definition of create_dual_shot_agent down to its return statement.
# And we also want to insert create_dynamic_backend_agent right before it.

dynamic_backend_code = """
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
            context_str = "\\n\\n### EXISTING FILE CONTENTS FOR EDITING ###\\n"
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
                        context_str += f"\\n--- package.json ---\\n{f.read()}\\n"
                except Exception:
                    pass
            
            struct_path = os.path.join(workspace_dir, "project_structure.md")
            if os.path.exists(struct_path):
                try:
                    with open(struct_path, "r", encoding="utf-8") as f:
                        context_str += f"\\n### PROJECT STRUCTURE ###\\n{f.read()}\\n"
                except Exception:
                    pass
            
            for root, dirs, files in os.walk(workspace_dir):
                dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", "build", ".vite", ".next", ".swc", "public"]]
                for f in files:
                    if f.endswith(('.js', '.jsx', '.ts', '.tsx', '.css', '.html', '.sql', '.md')):
                        rel_path = os.path.relpath(os.path.join(root, f), workspace_dir).replace('\\\\', '/')
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
                                context_str += f"\\n--- {rel_path} ---\\n{content}\\n"
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
            if parsed_files and workspace_dir:
                for file_edit in parsed_files:
                    apply_file_edit(workspace_dir, file_edit)
            from langchain_core.messages import AIMessage
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
            if parsed_1 and workspace_dir:
                for file_edit in parsed_1:
                    apply_file_edit(workspace_dir, file_edit)
                    phase1_summaries.append(f"--- {file_edit.filepath} ---\\n{file_edit.content}\\n")
            
            print("[BACKEND] Sleeping to respect RPM limit...")
            await asyncio.sleep(6)
            
            print("[BACKEND] Running Phase 2 (API Routes)...")
            phase2_context = "\\n\\n### PHASE 1 OUTPUT ###\\n" + "".join(phase1_summaries)
            msg_2 = [
                SystemMessage(content=system_prompt + context_str + phase2_context),
                HumanMessage(content="Phase 2: Now implement the actual API routes and controllers that use the models from Phase 1. Use the <file> XML tags.")
            ]
            res_2 = await invoke_with_retry(msg_2)
            parsed_2 = extract_xml_files(res_2.content) if res_2 else []
            if parsed_2 and workspace_dir:
                for file_edit in parsed_2:
                    apply_file_edit(workspace_dir, file_edit)
            
            from langchain_core.messages import AIMessage
            return {"messages": [AIMessage(content=f"Wrote {len(parsed_1)+len(parsed_2)} backend files over 2 phases.")]}
    return agent_node
"""

dynamic_frontend_code = """
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
            context_str = "\\n\\n### EXISTING FILE CONTENTS FOR EDITING ###\\n"
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
                        context_str += f"\\n--- package.json ---\\n{f.read()}\\n"
                except Exception:
                    pass
            
            struct_path = os.path.join(workspace_dir, "project_structure.md")
            if os.path.exists(struct_path):
                try:
                    with open(struct_path, "r", encoding="utf-8") as f:
                        context_str += f"\\n### PROJECT STRUCTURE ###\\n{f.read()}\\n"
                except Exception:
                    pass
            
            for root, dirs, files in os.walk(workspace_dir):
                dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", "build", ".vite", ".next", ".swc", "public"]]
                for f in files:
                    if f.endswith(('.js', '.jsx', '.ts', '.tsx', '.css', '.html', '.sql', '.md')):
                        rel_path = os.path.relpath(os.path.join(root, f), workspace_dir).replace('\\\\', '/')
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
                                context_str += f"\\n--- {rel_path} ---\\n{content}\\n"
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
            if parsed_files and workspace_dir:
                for file_edit in parsed_files:
                    apply_file_edit(workspace_dir, file_edit)
            from langchain_core.messages import AIMessage
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
            if parsed_1 and workspace_dir:
                for file_edit in parsed_1:
                    apply_file_edit(workspace_dir, file_edit)
                    phase1_summaries.append(f"--- {file_edit.filepath} ---\\n{file_edit.content}\\n")
            
            print("[FRONTEND] Sleeping to respect RPM limit...")
            await asyncio.sleep(6)
            
            print("[FRONTEND] Running Phase 2 (Route Pages)...")
            phase2_context = "\\n\\n### PHASE 1 OUTPUT ###\\n" + "".join(phase1_summaries)
            msg_2 = [
                SystemMessage(content=system_prompt + context_str + phase2_context),
                HumanMessage(content="Phase 2: Now implement the actual application route pages. Use the <file> XML tags.")
            ]
            res_2 = await invoke_with_retry(msg_2)
            parsed_2 = extract_xml_files(res_2.content) if res_2 else []
            if parsed_2 and workspace_dir:
                for file_edit in parsed_2:
                    apply_file_edit(workspace_dir, file_edit)
                    
            from langchain_core.messages import AIMessage
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
            if parsed_1 and workspace_dir:
                for file_edit in parsed_1:
                    apply_file_edit(workspace_dir, file_edit)
                    phase1_summaries.append(f"--- {file_edit.filepath} ---\\n{file_edit.content}\\n")
            
            print("[FRONTEND] Sleeping to respect RPM limit...")
            await asyncio.sleep(6)
            
            print("[FRONTEND] Running Phase 2 (Reusable Components)...")
            phase2_context = "\\n\\n### PHASE 1 OUTPUT ###\\n" + "".join(phase1_summaries)
            msg_2 = [
                SystemMessage(content=system_prompt + context_str + phase2_context),
                HumanMessage(content="Phase 2: Now implement generic reusable UI components (cards, buttons, inputs). DO NOT write the main pages yet. Use the <file> XML tags.")
            ]
            res_2 = await invoke_with_retry(msg_2)
            parsed_2 = extract_xml_files(res_2.content) if res_2 else []
            phase2_summaries = []
            if parsed_2 and workspace_dir:
                for file_edit in parsed_2:
                    apply_file_edit(workspace_dir, file_edit)
                    phase2_summaries.append(f"--- {file_edit.filepath} ---\\n{file_edit.content}\\n")
            
            print("[FRONTEND] Sleeping to respect RPM limit...")
            await asyncio.sleep(6)
            
            print("[FRONTEND] Running Phase 3 (Route Pages)...")
            phase3_context = phase2_context + "\\n\\n### PHASE 2 OUTPUT ###\\n" + "".join(phase2_summaries)
            msg_3 = [
                SystemMessage(content=system_prompt + context_str + phase3_context),
                HumanMessage(content="Phase 3: Now implement the actual application route pages and hook them up. Use the <file> XML tags.")
            ]
            res_3 = await invoke_with_retry(msg_3)
            parsed_3 = extract_xml_files(res_3.content) if res_3 else []
            if parsed_3 and workspace_dir:
                for file_edit in parsed_3:
                    apply_file_edit(workspace_dir, file_edit)
                    
            from langchain_core.messages import AIMessage
            return {"messages": [AIMessage(content=f"Wrote {len(parsed_1)+len(parsed_2)+len(parsed_3)} frontend files over 3 phases.")]}
    return agent_node
"""

# Regex to find create_dual_shot_agent block
pattern = r"def create_dual_shot_agent\(model, prompt_func\):.*?(?=\ndef create_pipeline)"
match = re.search(pattern, content, re.DOTALL)

if match:
    new_content = content[:match.start()] + dynamic_backend_code + "\n" + dynamic_frontend_code + "\n" + content[match.end():]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully replaced agent definitions.")
else:
    print("Could not find create_dual_shot_agent.")
