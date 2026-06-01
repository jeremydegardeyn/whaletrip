import httpx
import structlog
from fastapi import APIRouter, HTTPException
from app.config import get_settings
from app.models.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])
logger = structlog.get_logger()
settings = get_settings()


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Proxy chat messages to the ADK agent service."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{settings.agents_url}/chat",
                json=req.model_dump(),
            )
            resp.raise_for_status()
            return ChatResponse(**resp.json())
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Agent service timed out")
        except httpx.HTTPStatusError as e:
            logger.error("agent_error", status=e.response.status_code, body=e.response.text)
            raise HTTPException(status_code=502, detail="Agent service error")


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.delete(f"{settings.agents_url}/session/{session_id}")
            resp.raise_for_status()
            return {"cleared": True}
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=502, detail="Could not clear session")
