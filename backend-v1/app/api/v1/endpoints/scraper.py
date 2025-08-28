"""``POST /api/v1/articles/scrape`` endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_handlers import BadRequestError
from app.db.database import get_async_db
from app.db.repositories.article_repository import ArticleRepository
from app.schemas.scraper import (
    ArticleScrapeRequest,
    ArticleScrapeResponse,
)
from app.services.scraper import ScraperService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles", tags=["articles"])


def _get_scraper_service() -> ScraperService:
    """Dependency provider for :class:`ScraperService`."""
    return ScraperService(ArticleRepository())


@router.post(
    "/scrape",
    response_model=ArticleScrapeResponse,
    summary="Scrape article content from resolved publisher URLs",
)
async def scrape_articles(
    payload: ArticleScrapeRequest,
    db: AsyncSession = Depends(get_async_db),
    service: ScraperService = Depends(_get_scraper_service),
) -> ArticleScrapeResponse:
    """Fetch and clean article content from each ``resolved_url``.

    Preconditions:
        Every requested article must exist and have a non-null
        ``resolved_url``; otherwise HTTP 400 is returned before any network
        activity (R-001, AC-002). Per-item failures during fetching are
        isolated in the response payload (AC-004). Unexpected database
        errors propagate to the global handler (HTTP 500).
    """
    if not payload.article_ids:
        raise BadRequestError(
            "article_ids must contain at least one article ID.",
            context={"field": "article_ids"},
        )

    unique_ids = list(dict.fromkeys(payload.article_ids))
    articles = await service.article_repo.get_by_ids(db, unique_ids)
    articles_by_id = {a.id: a for a in articles}

    missing = [aid for aid in unique_ids if aid not in articles_by_id]
    unresolved = [
        aid
        for aid in unique_ids
        if aid in articles_by_id and not articles_by_id[aid].resolved_url
    ]
    if missing or unresolved:
        raise BadRequestError(
            "All articles must exist and have a resolved_url before scraping.",
            context={
                "missing_ids": missing,
                "unresolved_ids": unresolved,
            },
        )

    return await service.scrape_articles_batch(db, payload.article_ids)