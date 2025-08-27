"""Pydantic v2 schemas for the batch article content scraping endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.db.models import ScrapingStatus


class ArticleScrapeRequest(BaseModel):
    """Request body for ``POST /api/v1/articles/scrape``."""

    article_ids: list[int] = Field(
        ...,
        min_length=1,
        description="Article IDs whose resolved publisher URLs should be scraped.",
    )


class ArticleScrapeResult(BaseModel):
    """Per-article scraping outcome."""

    article_id: int
    scraping_status: ScrapingStatus
    scraped_content_length: int | None = None
    error: str | None = None


class ArticleScrapeResponse(BaseModel):
    """Aggregated result for a batch scraping request."""

    processed_count: int
    success_count: int
    failed_count: int
    results: list[ArticleScrapeResult]