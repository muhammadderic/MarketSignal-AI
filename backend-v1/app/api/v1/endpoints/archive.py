"""Archive calendar aggregate endpoint.

Exposes ``GET /api/v1/archive-counts`` defined in ``API_CONTRACTS.md``
§Endpoint: Get Calendar Archive Counts. Routers validate and delegate;
aggregation happens in the repository (ARC §2).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_handlers import BadRequestError
from app.db.repositories.article_repository import ArticleRepository
from app.db.database import get_async_db
from app.schemas.archive_schema import ArchiveCountItem

logger = logging.getLogger(__name__)

router = APIRouter(tags=["archive"])

_MIN_YEAR = 2000


def get_article_repository() -> ArticleRepository:
    """Provide an :class:`ArticleRepository` instance."""
    return ArticleRepository()


@router.get(
    "/archive-counts",
    response_model=list[ArchiveCountItem],
    summary="Get monthly calendar archive counts",
)
async def get_archive_counts(
    year: int = Query(
        ...,
        description="Target calendar year (> 2000).",
    ),
    month: int = Query(
        ...,
        description="Target calendar month (1-12).",
    ),
    db: AsyncSession = Depends(get_async_db),
    repository: ArticleRepository = Depends(get_article_repository),
) -> list[ArchiveCountItem]:
    """Return daily article counts for the requested month.

    Args:
        year: Calendar year; must be ``> 2000`` (R-001).
        month: Calendar month; must be ``1``–``12`` (R-001).
        db: Injected async database session.
        repository: Injected article repository.

    Raises:
        BadRequestError: When ``year`` or ``month`` is out of range.

    Returns:
        List of :class:`ArchiveCountItem` for dates with at least one article.
    """
    if month < 1 or month > 12:
        raise BadRequestError(
            detail=f"month must be between 1 and 12, got {month}",
            context={"month": month},
        )
    if year <= _MIN_YEAR:
        raise BadRequestError(
            detail=f"year must be greater than {_MIN_YEAR}, got {year}",
            context={"year": year},
        )

    rows = await repository.get_archive_counts(db, year=year, month=month)
    logger.info(
        "Archive counts: year=%d month=%d dates=%d", year, month, len(rows)
    )
    return [
        ArchiveCountItem(date=published_date.isoformat(), count=count)
        for published_date, count in rows
    ]