from datetime import date
from fastapi import APIRouter, Depends, Query

from app.modules.news.dependencies import get_news_service
from app.modules.news.news_constants import ArticleLocale
from app.modules.news.news_schemas import NewsFeedResponse, DateMetadataSchema, NewsArticleResponse
from app.modules.news.news_services import NewsService

router = APIRouter(prefix="/news")


@router.get(
    "/business",
    response_model=NewsFeedResponse
)
def get_business_news(
    locale: str = Query(
        "ID",
        description="Locale code for news region (e.g., ID, US)",
        pattern="^(ID|US)$"
    ),
    service: NewsService = Depends(get_news_service)
) -> NewsFeedResponse:
    """
    Get business news from Google RSS feed.

    Args:
        locale: Locale code (ID or US). Defaults to ID (Indonesia).

    Returns:
        NewsFeedResponse: Filtered business news articles
    """
    return service.get_business_news(locale)


# Retrieves a list of available news publication dates along with their total article counts.
@router.get("/available-dates", response_model=list[DateMetadataSchema])
async def get_available_news_dates(
    service: NewsService = Depends(get_news_service),
) -> list[DateMetadataSchema]:
    """Fetch distinct publication dates available in the news store."""
    dates_list = service.get_available_dates()
    return dates_list


# Retrieve all news articles published on a specific UTC calendar date.
@router.get(
    "/by-date",
    response_model=list[NewsArticleResponse],
)
async def get_news_by_date(
    date: date = Query(..., description="Article date in YYYY-MM-DD format"),
    locale: ArticleLocale = Query(
        ArticleLocale.ID,
        description="Article locale (defaults to ID)",
    ),
    service: NewsService = Depends(get_news_service),
) -> list[NewsArticleResponse]:
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