from typing import Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "anonymous"
    context: Optional[dict] = None  # e.g. current map viewport, active filters


class ChatResponse(BaseModel):
    session_id: str
    message: str
    agent: Optional[str] = None       # which sub-agent handled the response
    map_actions: Optional[list] = None  # [{action: "filter", params: {...}}]
    recommendations: Optional[list] = None
    follow_up_questions: Optional[list[str]] = None
