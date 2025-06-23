from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.integrations.adapters import GoogleNewsLinkAdapter
from app.integrations.clients import GoogleNewsClient
from app.modules.news_scraping.repositories import NewsArticleRepository
from app.modules.news_scraping.services import LinkResolutionService


def get_news_article_repository(session: Session = Depends(get_db)) -> NewsArticleRepository:
    return NewsArticleRepository(session)


def get_google_news_adapter() -> GoogleNewsLinkAdapter:
    return GoogleNewsLinkAdapter(GoogleNewsClient())


def get_link_resolution_service(
    repository: NewsArticleRepository = Depends(get_news_article_repository),
    adapter: GoogleNewsLinkAdapter = Depends(get_google_news_adapter),
) -> LinkResolutionService:
    return LinkResolutionService(repository, adapter)