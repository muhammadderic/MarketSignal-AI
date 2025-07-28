"""Pydantic v2 response schemas for the article list endpoint.

Defines the lightweight ``ArticleSummaryResponse`` (heavy text columns excluded)
and the paginated ``ArticleListResponse`` envelope specified in
``API_CONTRACTS.md`` §Endpoint: List Articles.
"""

from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ScrapingStatus, WorkflowState


class ArticleSummaryResponse(BaseModel):
    """Lightweight article metadata (excludes ``scraped_content``/``financial_insight``)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_name: str | None
    published_at: datetime
    published_at_date: date
    google_url: str
    resolved_url: str | None
    relevance_score: int | None
    relevance_reasoning: str | None
    scraping_status: ScrapingStatus
    workflow_state: WorkflowState
    created_at: datetime
    updated_at: datetime


class ArticleListResponse(BaseModel):
    """Paginated envelope for ``GET /api/v1/articles``."""

    total: int = Field(..., ge=0, description="Total matching records.")
    limit: int = Field(..., ge=1, description="Applied page size.")
    offset: int = Field(..., ge=0, description="Applied pagination offset.")
    items: list[ArticleSummaryResponse]