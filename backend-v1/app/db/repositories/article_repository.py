"""Article repository encapsulating SQLite mutations.

Owns all ``INSERT ... ON CONFLICT DO NOTHING`` semantics for ingestion. The
service layer must not execute raw SQL (ARC §2, §3).
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import defer
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Article, ScrapingStatus, WorkflowState

logger = logging.getLogger(__name__)


class ArticleRepository:
    """Persistence operations for :class:`~app.db.models.Article`."""

    # ------------
    # --- READ ---
    # ------------
    async def get_by_ids(
        self,
        db: AsyncSession,
        article_ids: list[int],
    ) -> list[Article]:
        """Fetch article rows by primary key IDs.

        Args:
            db: Active async session.
            article_ids: Candidate article IDs (may contain duplicates).

        Returns:
            Matching :class:`Article` rows; order is not guaranteed. Missing IDs
            are simply absent from the result.
        """
        if not article_ids:
            return []
        result = await db.execute(
            select(Article).where(Article.id.in_(set(article_ids)))
        )
        return list(result.scalars().all())

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

    async def list_articles(
        self,
        db: AsyncSession,
        *,
        published_date: date | None = None,
        workflow_state: WorkflowState | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Article], int]:
        """Return a page of article metadata plus the total matching count.

        Applies optional filters on the indexed ``published_at_date`` and
        ``workflow_state`` columns, orders by ``published_at`` descending, and
        defers the heavy text columns (``scraped_content``,
        ``financial_insight``) so the list payload stays small
        (``API_CONTRACTS.md`` §Business Rules).

        Args:
            db: Active async session.
            published_date: Optional UTC publication date filter.
            workflow_state: Optional lifecycle state filter.
            limit: Page size (already validated by the endpoint, 1–200).
            offset: Pagination offset (already validated, ``>= 0``).

        Returns:
            ``(items, total)`` where ``total`` is the unpaginated match count.
        """
        conditions = []
        if published_date is not None:
            conditions.append(Article.published_at_date == published_date)
        if workflow_state is not None:
            conditions.append(Article.workflow_state == workflow_state.value)

        count_stmt = select(func.count(Article.id))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total = int((await db.execute(count_stmt)).scalar_one())

        stmt = (
            select(Article)
            .options(
                defer(Article.scraped_content),
                defer(Article.financial_insight),
            )
            .order_by(Article.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if conditions:
            stmt = stmt.where(*conditions)

        result = await db.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    # --------------
    # --- CREATE ---
    # --------------
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

    # --------------
    # --- UPDATE ---
    # --------------
    async def update_relevance_scores(
        self,
        db: AsyncSession,
        updates: list[dict[str, Any]],
    ) -> None:
        """Persist relevance scores and reasoning for a batch of articles.

        Only articles whose current ``workflow_state`` is a permitted
        predecessor (``Ingested``) are advanced to ``Relevance Scored``.
        Later states are preserved (forward-only lifecycle) while the scoring
        columns are still refreshed.

        Args:
            db: Active async session.
            updates: List of dicts with keys ``id``, ``relevance_score``,
                ``relevance_reasoning``.
        """
        if not updates:
            return

        now = datetime.now(UTC)
        for upt in updates:
            stmt = (
                update(Article)
                .where(Article.id == upt["id"])
                .values(
                    relevance_score=upt["relevance_score"],
                    relevance_reasoning=upt["relevance_reasoning"],
                    updated_at=now,
                )
            )
            await db.execute(stmt)

        # Advance workflow_state forward-only for eligible articles.
        eligible_ids = [u["id"] for u in updates]
        advance_stmt = (
            update(Article)
            .where(
                Article.id.in_(eligible_ids),
                Article.workflow_state == WorkflowState.INGESTED.value,
            )
            .values(
                workflow_state=WorkflowState.RELEVANCE_SCORED.value,
                updated_at=now,
            )
        )
        await db.execute(advance_stmt)
        await db.flush()

    async def update_resolution_results(
        self,
        db: AsyncSession,
        updates: list[dict[str, Any]],
    ) -> None:
        """Persist resolved URLs and optional normalized source names.

        For each update, writes ``resolved_url`` and (when provided)
        ``source_name``, and advances ``workflow_state`` forward-only to
        ``URL Resolved`` only when the current state is ``Ingested`` or
        ``Relevance Scored`` (Q5(b), FEAT-005).

        Args:
            db: Active async session.
            updates: List of dicts with keys ``id``, ``resolved_url``,
                ``source_name`` (optional, may be ``None``).
        """
        if not updates:
            return

        now = datetime.now(UTC)
        for update in updates:
            values: dict[str, Any] = {
                "resolved_url": update["resolved_url"],
                "updated_at": now,
            }
            if update.get("source_name") is not None:
                values["source_name"] = update["source_name"]
            await db.execute(
                update(Article)
                .where(Article.id == update["id"])
                .values(**values)
            )

        eligible_ids = [u["id"] for u in updates]
        advance_stmt = (
            update(Article)
            .where(
                Article.id.in_(eligible_ids),
                Article.workflow_state.in_(
                    [
                        WorkflowState.INGESTED.value,
                        WorkflowState.RELEVANCE_SCORED.value,
                    ]
                ),
            )
            .values(
                workflow_state=WorkflowState.URL_RESOLVED.value,
                updated_at=now,
            )
        )
        await db.execute(advance_stmt)
        await db.flush()


def _utcnow_factory() -> datetime:  # pragma: no cover - helper for tests
    return datetime.now(UTC)


__all__ = ["ArticleRepository"]