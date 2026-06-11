from pydantic import BaseModel
from typing import Optional, Any, Dict, List

class AgentEvent(BaseModel):
    type: str = "agent_event"
    agent: str
    status: str
    data: Dict[str, Any]
    timestamp: str

class UserPrompt(BaseModel):
    prompt: str

class FeedbackMessage(BaseModel):
    feedback: str

class FileOutput(BaseModel):
    filename: str
    content: str
