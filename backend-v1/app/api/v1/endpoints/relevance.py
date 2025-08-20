"""``POST /api/v1/articles/score-relevance`` endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.article_repository import ArticleRepository
from app.db.database import get_async_db
from app.schemas.relevance import (
    ArticleBatchScoreRequest,
    ArticleBatchScoreResponse,
)
from app.services.relevance import RelevanceScoringService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles", tags=["articles"])


def _get_relevance_service() -> RelevanceScoringService:
    """Dependency provider for the relevance scoring service."""
    return RelevanceScoringService(ArticleRepository())


@router.post(
    "/score-relevance",
    response_model=ArticleBatchScoreResponse,
    summary="Batch title relevance scoring via Groq",
)
async def score_relevance(
    payload: ArticleBatchScoreRequest,
    db: AsyncSession = Depends(get_async_db),
    service: RelevanceScoringService = Depends(_get_relevance_service),
) -> ArticleBatchScoreResponse:
    """Score article titles for financial relevance (1–5) using Groq.

    Per-article failures are isolated; batch-level Groq outages surface as
    ``503 Service Unavailable``.
    """
    return await service.score_article_batch(db, payload.article_ids)