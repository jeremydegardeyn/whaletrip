from fastapi import APIRouter
from app.config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
async def health():
    return {"status": "ok", "project": settings.gcp_project_id}


@router.get("/")
async def root():
    return {"service": "whaletrip-api", "version": "1.0.0"}
