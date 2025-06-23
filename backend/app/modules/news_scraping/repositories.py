from sqlalchemy.orm import Session
from sqlalchemy import select

from app.modules.news_scraping.constants import LinkResolutionStatus
from app.modules.news_archieve.models import NewsArticleData


class NewsArticleRepository:
    """Persistence operations for news articles."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_ids(self, ids: list[int]) -> list[NewsArticleData]:
        stmt = select(NewsArticleData).where(NewsArticleData.id.in_(ids))
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def update_resolution(
        self, article_id: int, resolved_link: str | None, status: LinkResolutionStatus
    ) -> None:
        article = self.db.get(NewsArticleData, article_id)
        if article is None:
            return
        article.resolved_link = resolved_link
        article.link_resolution_status = status
        self.db.commit()
