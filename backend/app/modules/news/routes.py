from fastapi import APIRouter, Depends, Query

from app.modules.news.dependencies import get_news_service
from app.modules.news.news_services import NewsService
from app.modules.news.news_schemas import NewsFeedResponse, DateMetadataSchema

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
