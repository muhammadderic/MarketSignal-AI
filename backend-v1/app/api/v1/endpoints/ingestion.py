"""``POST /api/v1/ingest`` controller.

Thin HTTP adapter: validates payload, delegates to
:class:`IngestionService`, returns the response DTO. Domain errors propagate
to the global ``AppError`` handler (mapped to the contract's status codes).
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.db.repositories.article_repository import ArticleRepository
from app.schemas.ingestion import ArticleIngestRequest, ArticleIngestResponse
from app.services.ingestion import IngestionService

router = APIRouter(tags=["ingestion"])


def _get_ingestion_service() -> IngestionService:
    """FastAPI dependency provider for :class:`IngestionService`."""
    return IngestionService(article_repository=ArticleRepository())


@router.post(
    "/ingest",
    response_model=ArticleIngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Google News RSS ingestion",
)
async def ingest_news(
    payload: ArticleIngestRequest | None = Body(default=None),
    db: AsyncSession = Depends(get_async_db),
    service: IngestionService = Depends(_get_ingestion_service),
) -> ArticleIngestResponse:
    """Fetch, parse, normalize, and persist new articles from an RSS feed.

    Args:
        payload: Optional ``{"feed_url": "..."}`` override. An absent/empty
            body is treated as "use configured default".
        db: Async SQLite session (committed by the dependency on success).
        service: Injected ingestion domain service.

    Returns:
        ArticleIngestResponse with ingestion metrics.

    Raises:
        ExternalServiceError: Propagated to the global handler (HTTP 502).
    """
    feed_url_override = str(payload.feed_url) if payload and payload.feed_url else None
    return await service.ingest_google_news(db, feed_url_override=feed_url_override)