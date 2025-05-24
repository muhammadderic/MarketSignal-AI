from fastapi import Depends

from app.integrations.clients.google_rss_client import GoogleRSSClient
from app.modules.news.news_services import NewsService
from app.core.dependencies import get_news_client


def get_news_service(
    client: GoogleRSSClient = Depends(get_news_client)
) -> NewsService:
    """Dependency provider for NewsService"""
    return NewsService(client=client)
    