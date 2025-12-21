"""
Health check endpoints.
"""

from fastapi import APIRouter

from config import get_settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with configuration info."""
    settings = get_settings()
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "version": "1.0.0",
        "sc_model": settings.sc_model,
        "qa_model": settings.qa_model,
        "temperatures": settings.temperatures,
    }
