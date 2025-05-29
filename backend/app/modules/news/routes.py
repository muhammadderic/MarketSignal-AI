from fastapi import APIRouter, Depends, Query

from app.modules.news.dependencies import get_news_service
from app.modules.news.news_services import NewsService
from app.modules.news.news_schemas import NewsFeedResponse

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
