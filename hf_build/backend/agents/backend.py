from agents.base import BaseAgent
from llm.llm_client import get_backend_model

class BackendAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role='Senior Backend Node.js Engineer',
            goal='Develop robust Express.js/Node.js backend services based on database schemas and project requirements.',
            prompt_file='backend.txt',
            llm=get_backend_model()
        )

    async def execute(self, db_code: str, backend_tasks: str, complexity: str, features: list, existing_codebase: str = "", validation_error: str = None, project_template: str = "react-tailwind", stream_callback=None) -> str:
        if complexity == "EASY":
            return "{ \"agent\": \"backend\", \"status\": \"skipped\", \"reason\": \"No backend required for EASY complexity\" }"
            
        existing_code_str = f"EXISTING CODEBASE:\n{existing_codebase}\n\n" if existing_codebase else ""
        
        import os
        framework_rules = ""
        framework_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'frameworks', f"{project_template}_backend.txt")
        if os.path.exists(framework_path):
            with open(framework_path, 'r') as f:
                framework_rules = f.read()
        
        prompt_template = (
            "Database Schema / Code (if any):\n{db_code}\n\n"
            "{existing_code_str}"
            "Task: {backend_tasks}\n"
            "Complexity: {complexity}\n"
            "Features: {features}\n"
            "Project Template: {project_template}\n\n"
            f"{framework_rules}\n\n"
            "{validation_error_str}"
            "Implement the backend APIs/logic.\n"
            "If 'EXISTING CODEBASE' is provided, ONLY return files that you have created or modified. Omit files that do not need changes."
        )
            
        chain = self.create_chain(prompt_template)
        
        val_str = f"\nURGENT LINTER ERROR FROM PREVIOUS ATTEMPT:\n{validation_error}\n\n" if validation_error else ""
        
        full_response = ""
        async for chunk in chain.astream({
            "db_code": db_code,
            "existing_code_str": existing_code_str,
            "backend_tasks": backend_tasks,
            "complexity": complexity,
            "features": features,
            "project_template": project_template,
            "validation_error_str": val_str
        }):
            content_str = self.extract_content(chunk)
            if stream_callback and content_str:
                await stream_callback("backend", content_str)
            full_response += content_str
            
        return full_response
