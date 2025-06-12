from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_google_rss_adapter
from app.integrations.adapters import GoogleRSSAdapter
from app.modules.news_archieve.repositories import NewsArchieveRepo
from app.modules.news_archieve.services import NewsArchieveService


def get_news_archieve_repo(db: Session = Depends(get_db)) -> NewsArchieveRepo:
    """Provide a NewsArchieveRepo bound to the current request session."""
    return NewsArchieveRepo(db)


def get_news_archieve_service(
    repo: NewsArchieveRepo = Depends(get_news_archieve_repo),
    rss_adapter: GoogleRSSAdapter = Depends(get_google_rss_adapter),
) -> NewsArchieveService:
    """Provide a NewsArchieveService with repo and RSS adapter wired in."""
    return NewsArchieveService(repo=repo, rss_adapter=rss_adapter)