import os
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage

class BaseAgent:
    def __init__(self, role: str, goal: str, prompt_file: str, llm=None):
        self.role = role
        self.goal = goal
        self.system_prompt = self._load_prompt(prompt_file)
        self.llm = llm

    def _load_prompt(self, filename: str) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', filename)
        if not os.path.exists(prompt_path):
            return f"You are a {self.role}. {self.goal}"
        with open(prompt_path, 'r') as f:
            return f.read()

    def create_chain(self, human_message_template: str):
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessagePromptTemplate.from_template(human_message_template)
        ])
        return prompt | self.llm

    def extract_content(self, response) -> str:
        content = response.content
        if isinstance(content, list):
            # Gemini models sometimes return a list of content blocks
            text_parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    text_parts.append(part["text"])
                elif isinstance(part, str):
                    text_parts.append(part)
                else:
                    text_parts.append(str(part))
            return "".join(text_parts)
        return str(content)
