"""
Application configuration exposed to the frontend.
"""

from fastapi import APIRouter

from backend.core.config import get_settings

router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
async def get_app_config() -> dict[str, float | int]:
    """Return server-side defaults for optimization settings."""
    settings = get_settings()
    return {
        "hire_threshold": settings.hire_threshold,
        "gepa_max_metric_calls": settings.gepa_max_metric_calls,
        "early_stop_patience": settings.early_stop_patience,
    }
