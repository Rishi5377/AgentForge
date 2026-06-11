from agents.base import BaseAgent
from llm.llm_client import get_database_model

class DatabaseAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role='Senior Database Architect',
            goal='Design optimal SQLite database schemas and queries based on the project requirements.',
            prompt_file='database.txt',
            llm=get_database_model()
        )

    async def execute(self, db_tasks: str, complexity: str, features: list, existing_codebase: str = "", stream_callback=None) -> str:
        if complexity == "EASY":
            return "{ \"agent\": \"database\", \"status\": \"skipped\", \"reason\": \"No database required for EASY complexity\" }"
            
        existing_code_str = f"EXISTING CODEBASE:\n{existing_codebase}\n\n" if existing_codebase else ""

        chain = self.create_chain(
            "{existing_code_str}"
            "Task: {db_tasks}\n"
            "Complexity: {complexity}\n"
            "Features: {features}\n\n"
            "Design the SQLite schema and return a valid SQL migration file and ORM models."
        )
        
        full_response = ""
        async for chunk in chain.astream({
            "existing_code_str": existing_code_str,
            "db_tasks": db_tasks,
            "complexity": complexity,
            "features": features
        }):
            content_str = self.extract_content(chunk)
            if stream_callback and content_str:
                await stream_callback("database", content_str)
            full_response += content_str
            
        return full_response
