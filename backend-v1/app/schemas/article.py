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


class ArticleDetailResponse(BaseModel):
    """Full article detail for ``GET /api/v1/articles/{id}``.

    Includes heavy text columns (``scraped_content``, ``financial_insight``)
    which are excluded from :class:`ArticleSummaryResponse` per
    ``API_CONTRACTS.md`` §Get Article Detail.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_name: str | None
    published_at: datetime
    published_at_date: date
    google_url: str
    resolved_url: str | None
    url_hash: str
    relevance_score: int | None
    relevance_reasoning: str | None
    scraped_content: str | None
    scraping_status: ScrapingStatus
    scraping_error: str | None
    financial_insight: str | None
    workflow_state: WorkflowState
    created_at: datetime
    updated_at: datetime
    scraped_at: datetime | None
    insight_extracted_at: datetime | None


class ArticleContentUpdate(BaseModel):
    """Request body for ``PUT /api/v1/articles/{id}/content``.

    ``scraped_content`` must be a non-empty string; whitespace-only input is
    rejected by the endpoint (R-002). Field-level validation is intentionally
    minimal to keep the HTTP 400 error contract consistent with other
    endpoints (e.g. ``resolver`` empty-``article_ids`` handling).
    """

    scraped_content: str = Field(
        ...,
        description="User-edited plain-text article body content.",
    )


class ArticleContentUpdateResponse(BaseModel):
    """Response for ``PUT /api/v1/articles/{id}/content``.

    Mirrors the payload shape in ``API_CONTRACTS.md`` §Update Scraped Article
    Content.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    scraped_content: str
    scraping_status: ScrapingStatus
    workflow_state: WorkflowState
    updated_at: datetime