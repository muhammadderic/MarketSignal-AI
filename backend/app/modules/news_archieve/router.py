from fastapi import APIRouter, Depends, Query, status

from app.modules.news.news_constants import ArticleLocale
from app.modules.news_archieve.constants import MONTH_QUERY_PATTERN
from app.modules.news_archieve.schemas import ArchiveCountsResponse
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
