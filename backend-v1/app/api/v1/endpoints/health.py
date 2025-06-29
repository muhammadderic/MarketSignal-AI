"""Health check endpoint verifying application and database readiness."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_handlers import ServiceUnavailableError
from app.db.database import get_async_db
from app.schemas.health import HealthCheckResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Application and database health probe",
    tags=["Health"],
)
async def health_check(
    db: AsyncSession = Depends(get_async_db),
) -> HealthCheckResponse:
    """Return application status plus a database connectivity check.

    Executes ``SELECT 1`` through the injected async session. On DB failure
    raises :class:`ServiceUnavailableError` so the global handler returns a
    contract-compliant ``503`` envelope (AC-003).

    Args:
        db: Async database session dependency.

    Returns:
        :class:`HealthCheckResponse` with status, database, and UTC timestamp.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - surface all DB failures uniformly
        logger.error("Health check database probe failed: %s", exc)
        raise ServiceUnavailableError(
            "Database connectivity check failed.",
            context={"probe": "SELECT 1"},
        ) from exc

    return HealthCheckResponse(status="ok", database="ok", timestamp=timestamp)