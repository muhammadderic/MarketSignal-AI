"""``POST /api/v1/articles/resolve-url`` endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_handlers import BadRequestError
from app.db.database import get_async_db
from app.db.repositories.article_repository import ArticleRepository
from app.schemas.resolver import (
    ArticleResolveURLRequest,
    ArticleResolveURLResponse,
)
from app.services.resolver import ResolverService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles", tags=["articles"])


def _get_resolver_service() -> ResolverService:
    """Dependency provider for :class:`ResolverService`."""
    return ResolverService(ArticleRepository())


@router.post(
    "/resolve-url",
    response_model=ArticleResolveURLResponse,
    summary="Decode Google News URLs to publisher URLs",
)
async def resolve_urls(
    payload: ArticleResolveURLRequest,
    db: AsyncSession = Depends(get_async_db),
    service: ResolverService = Depends(_get_resolver_service),
) -> ArticleResolveURLResponse:
    """Decode each requested article's ``google_url`` to its publisher URL.

    Per-article failures are isolated in the response payload. An empty
    ``article_ids`` list produces HTTP 400 (``BAD_REQUEST``). Unexpected
    database errors propagate to the global handler (HTTP 500).
    """
    if not payload.article_ids:
        raise BadRequestError(
            "article_ids must contain at least one article ID.",
            context={"field": "article_ids"},
        )
    return await service.resolve_article_urls_batch(db, payload.article_ids)