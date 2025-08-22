"""Pydantic v2 schemas for the batch publisher URL resolution endpoint."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ArticleResolveURLRequest(BaseModel):
    """Request body for ``POST /api/v1/articles/resolve-url``."""

    article_ids: list[int] = Field(
        ...,
        min_length=1,
        description="Article IDs whose Google News URLs should be resolved.",
    )


class ArticleResolveItemResult(BaseModel):
    """Per-article URL resolution outcome."""

    article_id: int
    status: Literal["SUCCESS", "FAILED"]
    resolved_url: str | None = None
    error: str | None = None


class ArticleResolveURLResponse(BaseModel):
    """Aggregated result for a batch URL resolution request."""

    processed_count: int
    success_count: int
    failed_count: int
    results: list[ArticleResolveItemResult]