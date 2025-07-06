"""Article repository encapsulating SQLite mutations.

Owns all ``INSERT ... ON CONFLICT DO NOTHING`` semantics for ingestion. The
service layer must not execute raw SQL (ARC §2, §3).
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any

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

        from sqlalchemy import select

        result = await db.execute(
            select(Article.url_hash).where(Article.url_hash.in_(hashes))
        )
        return set(result.scalars().all())


def _utcnow_factory() -> datetime:  # pragma: no cover - helper for tests
    return datetime.now(UTC)


__all__ = ["ArticleRepository", "date"]