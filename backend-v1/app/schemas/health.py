"""Pydantic response schema for the ``GET /api/v1/health`` endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Operational status payload returned by the health probe.

    Attributes:
        status: Overall application status (``"ok"`` when serving).
        database: Database connectivity status (``"ok"`` when reachable).
        timestamp: Current server time as an ISO 8601 UTC string.
    """

    status: str = Field(..., description="Overall application status.")
    database: str = Field(..., description="Database connectivity status.")
    timestamp: str = Field(
        ..., description="ISO 8601 UTC timestamp of the health probe."
    )