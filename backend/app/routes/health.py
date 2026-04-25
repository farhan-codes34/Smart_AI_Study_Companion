"""
health.py — Simple liveness check route

Why have a /health endpoint?
  It lets you confirm the server is running before testing
  anything else. Also useful for future deployment health checks.
"""

from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Returns server status. Use this to verify the API is alive."""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        message="Smart AI Study Companion API is running.",
    )
