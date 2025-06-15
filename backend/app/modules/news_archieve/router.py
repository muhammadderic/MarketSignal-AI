from fastapi import APIRouter, Depends, Query, status
from datetime import date

from app.modules.news.news_constants import ArticleLocale
from app.modules.news_archieve.constants import MONTH_QUERY_PATTERN
from app.modules.news_archieve.schemas import ArchiveCountsResponse, DailyNewsResponse
from app.modules.news_archieve.services import NewsArchieveService
from app.modules.news_archieve.dependencies import get_news_archieve_service

router = APIRouter(prefix="/news-archieve")


@router.get(
    "/archive/counts",
    response_model=ArchiveCountsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_archive_counts(
    month: str = Query(
        ...,
        description="Month in YYYY-MM format (e.g. 2026-10).",
        pattern=MONTH_QUERY_PATTERN,
    ),
    locale: ArticleLocale = Query(
        ...,
        description="Article locale. One of ID, US, GLOBAL, UNSIGNED.",
    ),
    service: NewsArchieveService = Depends(get_news_archieve_service),
) -> ArchiveCountsResponse:
    """
    Return per-day article counts for one month and locale (for calendar badges).
    
    `counts` is sorted by `date` descending (newest first).
    """
    return service.get_archive_counts(month=month, locale=locale)


# Retrieve all news articles published on a specific UTC calendar date.
@router.get(
    "/by-date",
    response_model=DailyNewsResponse,
)
async def get_news_by_date(
    date: date = Query(..., description="Article date in YYYY-MM-DD format"),
    locale: ArticleLocale = Query(
        ArticleLocale.ID,
        description="Article locale (defaults to ID)",
    ),
    service: NewsArchieveService = Depends(get_news_archieve_service),
) -> DailyNewsResponse:
    """
    Retrieve all news articles published on a specific UTC calendar date,
    scoped to a locale.

    Args:
        date: The UTC calendar date to fetch articles for (YYYY-MM-DD).
        locale: Target locale; defaults to ArticleLocale.ID.

    Returns:
        A list of NewsArticleResponse payloads, newest first.
    """
    return service.get_news_by_published_date(date, locale)
