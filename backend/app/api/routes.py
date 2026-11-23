"""HTTP API route definitions."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.stats import DatabaseStatsResponse, HealthResponse
from app.services.stats import get_database_stats

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Liveness / readiness style health check."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.app_env,
    )


@router.get(
    "/api/v1/database/stats",
    response_model=DatabaseStatsResponse,
    tags=["database"],
)
def database_stats(db: Session = Depends(get_db)) -> DatabaseStatsResponse:
    """Return record counts for all tables."""
    return get_database_stats(db)
