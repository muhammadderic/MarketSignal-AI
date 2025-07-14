"""Article repository encapsulating SQLite mutations.

Owns all ``INSERT ... ON CONFLICT DO NOTHING`` semantics for ingestion. The
service layer must not execute raw SQL (ARC §2, §3).
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Article, ScrapingStatus, WorkflowState

logger = logging.getLogger(__name__)


class ArticleRepository:
    """Persistence operations for :class:`~app.db.models.Article`."""

    async def insert_unique(
        self,
        db: AsyncSession,
        candidates: list[dict[str, Any]],
    ) -> int:
        """Insert candidate article rows, silently skipping duplicates.

        Uniqueness is enforced at the database layer via
        ``uq_articles_url_hash`` and ``uq_articles_title_published_at_date``.
        ``ON CONFLICT DO NOTHING`` avoids a separate pre-check query and is
        race-safe.

        Args:
            db: Active async session (commit handled by caller/dependency).
            candidates: Normalized row dicts keyed by ORM column name. Each
                dict must include at least ``google_url``, ``url_hash``,
                ``title``, ``published_at``, ``published_at_date``,
                ``source_name``, ``workflow_state``, ``scraping_status``.

        Returns:
            Number of rows actually inserted. ``len(candidates) - inserted`` is
            the duplicate count.
        """
        if not candidates:
            return 0

        now = datetime.now(UTC)
        rows = [
            {
                "workflow_state": WorkflowState.INGESTED.value,
                "scraping_status": ScrapingStatus.PENDING.value,
                "created_at": now,
                "updated_at": now,
                **candidate,
            }
            for candidate in candidates
        ]

        stmt = (
            sqlite_insert(Article)
            .values(rows)
            .on_conflict_do_nothing()
            .returning(Article.id)
        )
        result = await db.execute(stmt)
        inserted_ids = result.scalars().all()
        await db.flush()
        return len(inserted_ids)

    async def count_existing_hashes(
        self,
        db: AsyncSession,
        hashes: list[str],
    ) -> set[str]:
        """Return the subset of ``hashes`` already present in ``articles``.

        Used only for structured INFO logging on duplicate classification;
        correctness does not depend on this call.

        Args:
            db: Active async session.
            hashes: Candidate ``url_hash`` values.

        Returns:
            Set of already-persisted hashes.
        """
        if not hashes:
            return set()

        result = await db.execute(
            select(Article.url_hash).where(Article.url_hash.in_(hashes))
        )
        return set(result.scalars().all())

    async def get_archive_counts(
        self,
        db: AsyncSession,
        year: int,
        month: int,
    ) -> list[tuple[date, int]]:
        """Aggregate article counts grouped by UTC publication date.

        Filters strictly to the requested calendar month using the indexed
        ``published_at_date`` column (``ix_articles_published_at_date``), and
        omits dates with zero articles per ``API_CONTRACTS.md``.

        Args:
            db: Active async session.
            year: Calendar year (validated by the endpoint, ``> 2000``).
            month: Calendar month (validated by the endpoint, ``1``–``12``).

        Returns:
            List of ``(published_at_date, count)`` tuples ordered ascending by
            date. Empty when no articles exist in the month.
        """
        first_of_month = date(year, month, 1)
        if month == 12:
            first_of_next_month = date(year + 1, 1, 1)
        else:
            first_of_next_month = date(year, month + 1, 1)

        stmt = (
            select(
                Article.published_at_date,
                func.count(Article.id).label("article_count"),
            )
            .where(
                Article.published_at_date >= first_of_month,
                Article.published_at_date < first_of_next_month,
            )
            .group_by(Article.published_at_date)
            .order_by(Article.published_at_date.asc())
        )
        result = await db.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]


def _utcnow_factory() -> datetime:  # pragma: no cover - helper for tests
    return datetime.now(UTC)


__all__ = ["ArticleRepository"]