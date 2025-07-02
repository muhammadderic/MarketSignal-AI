"""Integration smoke tests for async SQLAlchemy session against migrated schema.

Verifies AC-003: tables are initialized via Alembic and sessions isolate
per-test state via outer-transaction rollback.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Article, ScrapingStatus, WorkflowState


def _sample_article(**overrides: object) -> Article:
    """Build a fully populated ``Article`` ORM instance for insertion."""
    now = datetime.now(timezone.utc)
    data: dict[str, object] = {
        "google_url": "https://news.google.com/rss/articles/mock?oc=5",
        "resolved_url": None,
        "url_hash": "0" * 64,
        "title": "Acme Corp reports record Q3 earnings",
        "source_name": "Reuters",
        "published_at": now,
        "published_at_date": now.date(),
        "workflow_state": WorkflowState.INGESTED.value,
        "scraping_status": ScrapingStatus.PENDING.value,
    }
    data.update(overrides)
    return Article(**data)


async def test_db_session_crud_roundtrip(db_session: AsyncSession) -> None:
    """Insert, select, update, and delete an Article within the test session."""
    article = _sample_article()
    db_session.add(article)
    await db_session.flush()
    assert article.id is not None

    fetched = await db_session.scalar(select(Article).where(Article.id == article.id))
    assert fetched is not None
    assert fetched.title == article.title

    fetched.relevance_score = 4
    fetched.relevance_reasoning = "Specific earnings figures."
    fetched.workflow_state = WorkflowState.RELEVANCE_SCORED.value
    await db_session.flush()

    await db_session.delete(fetched)
    await db_session.flush()

    remaining = await db_session.scalar(select(Article).where(Article.id == article.id))
    assert remaining is None


async def test_test_isolation_between_tests(db_session: AsyncSession) -> None:
    """A fresh test session must start empty thanks to per-test rollback."""
    count = await db_session.scalar(select(Article.id))
    assert count is None