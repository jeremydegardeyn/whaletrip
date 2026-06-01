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
    gcp_region: str = "us-central1"
    allowed_origins: str = "http://localhost:8000,http://localhost:3000"
    model_armor_template: str = "whaletrip-guardrails"
    port: int = 8001

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def armor_template_name(self) -> str | None:
        if not self.gcp_project_id:
            return None
        return (
            f"projects/{self.gcp_project_id}/locations/{self.gcp_region}"
            f"/templates/{self.model_armor_template}"
        )


settings = Settings()

# ── Model Armor client (optional — disabled if no project set) ─────────────────
_armor_client = None

def _get_armor_client():
    global _armor_client
    if _armor_client is None and settings.gcp_project_id:
        try:
            from google.cloud import modelarmor_v1
            from google.api_core.client_options import ClientOptions
            _armor_client = modelarmor_v1.ModelArmorClient(
                client_options=ClientOptions(
                    api_endpoint=f"modelarmor.{settings.gcp_region}.rep.googleapis.com"
                )
            )
        except Exception as e:
            logger.warning("model_armor_unavailable", error=str(e))
    return _armor_client


def _check_armor(text: str, screen_type: str) -> str | None:
    """
    Run text through Model Armor. Returns a block reason string if the content
    is flagged, or None if it passes. Fails open (returns None) on any error.
    """
    client = _get_armor_client()
    template = settings.armor_template_name
    if not client or not template:
        return None

    try:
        from google.cloud import modelarmor_v1
        if screen_type == "prompt":
            req = modelarmor_v1.SanitizeUserPromptRequest(
                name=template,
                user_prompt_data=modelarmor_v1.DataItem(text=text),
            )
            result = client.sanitize_user_prompt(request=req)
            decision = result.sanitization_result.filter_match_state
        else:
            req = modelarmor_v1.SanitizeModelResponseRequest(
                name=template,
                model_response_data=modelarmor_v1.DataItem(text=text),
            )
            result = client.sanitize_model_response(request=req)
            decision = result.sanitization_result.filter_match_state

        # MATCH_FOUND means it was flagged
        if decision == modelarmor_v1.FilterMatchState.MATCH_FOUND:
            matched = result.sanitization_result.filter_results
            reasons = [k for k, v in matched.items()
                       if hasattr(v, 'match_state') and
                       v.match_state == modelarmor_v1.FilterMatchState.MATCH_FOUND]
            logger.warning(
                "model_armor_blocked",
                screen_type=screen_type,
                reasons=reasons,
            )
            return ",".join(reasons) if reasons else "policy_violation"
    except Exception as e:
        logger.warning("model_armor_error", error=str(e), screen_type=screen_type)

    return None


# ── Session service ────────────────────────────────────────────────────────────
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
    armor_status = "enabled" if settings.armor_template_name else "disabled"
    logger.info("agent_service_started", model_armor=armor_status)
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
        # ── Model Armor: screen incoming prompt ────────────────────────────────
        block_reason = _check_armor(req.message, "prompt")
        if block_reason:
            logger.warning("prompt_blocked", session_id=session_id, reason=block_reason)
            return ChatResponse(
                session_id=session_id,
                message="I'm not able to respond to that. Let me know if I can help you plan a whale-watching trip.",
            )

        # ── Get or create session (ADK 1.x returns None if not found) ──────────
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

        # ── Model Armor: screen outgoing response ──────────────────────────────
        block_reason = _check_armor(full_response, "response")
        if block_reason:
            logger.warning("response_blocked", session_id=session_id, reason=block_reason)
            full_response = "I wasn't able to generate a safe response. Please try rephrasing your question."

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
    armor_active = _get_armor_client() is not None
    return {"status": "ok", "service": "whaletrip-agents", "model_armor": armor_active}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
