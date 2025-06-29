"""Uniform error response schema used by all global exception handlers."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class APIErrorResponse(BaseModel):
    """Standard error envelope.

    Attributes:
        detail: Human-readable description, or a list of validation errors.
        error_code: Stable machine-readable code (e.g. ``"NOT_FOUND"``).
        timestamp: ISO 8601 UTC timestamp of the error.
        context: Optional structured payload (e.g. request_id, path, method).
    """

    detail: str | list[Any] = Field(
        ..., description="Human-readable error description."
    )
    error_code: str | None = Field(
        default=None, description="Stable machine-readable error code."
    )
    timestamp: str | None = Field(
        default=None, description="ISO 8601 UTC timestamp."
    )
    context: dict[str, Any] | None = Field(
        default=None, description="Optional structured error context."
    )