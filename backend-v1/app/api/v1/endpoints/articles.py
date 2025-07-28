"""Article metadata list endpoint.

Exposes ``GET /api/v1/articles`` as defined in ``API_CONTRACTS.md``
§Endpoint: List Articles. The controller validates query parameters, delegates
to :class:`ArticleRepository`, and serializes the paginated envelope. Heavy text
columns are excluded from the payload.
"""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.db.models import WorkflowState
from app.db.repositories.article_repository import ArticleRepository
from app.schemas.article_schema import ArticleListResponse, ArticleSummaryResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["articles"])

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


def get_article_repository() -> ArticleRepository:
    """Provide an :class:`ArticleRepository` instance."""
    return ArticleRepository()


@router.get(
    "/articles",
    response_model=ArticleListResponse,
    summary="List article metadata with optional date/state filters",
)
async def list_articles(
    published_date: date | None = Query(
        default=None,
        alias="date",
        description="Filter by UTC publication date (YYYY-MM-DD).",
    ),
    workflow_state: WorkflowState | None = Query(
        default=None,
        description="Filter by lifecycle workflow state.",
    ),
    limit: int = Query(
        default=DEFAULT_LIMIT,
        ge=1,
        le=MAX_LIMIT,
        description="Maximum number of records to return.",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Pagination offset index.",
    ),
    db: AsyncSession = Depends(get_async_db),
    repository: ArticleRepository = Depends(get_article_repository),
) -> ArticleListResponse:
    """Return a paginated, date-filtered list of article metadata.

    Args:
        published_date: Optional UTC publication date (query alias ``date``).
        workflow_state: Optional lifecycle state filter.
        limit: Page size (1–200).
        offset: Pagination offset.
        db: Injected async database session.
        repository: Injected article repository.

    Returns:
        :class:`ArticleListResponse` with ``total``, ``limit``, ``offset``, and
        metadata ``items`` ordered by ``published_at`` descending.
    """
    items, total = await repository.list_articles(
        db,
        published_date=published_date,
        workflow_state=workflow_state,
        limit=limit,
        offset=offset,
    )
    logger.info(
        "Article list: date=%s state=%s limit=%d offset=%d total=%d",
        published_date,
        workflow_state,
        limit,
        offset,
        total,
    )
    return ArticleListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[ArticleSummaryResponse.model_validate(item) for item in items],
    )