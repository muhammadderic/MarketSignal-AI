"""Pydantic v2 schemas for the ``POST /api/v1/ingest`` endpoint.

Field names and JSON serialization mirror ``API_CONTRACTS.md``
§Endpoint: Ingest Financial News.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ArticleIngestRequest(BaseModel):
    """Optional request body for ``POST /api/v1/ingest``.

    Attributes:
        feed_url: When set, overrides ``settings.GOOGLE_NEWS_RSS_URL`` for this
            single request (R-006).
    """

    model_config = ConfigDict(extra="forbid")

    feed_url: HttpUrl | None = Field(
        default=None,
        description="Optional RSS feed URL override.",
    )


class ArticleIngestResponse(BaseModel):
    """Ingestion execution metrics returned to the caller.

    Attributes:
        status: Literal ``"success"`` (contract value).
        ingested_count: Rows newly inserted.
        duplicate_count: Rows skipped due to ``url_hash`` or composite
            ``(title, published_at_date)`` collisions.
        failed_count: Entries dropped during parse/validation.
        ingested_at: Completion timestamp (UTC, ISO-8601 with ``Z`` suffix via
            :class:`~fastapi.encoders.jsonable_encoder`).
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["success"] = "success"
    ingested_count: int = Field(ge=0)
    duplicate_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )


__all__ = ["ArticleIngestRequest", "ArticleIngestResponse"]