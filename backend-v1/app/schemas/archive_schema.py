"""Pydantic v2 schemas for the ``GET /api/v1/archive-counts`` endpoint.

Field names and JSON serialization mirror ``API_CONTRACTS.md``
§Endpoint: Get Calendar Archive Counts.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ArchiveCountItem(BaseModel):
    """A single calendar day aggregate.

    Attributes:
        date: Publication date in ``YYYY-MM-DD`` format (UTC).
        count: Number of articles published on ``date`` (>= 1; zero-count
            dates are omitted from responses per ``API_CONTRACTS.md``).
    """

    model_config = ConfigDict(extra="forbid")

    date: str = Field(
        ...,
        description="UTC publication date in YYYY-MM-DD format.",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    count: int = Field(
        ...,
        ge=1,
        description="Number of articles published on this date.",
    )


__all__ = ["ArchiveCountItem"]