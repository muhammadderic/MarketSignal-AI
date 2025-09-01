"""Article metadata list endpoint.

Exposes ``GET /api/v1/articles`` as defined in ``API_CONTRACTS.md``
§Endpoint: List Articles. The controller validates query parameters, delegates
to :class:`ArticleRepository`, and serializes the paginated envelope. Heavy text
columns are excluded from the payload.
"""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_handlers import BadRequestError, NotFoundError
from app.db.database import get_async_db
from app.db.models import WorkflowState
from app.db.repositories.article_repository import ArticleRepository
from app.schemas.article import (
    ArticleContentUpdate,
    ArticleContentUpdateResponse,
    ArticleListResponse,
    ArticleSummaryResponse,
)

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


@router.put(
    "/articles/{article_id}/content",
    response_model=ArticleContentUpdateResponse,
    summary="Overwrite scraped article content and recover workflow state",
)
async def update_article_content(
    payload: ArticleContentUpdate,
    article_id: int = Path(
        ...,
        ge=1,
        description="Target article primary key ID.",
    ),
    db: AsyncSession = Depends(get_async_db),
    repository: ArticleRepository = Depends(get_article_repository),
) -> ArticleContentUpdateResponse:
    """Persist manually edited ``scraped_content`` for a single article.

    Behavior (``API_CONTRACTS.md`` §Update Scraped Article Content, FEAT-007):

    * ``scraped_content`` is overwritten with the provided text.
    * ``scraping_status`` is set to ``SUCCESS`` and ``scraping_error`` cleared,
      allowing downstream extraction to proceed (BR-010, R-001).
    * ``workflow_state`` is advanced to ``Scraped``.
    * ``scraped_at`` is set when previously ``null``; otherwise preserved.
    * ``updated_at`` is refreshed.

    Args:
        payload: Request body with the new ``scraped_content`` text.
        article_id: Target article ID (path parameter).
        db: Injected async database session.
        repository: Injected article repository.

    Returns:
        :class:`ArticleContentUpdateResponse` with the persisted values.

    Raises:
        BadRequestError: When ``scraped_content`` is empty or whitespace-only
            (HTTP 400, R-002).
        NotFoundError: When ``article_id`` does not exist (HTTP 404).
    """
    if not payload.scraped_content.strip():
        raise BadRequestError(
            "scraped_content must be a non-empty, non-whitespace string.",
            context={"field": "scraped_content"},
        )

    article = await repository.update_scraped_content(
        db,
        article_id=article_id,
        content=payload.scraped_content,
    )
    if article is None:
        raise NotFoundError(
            f"Article ID {article_id} not found.",
            context={"article_id": article_id},
        )

    logger.info(
        "Scraped content updated manually: article_id=%d length=%d",
        article.id,
        len(payload.scraped_content),
    )
    return ArticleContentUpdateResponse.model_validate(article)