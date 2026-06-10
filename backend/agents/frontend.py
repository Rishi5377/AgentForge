from agents.base import BaseAgent
from llm.llm_client import get_frontend_model

class FrontendAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role='Senior React Developer',
            goal='Build beautiful, responsive Next.js frontend interfaces connecting to backend APIs.',
            prompt_file='frontend.txt',
            llm=get_frontend_model()
        )

    async def execute(self, backend_code: str, frontend_tasks: str, complexity: str, features: list, existing_codebase: str = "", validation_error: str = None, project_template: str = "react-tailwind", stream_callback=None) -> str:
        existing_code_str = f"EXISTING CODEBASE:\n{existing_codebase}\n\n" if existing_codebase else ""
        
        import os
        framework_rules = ""
        framework_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'frameworks', f"{project_template}.txt")
        if os.path.exists(framework_path):
            with open(framework_path, 'r') as f:
                framework_rules = f.read()
                
        prompt_template = (
            "Backend API Code / Endpoints (if any):\n{backend_code}\n\n"
            "{existing_code_str}"
            "Task: {frontend_tasks}\n"
            "Complexity: {complexity}\n"
            "Features: {features}\n"
            "Project Template: {project_template}\n\n"
            f"{framework_rules}\n\n"
            "{validation_error_str}"
            "Implement the frontend UI tasks.\n"
            "If 'EXISTING CODEBASE' is provided, ONLY return files that you have created or modified. Omit files that do not need changes."
        )
            
        chain = self.create_chain(prompt_template)
        
        val_str = f"\nURGENT LINTER ERROR FROM PREVIOUS ATTEMPT:\n{validation_error}\n\n" if validation_error else ""
        
        full_response = ""
        async for chunk in chain.astream({
            "backend_code": backend_code,
            "existing_code_str": existing_code_str,
            "frontend_tasks": frontend_tasks,
            "complexity": complexity,
            "features": features,
            "project_template": project_template,
            "validation_error_str": val_str
        }):
            content_str = self.extract_content(chunk)
            if stream_callback and content_str:
                await stream_callback("frontend", content_str)
            full_response += content_str
            
        return full_response
