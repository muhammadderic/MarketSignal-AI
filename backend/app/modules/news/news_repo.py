from datetime import datetime
from typing import Sequence
from sqlalchemy import Row, select, func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert

from app.modules.news.models import NewsArticleData
from app.modules.news.news_constants import ArticleLocale


class NewsRepository:
    def __init__(self, db: Session):
        self.db = db

    # === READ ===
    def get_latest_published_at(self) -> datetime | None:
        """
        Fetch the newest article's published_at value natively using SQL MAX aggregation.
        
        Returns:
            The most recent published_at datetime, or None if the table is empty.
        """
        latest_timestamp = self.db.query(
            func.max(NewsArticleData.published_at)
        ).scalar()

        return latest_timestamp

    def get_articles_from_date(
        self,
        start_date: datetime,
        locale: ArticleLocale | str = ArticleLocale.ID
    ) -> Sequence[Row[tuple[str | None, str, datetime, str | None, str]]]:
        """
        Fetch all articles matching published_at >= start_date and target locale, newest first.
        
        Args:
            start_date: Lower bound (inclusive) for published_at filter.
            locale: Target locale filter (e.g., ArticleLocale.ID or 'ID').
            
        Returns:
            Sequence of rows, each containing (title, source, published_at, link, locale).
        """
        stmt = (
            select(
                NewsArticleData.title,
                NewsArticleData.source,
                NewsArticleData.published_at,
                NewsArticleData.link,
                NewsArticleData.locale
            )
            .where(
                NewsArticleData.published_at >= start_date,
                NewsArticleData.locale == locale
            )
            .order_by(NewsArticleData.published_at.desc())
        )
        return self.db.execute(stmt).all()

    # === CREATE ===
    def save_filtered_articles(self, articles: list[dict[str, str | None]]) -> None:
        """
        Persist filtered news articles to database while ignoring duplicates 
        matching the unique composite constraint (title, source, published_at, locale).
        
        Args:
            articles: List of dictionary payloads to insert.
        """
        if not articles:
            return

        stmt = insert(NewsArticleData).values(articles)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["title", "source", "published_at", "locale"]
        )

        self.db.execute(stmt)
        self.db.commit()
