from datetime import date
from fastapi import APIRouter, Depends, Query

from app.modules.news.dependencies import get_news_service
from app.modules.news.news_constants import ArticleLocale
from app.modules.news.news_schemas import NewsFeedResponse, DailyNewsResponse
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
    service: NewsService = Depends(get_news_service),
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