import logging
from datetime import datetime, date
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.news.models import NewsArticleData
from app.modules.news.news_constants import ArticleLocale

logger = logging.getLogger(__name__)


# Row type aliases (module-level, per conventions)
ArchiveCountRow = tuple[datetime, int]


class NewsArchieveRepo:
    """Persistence operations for news articles."""

    def __init__(self, db: Session):
        self.db = db

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
            .order_by(day_expr.asc())
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

    def insert_articles(self, articles: list[dict]) -> None:
        """
        Bulk-insert adapted article dicts.
        Uses `INSERT ... ON CONFLICT DO NOTHING` semantics to satisfy the
        unique constraint on (title, source, published_at, locale).
        """
        if not articles:
            return

        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(NewsArticleData).values(articles)
        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_news_article_identity",
        )
        self.db.execute(stmt)
        self.db.commit()
