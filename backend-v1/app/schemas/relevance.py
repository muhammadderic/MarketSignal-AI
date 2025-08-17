"""Pydantic v2 schemas for the batch title relevance scoring endpoint."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ArticleBatchScoreRequest(BaseModel):
    """Request body for ``POST /api/v1/articles/score-relevance``."""

    article_ids: list[int] = Field(
        ...,
        min_length=1,
        description="List of article IDs to score (1–5 integer relevance).",
    )


class ScoreItemResult(BaseModel):
    """Per-article scoring outcome reported back to the client."""

    article_id: int
    status: Literal["SUCCESS", "FAILED"]
    relevance_score: int | None = Field(default=None, ge=1, le=5)
    relevance_reasoning: str | None = None
    error: str | None = None


class ArticleBatchScoreResponse(BaseModel):
    """Aggregated result for a batch title relevance scoring request."""

    processed_count: int
    success_count: int
    failed_count: int
    results: list[ScoreItemResult]