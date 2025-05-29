from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_news_client
from app.integrations.clients.google_rss_client import GoogleRSSClient
from app.modules.news.news_services import NewsService
from app.modules.news.news_repo import NewsRepository


# --- Repository Dependencies ---
def get_security_repo(db: Session = Depends(get_db)) -> NewsRepository:
    """Dependency provider for NewsRepository"""
    return NewsRepository(db)


# --- Service Dependencies ---
def get_news_service(
    repo: NewsRepository = Depends(get_security_repo),
    client: GoogleRSSClient = Depends(get_news_client)
) -> NewsService:
    """Dependency provider for NewsService"""
    return NewsService(
        repo=repo,
        client=client
    )
    