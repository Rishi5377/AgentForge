from agents.base import BaseAgent
from llm.llm_client import get_assembler_model
import json
import re
import os

def clean_json_str(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace:last_brace+1]
    return text

def parse_agent_files_and_deps(agent_output: str):
    if not agent_output:
        return [], []
        
    files = []
    dependencies = []
    
    # 1. Parse XML Tags <agent-write path="...">...</agent-write>
    # The regex handles multiline content inside the tag.
    write_matches = re.finditer(r'<agent-write\s+path=["\']([^"\']+)["\']\s*>(.*?)</agent-write>', agent_output, re.DOTALL)
    for match in write_matches:
        path = match.group(1).strip()
        content = match.group(2).strip()
        files.append({"path": path, "content": content})
        
    # 2. Parse XML Tags <agent-deps>...</agent-deps>
    deps_matches = re.finditer(r'<agent-deps>\s*(.*?)\s*</agent-deps>', agent_output, re.DOTALL)
    for match in deps_matches:
        deps_str = match.group(1)
        # Split by spaces, commas, or newlines
        deps = [d.strip() for d in re.split(r'[\s,]+', deps_str) if d.strip()]
        dependencies.extend(deps)
        
    # 3. Fallback: Parse <agent-schema>...</agent-schema> for database
    schema_matches = re.finditer(r'<agent-schema>\s*(.*?)\s*</agent-schema>', agent_output, re.DOTALL)
    for match in schema_matches:
        schema_content = match.group(1).strip()
        # Mocking the path so it can be merged by the existing logic if needed
        files.append({"path": "db/schema.sql", "content": schema_content})
        
    # Fallback to old JSON parse if no XML tags found (for backward compatibility during migration)
    if not files and not dependencies:
        cleaned = clean_json_str(agent_output)
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                if "files" in data and isinstance(data["files"], list):
                    for f in data["files"]:
                        if isinstance(f, dict) and "path" in f and "content" in f:
                            files.append({"path": f["path"], "content": f["content"]})
                elif "files" in data and isinstance(data["files"], dict):
                    for p, c in data["files"].items():
                        files.append({"path": p, "content": c})
                if "dependencies" in data:
                    deps = data["dependencies"]
                    if isinstance(deps, list): dependencies.extend(deps)
                    elif isinstance(deps, dict): dependencies.extend(list(deps.keys()))
        except:
            pass

    return files, dependencies

class AssemblerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role='Integration Specialist',
            goal='Assemble all code pieces into a final cohesive markdown response.',
            prompt_file='assembler.txt',
            llm=get_assembler_model()
        )

    async def execute(self, db_code: str, backend_code: str, frontend_code: str, plan_json: str, session_id: str = "default", stream_callback=None) -> str:
        # Programmatic assembly attempt
        try:
            print("Attempting programmatic assembly of agent files...")
            files_map = {}
            all_deps = set([
                "react", "react-dom", "react-router-dom", "axios", 
                "express", "cors", "better-sqlite3", "bcrypt", 
                "jsonwebtoken", "concurrently", "lucide-react", "framer-motion",
                "@auth/prisma-adapter"
            ])
            
            # Extract database agent files
            db_files, _ = parse_agent_files_and_deps(db_code)
            for f in db_files:
                path = f["path"]
                if path.startswith("./"): path = path[2:]
                files_map[path] = f["content"]
                
            # Extract backend files and dependencies
            be_files, be_deps = parse_agent_files_and_deps(backend_code)
            for f in be_files:
                path = f["path"]
                if path.startswith("./"): path = path[2:]
                content = f["content"]
                if "server.js" in path or "app.js" in path or "main.py" in path:
                    content = content.replace("3000", "3001")
                    content = re.sub(r'port\s*=\s*3000', 'port = 3001', content, flags=re.IGNORECASE)
                    content = re.sub(r'listen\(3000', 'listen(3001', content)
                files_map[path] = content
            for d in be_deps: all_deps.add(d)
                
            # Extract frontend files and dependencies
            fe_files, fe_deps = parse_agent_files_and_deps(frontend_code)
            for f in fe_files:
                path = f["path"]
                if path.startswith("./"): path = path[2:]
                content = f["content"]
                
                # Check and append missing default export for capitalized React components
                basename = os.path.splitext(os.path.basename(path))[0]
                if basename and basename[0].isupper():
                    if "export default" not in content:
                        if f"function {basename}" in content or f"const {basename}" in content or f"class {basename}" in content:
                            content += f"\nexport default {basename};\n"
                            
                # Migrate ReactDOM.render to React 18 createRoot
                if "ReactDOM.render(" in content:
                    content = content.replace("import ReactDOM from 'react-dom';", "import { createRoot } from 'react-dom/client';")
                    content = content.replace('import ReactDOM from "react-dom";', 'import { createRoot } from "react-dom/client";')
                    content = content.replace("import ReactDOM from 'react-dom/client';", "import { createRoot } from 'react-dom/client';")
                    content = content.replace('import ReactDOM from "react-dom/client";', 'import { createRoot } from "react-dom/client";')
                    
                    match = re.search(r'ReactDOM\.render\(\s*(.*?)\s*,\s*document\.getElementById\(\'(.*?)\'\)\s*\);?', content, re.DOTALL)
                    if not match:
                        match = re.search(r'ReactDOM\.render\(\s*(.*?)\s*,\s*document\.getElementById\("(.*?)"\)\s*\);?', content, re.DOTALL)
                    if match:
                        element = match.group(1)
                        container_id = match.group(2)
                        replacement = f"createRoot(document.getElementById('{container_id}')).render({element});"
                        content = content.replace(match.group(0), replacement)
                            
                content = content.replace("http://localhost:3000/api", "/api")
                content = content.replace("http://localhost:3001/api", "/api")
                content = content.replace("http://127.0.0.1:3000/api", "/api")
                content = content.replace("http://127.0.0.1:3001/api", "/api")
                files_map[path] = content
            for d in fe_deps: all_deps.add(d)
            
            if len(files_map) > 0:
                print(f"Programmatic assembly succeeded with {len(files_map)} files.")
                
                workspace_dir = os.path.join(os.getcwd(), "workspace", f"app_{session_id}")
                
                if not os.path.exists(workspace_dir):
                    # Extract project_template from plan
                    try:
                        plan_data = json.loads(plan_json)
                        template_name = plan_data.get("project_template", "react-tailwind")
                    except Exception:
                        template_name = "react-tailwind"
                        
                    from utils.template_engine import TemplateEngine
                    engine = TemplateEngine(os.path.join(os.getcwd(), "templates"))
                    try:
                        engine.instantiate_template(template_name, workspace_dir, project_name=f"app_{session_id}")
                    except ValueError:
                        os.makedirs(workspace_dir, exist_ok=True)
                else:
                    os.makedirs(workspace_dir, exist_ok=True)
                
                def file_exists_in_workspace(filepath):
                    return os.path.exists(os.path.join(workspace_dir, filepath))
                if template_name == "react-tailwind":
                    default_dev_deps = {
                        "vite": "^4.4.5",
                        "@vitejs/plugin-react": "^4.0.3",
                        "tailwindcss": "^3.4.1",
                        "postcss": "^8.4.35",
                        "autoprefixer": "^10.4.18",
                        "concurrently": "^8.0.0"
                    }
                    
                    has_backend = any(f.endswith("server.js") or f.endswith("app.js") or f.endswith("main.py") for f in files_map.keys())
                    start_cmd = "concurrently \"node backend/server.js\" \"vite --port 5173 --host\"" if has_backend else "vite --port 5173 --host"
                    
                    default_scripts = {
                        "start": start_cmd,
                        "dev": "vite --port 5173 --host",
                        "build": "vite build"
                    }
                    
                    if "package.json" not in files_map and not file_exists_in_workspace("package.json"):
                        # Remove dev tools from all_deps so they don't get installed as 'latest'
                        deps_to_remove = {"tailwindcss", "postcss", "autoprefixer", "vite"}
                        filtered_deps = {d for d in all_deps if d not in deps_to_remove}
                        dependencies_dict = {dep: "latest" for dep in filtered_deps}
                        dependencies_dict["react"] = "^18.2.0"
                        dependencies_dict["react-dom"] = "^18.2.0"
                        package_json = {
                            "name": "agentforge-app",
                            "version": "1.0.0",
                            "scripts": default_scripts,
                            "dependencies": dependencies_dict,
                            "devDependencies": default_dev_deps
                        }
                        files_map["package.json"] = json.dumps(package_json, indent=2)
                    else:
                        # Merge dependencies into the existing package.json
                        try:
                            # Read either from files_map or from existing workspace file
                            if "package.json" in files_map:
                                pkg = json.loads(files_map["package.json"])
                            else:
                                with open(os.path.join(workspace_dir, "package.json"), "r") as f:
                                    pkg = json.loads(f.read())

                            if "devDependencies" not in pkg:
                                pkg["devDependencies"] = {}
                            if "dependencies" not in pkg:
                                pkg["dependencies"] = {}
                            if "scripts" not in pkg:
                                pkg["scripts"] = {}
                            
                            # Merge default scripts into existing
                            if "build" not in pkg["scripts"]:
                                pkg["scripts"]["build"] = "vite build"
                            if "dev" not in pkg["scripts"]:
                                pkg["scripts"]["dev"] = "vite --port 5173 --host"
                                
                            deps_to_remove = {"tailwindcss", "postcss", "autoprefixer", "vite"}
                            filtered_deps = {d for d in all_deps if d not in deps_to_remove}
                            for dep in filtered_deps:
                                if dep not in pkg["dependencies"] and dep not in pkg["devDependencies"]:
                                    pkg["dependencies"][dep] = "latest"
                            
                            # Remove dev tools from dependencies so they don't override devDependencies with 'latest'
                            for d in ["tailwindcss", "postcss", "autoprefixer", "vite", "@tailwindcss/postcss", "@tailwindcss/vite"]:
                                pkg["dependencies"].pop(d, None)


                                
                            files_map["package.json"] = json.dumps(pkg, indent=2)
                        except:
                            pass
                    
                    if "vite.config.js" not in files_map and "vite.config.ts" not in files_map and not file_exists_in_workspace("vite.config.js") and not file_exists_in_workspace("vite.config.ts"):
                        vite_config = (
                            "import { defineConfig } from 'vite';\n"
                            "import react from '@vitejs/plugin-react';\n\n"
                            "export default defineConfig({\n"
                            "  plugins: [react()],\n"
                            "  server: {\n"
                            "    port: 5173,\n"
                            "    host: true,\n"
                            "    proxy: {\n"
                            "      '/api': {\n"
                            "        target: 'http://localhost:3001',\n"
                            "        changeOrigin: true,\n"
                            "        secure: false\n"
                            "      }\n"
                            "    }\n"
                            "  }\n"
                            "});\n"
                        )
                        files_map["vite.config.js"] = vite_config
                        
                    if "tailwind.config.js" not in files_map and not file_exists_in_workspace("tailwind.config.js"):
                        tailwind_config = (
                            "module.exports = {\n"
                            "  content: [\n"
                            "    './index.html',\n"
                            "    './src/**/*.{js,ts,jsx,tsx}',\n"
                            "  ],\n"
                            "  theme: {\n"
                            "    extend: {},\n"
                            "  },\n"
                            "  plugins: [],\n"
                            "};\n"
                        )
                        files_map["tailwind.config.js"] = tailwind_config
                        
                    if "postcss.config.js" not in files_map and not file_exists_in_workspace("postcss.config.js"):
                        postcss_config = (
                            "module.exports = {\n"
                            "  plugins: {\n"
                            "    tailwindcss: {},\n"
                            "    autoprefixer: {},\n"
                            "  },\n"
                            "};\n"
                        )
                        files_map["postcss.config.js"] = postcss_config
                        
                    if "index.html" not in files_map and not file_exists_in_workspace("index.html"):
                        index_html = (
                            "<!DOCTYPE html>\n"
                            "<html lang='en'>\n"
                            "  <head>\n"
                            "    <meta charset='UTF-8' />\n"
                            "    <meta name='viewport' content='width=device-width, initial-scale=1.0' />\n"
                            "    <title>AgentForge App</title>\n"
                            "  </head>\n"
                            "  <body class='bg-gray-900 text-white'>\n"
                            "    <div id='root'></div>\n"
                            "    <script type='module' src='/src/main.jsx'></script>\n"
                            "  </body>\n"
                            "</html>\n"
                        )
                        files_map["index.html"] = index_html
                        
                    if "src/main.jsx" not in files_map and "src/main.js" not in files_map and not file_exists_in_workspace("src/main.jsx") and not file_exists_in_workspace("src/main.js"):
                        main_jsx = (
                            "import React from 'react';\n"
                            "import { createRoot } from 'react-dom/client';\n"
                            "import App from './App.jsx';\n"
                            "import './index.css';\n\n"
                            "createRoot(document.getElementById('root')).render(\n"
                            "  <React.StrictMode>\n"
                            "    <App />\n"
                            "  </React.StrictMode>\n"
                            ");\n"
                        )
                        files_map["src/main.jsx"] = main_jsx
                        
                    if "src/index.css" not in files_map and not file_exists_in_workspace("src/index.css"):
                        index_css = (
                            "@tailwind base;\n"
                            "@tailwind components;\n"
                            "@tailwind utilities;\n"
                        )
                        files_map["src/index.css"] = index_css
                
                # Write files to local workspace
                for file_path, content in files_map.items():
                    full_path = os.path.join(workspace_dir, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # Remove markdown code blocks if the LLM wrapped the content
                    if content.startswith("```"):
                        content = "\n".join(content.split("\n")[1:])
                        if content.endswith("```"):
                            content = content[:-3].strip()
                        elif content.endswith("```\n"):
                            content = content[:-4].strip()

                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                return json.dumps({"workspace_dir": workspace_dir})
        except Exception as prog_err:
            print(f"Programmatic assembly failed: {prog_err}. Falling back to LLM assembly.")

        # Fallback to LLM assembly
        chain = self.create_chain(
            "Execution Plan:\n{plan_json}\n\n"
            "Database Output:\n{db_code}\n\n"
            "Backend Output:\n{backend_code}\n\n"
            "Frontend Output:\n{frontend_code}\n\n"
            "Output ONLY the final merged codebase using <agent-write> tags. Do not include extra text, explanations, or wrappers."
        )
        
        full_response = ""
        async for chunk in chain.astream({
            "db_code": db_code,
            "backend_code": backend_code,
            "frontend_code": frontend_code,
            "plan_json": plan_json
        }):
            content_str = self.extract_content(chunk)
            if stream_callback and content_str:
                await stream_callback("assembler", content_str)
            full_response += content_str
        
        try:
            llm_files, _ = parse_agent_files_and_deps(full_response)
            workspace_dir = os.path.join(os.getcwd(), "workspace", f"app_{session_id}")
            
            if not os.path.exists(workspace_dir):
                try:
                    plan_data = json.loads(plan_json)
                    template_name = plan_data.get("project_template", "react-tailwind")
                except Exception:
                    template_name = "react-tailwind"
                    
                from utils.template_engine import TemplateEngine
                engine = TemplateEngine(os.path.join(os.getcwd(), "templates"))
                try:
                    engine.instantiate_template(template_name, workspace_dir, project_name=f"app_{session_id}")
                except ValueError:
                    os.makedirs(workspace_dir, exist_ok=True)
            else:
                os.makedirs(workspace_dir, exist_ok=True)
            
            for f in llm_files:
                file_path = f["path"]
                content = f["content"]
                
                full_path = os.path.join(workspace_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Remove markdown code blocks if the LLM wrapped the content
                if content.startswith("```"):
                    content = "\n".join(content.split("\n")[1:])
                    if content.endswith("```"):
                        content = content[:-3].strip()
                    elif content.endswith("```\n"):
                        content = content[:-4].strip()

                with open(full_path, 'w', encoding='utf-8') as fh:
                    fh.write(content)
                    
            return json.dumps({"workspace_dir": workspace_dir})
        except Exception as llm_err:
            print(f"LLM assembly fallback failed: {llm_err}")
            return json.dumps({"error": "Failed to assemble files.", "raw_output": response.content})
