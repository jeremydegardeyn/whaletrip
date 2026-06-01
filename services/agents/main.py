"""
WhaleTrip ADK Agent Service.

Runs as a FastAPI app on Cloud Run. Manages ADK sessions and exposes a /chat endpoint
that the API gateway proxies to.
"""
from __future__ import annotations

import re
import uuid
import structlog
from contextlib import asynccontextmanager

import google.cloud.logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from agents.coordinator import coordinator_agent

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    gcp_project_id: str = ""
    allowed_origins: str = "http://localhost:8000,http://localhost:3000"
    port: int = 8001

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


settings = Settings()

# Session service — swap for FirestoreSessionService in production for persistence
session_service = InMemorySessionService()
runner = Runner(
    agent=coordinator_agent,
    app_name="whaletrip",
    session_service=session_service,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.gcp_project_id:
        try:
            client = google.cloud.logging.Client(project=settings.gcp_project_id)
            client.setup_logging()
        except Exception:
            pass
    logger.info("agent_service_started", model="gemini-1.5-flash-001")
    yield


app = FastAPI(title="WhaleTrip Agent Service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    user_id: str = "anonymous"
    context: dict | None = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    agent: str | None = None
    map_actions: list | None = None
    recommendations: list | None = None
    follow_up_questions: list[str] | None = None


_MAP_ACTION_RE = re.compile(r"```map_action\s*(\{.*?\})\s*```", re.DOTALL)
_FOLLOW_UP_RE  = re.compile(r"(?:^|\n)[•\-]\s*(.*\?)\s*$", re.MULTILINE)


def _parse_response(text: str) -> tuple[str, list | None, list[str] | None]:
    """Extract map_action blocks and follow-up questions from agent text."""
    map_actions = None
    follow_ups = None

    action_matches = _MAP_ACTION_RE.findall(text)
    if action_matches:
        import json
        map_actions = []
        for m in action_matches:
            try:
                map_actions.append(json.loads(m))
            except json.JSONDecodeError:
                pass
        text = _MAP_ACTION_RE.sub("", text).strip()

    follow_up_matches = _FOLLOW_UP_RE.findall(text)
    if follow_up_matches:
        follow_ups = follow_up_matches[:3]

    return text, map_actions, follow_ups


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())

    try:
        # Get or create session (ADK 1.x returns None if not found, no exception)
        session = await session_service.get_session(
            app_name="whaletrip",
            user_id=req.user_id,
            session_id=session_id,
        )
        if session is None:
            session = await session_service.create_session(
                app_name="whaletrip",
                user_id=req.user_id,
                session_id=session_id,
                state=req.context or {},
            )

        message = Content(role="user", parts=[Part(text=req.message)])
        full_response = ""
        last_agent = None

        async for event in runner.run_async(
            user_id=req.user_id,
            session_id=session.id,
            new_message=message,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        full_response += part.text
            if hasattr(event, "author"):
                last_agent = event.author

        clean_text, map_actions, follow_ups = _parse_response(full_response)
        logger.info("chat_response", session_id=session_id, agent=last_agent, chars=len(clean_text))

        return ChatResponse(
            session_id=session_id,
            message=clean_text,
            agent=last_agent,
            map_actions=map_actions,
            follow_up_questions=follow_ups,
        )

    except Exception as e:
        logger.error("chat_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.delete("/session/{session_id}")
async def clear_session(session_id: str, user_id: str = "anonymous"):
    try:
        await session_service.delete_session(
            app_name="whaletrip",
            user_id=user_id,
            session_id=session_id,
        )
        return {"cleared": True}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "whaletrip-agents"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
