from datetime import datetime, date, time, timedelta, timezone
from typing import Sequence
from sqlalchemy import Row, select, func, bindparam, update
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert

from app.modules.news.models import NewsArticleData
from app.modules.news.news_constants import ArticleLocale


NewsArticleRecordRow = Row[
    tuple[
        int,
        str | None,
        str,
        datetime,
        str | None,
        ArticleLocale,
        int | None,
        str | None,
    ]
]

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
    ) -> Sequence[NewsArticleRecordRow]:
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
                NewsArticleData.id,
                NewsArticleData.title,
                NewsArticleData.source,
                NewsArticleData.published_at,
                NewsArticleData.link,
                NewsArticleData.locale,
                NewsArticleData.relevance_score,
                NewsArticleData.relevance_reason,
            )
            .where(
                NewsArticleData.published_at >= start_date,
                NewsArticleData.locale == locale,
            )
            .order_by(NewsArticleData.published_at.desc())
        )
        return self.db.execute(stmt).all()

    def get_id_title_pairs_by_ids(
        self, 
        article_ids: list[int]
    ) -> Sequence[Row[tuple[int, str | None]]]:
        """
        Fetch (id, title) pairs for the given article IDs.
        
        Args:
            article_ids: List of article IDs to fetch.
            
        Returns:
            Sequence of rows with named access (.id, .title).
            Missing IDs are excluded. Titles may be None.
        """
        if not article_ids:
            return []
        
        stmt = (
            select(NewsArticleData.id, NewsArticleData.title)
            .where(NewsArticleData.id.in_(article_ids))
        )
        return self.db.execute(stmt).all()

    def get_id_title_pairs_by_published_date(
        self,
        date: date,
    ) -> Sequence[Row[tuple[int, str | None]]]:
        """
        Fetch (id, title) pairs for all articles whose `published_at`
        falls within the given UTC calendar date.

        Since `published_at` is a DateTime column (UTC-normalized) and
        the incoming filter is a `date`, we translate the date into a
        half-open UTC range: [00:00:00Z, next_day 00:00:00Z). This keeps
        the query sargable against `ix_news_article_data_published_at`.

        Args:
            date: The UTC calendar date to filter by.

        Returns:
            A sequence of SQLAlchemy Row objects, each carrying
            (id, title) as a tuple. Empty sequence if no rows match.
        """
        start = datetime.combine(date, time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        stmt = (
            select(NewsArticleData.id, NewsArticleData.title)
            .where(
                NewsArticleData.published_at >= start,
                NewsArticleData.published_at < end,
            )
            .order_by(NewsArticleData.id)
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

    # === UPDATE ===
    def update_news_scores(
        self,
        score_payload: list[dict[str, any]],
    ) -> None:
        """
        Bulk-update `relevance_score` and `relevance_reason` for a batch
        of news rows, keyed by primary key `id`.

        Uses SQLAlchemy 2.0's executemany-style bulk UPDATE, which emits
        a single `UPDATE ... WHERE id = :id` statement executed once per
        payload entry within one round-trip. To avoid N individual
        SELECT+UPDATE pairs for N scored articles.

        Args:
            score_payload: List of dicts, each containing at minimum:
                - "id" (int): target row primary key
                - "relevance_score" (int)
                - "relevance_reason" (str)

        Returns:
            None. Commits the transaction on success.

        Raises:
            SQLAlchemyError: Propagated on DB failure; caller is
                responsible for rollback if the session is shared.
        """
        if not score_payload:
            return

        stmt = update(NewsArticleData).where(
            NewsArticleData.id == bindparam("id")
        )

        self.db.execute(stmt, score_payload)
        self.db.commit()
