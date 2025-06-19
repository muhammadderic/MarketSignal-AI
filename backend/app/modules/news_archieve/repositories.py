import logging
from datetime import datetime, date, timezone
from typing import Sequence

from sqlalchemy import func, select, insert, bindparam, update, Row
from sqlalchemy.orm import Session

from app.modules.news.models import NewsArticleData
from app.modules.news_archieve.constants import ArticleLocale

logger = logging.getLogger(__name__)


# Row type aliases (module-level, per conventions)
ArchiveCountRow = tuple[date, int]

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

class NewsArchieveRepo:
    """Persistence operations for news articles."""

    def __init__(self, db: Session):
        self.db = db

    # === READ ===
    def get_archive_counts(
        self,
        *,
        locale: ArticleLocale,
        start: datetime,
        end: datetime,
    ) -> Sequence[ArchiveCountRow]:
        """
        Return (publication_day, total) rows for the given locale within
        [start, end), grouped by publication date in UTC.
        """
        day_expr = func.date(NewsArticleData.published_at)

        stmt = (
            select(day_expr.label("day"), func.count(NewsArticleData.id).label("total"))
            .where(
                NewsArticleData.locale == locale,
                NewsArticleData.published_at >= start,
                NewsArticleData.published_at < end,
            )
            .group_by(day_expr)
            .order_by(day_expr.desc())
        )

        raw = self.db.execute(stmt).all()

        normalized: list[ArchiveCountRow] = []
        for day_value, total in raw:
            if isinstance(day_value, datetime):
                d = day_value.date()
            elif isinstance(day_value, date):
                d = day_value
            else:
                d = datetime.strptime(str(day_value)[:10], "%Y-%m-%d").date()
            normalized.append((d, total))
        return normalized

    def get_archive_counts_with_latest_timestamp(
        self,
        *,
        locale: ArticleLocale,
        start: datetime,
        end: datetime,
    ) -> tuple[Sequence[ArchiveCountRow], datetime | None]:
        day_expr = func.date(NewsArticleData.published_at)

        newest_stmt = (
            select(func.max(NewsArticleData.published_at))
            .where(
                NewsArticleData.locale == locale,
                NewsArticleData.published_at >= start,
                NewsArticleData.published_at < end,
            )
            .scalar_subquery()
        )

        stmt = (
            select(
                day_expr.label("day"),
                func.count(NewsArticleData.id).label("total"),
                newest_stmt.label("newest_published_at"),
            )
            .where(
                NewsArticleData.locale == locale,
                NewsArticleData.published_at >= start,
                NewsArticleData.published_at < end,
            )
            .group_by(day_expr)
            .order_by(day_expr.desc())
        )

        rows = self.db.execute(stmt).all()

        if not rows:
            return [], None

        daily_counts = [
            (date.fromisoformat(str(row.day)[:10]), row.total)
            for row in rows
        ]

        return daily_counts, rows[0].newest_published_at

    def get_all_by_published_date(
        self,
        start_date: datetime,
        locale: ArticleLocale,
        end_date: datetime | None = None,
    ) -> Sequence[NewsArticleRecordRow]:
        """
        Fetch all news articles whose `published_at` falls within the
        given UTC calendar date, scoped to a locale.

        Uses an inclusive [00:00:00, 23:59:59] UTC range so the query
        remains sargable against `ix_news_article_data_published_at`.

        Args:
            start_date
            end_date
            locale: Locale string (e.g. "ID") to scope results.

        Returns:
            Sequence of projected rows carrying the full article payload,
            newest first.
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc).replace(tzinfo=None)

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
                NewsArticleData.published_at <= end_date,
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

    # === CREATE ===
    def insert_articles(self, articles: list[dict]) -> None:
        """Bulk-insert articles, ignoring duplicate identities."""
        if not articles:
            return

        stmt = insert(NewsArticleData).values(articles)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["title", "source", "published_at", "locale"],
        )

        self.db.execute(stmt)
        self.db.commit()

    # === UPDATE ===
    def update_news_scores(
        self,
        score_payload: list[dict[str, any]],
    ) -> None:
        """Bulk-update relevance scores and reasons by article ID."""
        if not score_payload:
            return

        stmt = (
            update(NewsArticleData.__table__)
            .where(NewsArticleData.__table__.c.id == bindparam("target_id"))
            .values(
                relevance_score=bindparam("relevance_score"),
                relevance_reason=bindparam("relevance_reason"),
            )
        )

        self.db.execute(stmt, score_payload)
        self.db.commit()