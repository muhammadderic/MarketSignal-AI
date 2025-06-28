"""Article ORM entity for the MarketSignal AI SQLite database.

Field types, constraints, and indexes mirror ``DATA_MODEL.md`` §Entity: Article.
All timestamp columns are timezone-aware UTC (ARC-004). The cross-column
invariant ``ck_articles_insight_requires_scraped_content`` enforces
``DATA_MODEL.md`` §Check Constraints item 4.
"""

from __future__ import annotations

import enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class WorkflowState(str, enum.Enum):
    """Deterministic workflow states (``DATA_MODEL.md`` §Lifecycle)."""

    INGESTED = "Ingested"
    RELEVANCE_SCORED = "Relevance Scored"
    URL_RESOLVED = "URL Resolved"
    SCRAPED = "Scraped"
    FINANCIAL_INSIGHT_EXTRACTED = "Financial Insight Extracted"


class ScrapingStatus(str, enum.Enum):
    """Localized scraping sub-state, isolated per item (ARC-006)."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


def _utcnow() -> datetime:
    """Return the current time as a UTC-aware datetime."""
    return datetime.now(timezone.utc)


# SQLite has no native ``now()`` returning an ISO-8601 UTC string. This default
# produces ``YYYY-MM-DDTHH:MM:SS.fff+00:00`` which SQLAlchemy parses back into a
# ``datetime`` bearing ``timezone.utc``.
_SQLITE_UTC_NOW = text("(strftime('%Y-%m-%dT%H:%M:%f+00:00','now'))")


class Article(Base):
    """A single ingested news article record (``DATA_MODEL.md`` §Entity)."""

    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint(
            "title",
            "published_at_date",
            name="uq_articles_title_published_at_date",
        ),
        CheckConstraint(
            "relevance_score IS NULL OR (relevance_score >= 1 AND relevance_score <= 5)",
            name="ck_articles_relevance_score",
        ),
        CheckConstraint(
            "workflow_state IN ("
            "'Ingested', "
            "'Relevance Scored', "
            "'URL Resolved', "
            "'Scraped', "
            "'Financial Insight Extracted'"
            ")",
            name="ck_articles_workflow_state",
        ),
        CheckConstraint(
            "scraping_status IN ('PENDING', 'IN_PROGRESS', 'SUCCESS', 'FAILED')",
            name="ck_articles_scraping_status",
        ),
        CheckConstraint(
            "workflow_state <> 'Financial Insight Extracted' "
            "OR (scraping_status = 'SUCCESS' AND scraped_content IS NOT NULL)",
            name="ck_articles_insight_requires_scraped_content",
        ),
        Index("ix_articles_published_at_date", "published_at_date"),
        Index("ix_articles_workflow_state", "workflow_state"),
        Index("ix_articles_scraping_status", "scraping_status"),
        Index("ix_articles_url_hash", "url_hash", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # URL provenance: google_url immutable (ARC-005), resolved_url separate
    google_url: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Primary metadata
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # UTC-normalized timestamps (ARC-004)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Workflow / relevance
    workflow_state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=WorkflowState.INGESTED.value,
        server_default=WorkflowState.INGESTED.value,
    )
    relevance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    relevance_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Scraping
    scraping_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ScrapingStatus.PENDING.value,
        server_default=ScrapingStatus.PENDING.value,
    )
    scraped_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    scraping_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Financial insight
    financial_insight: Mapped[str | None] = mapped_column(Text, nullable=True)
    insight_extracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Lifecycle
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=_SQLITE_UTC_NOW,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
        server_default=_SQLITE_UTC_NOW,
    )

    def __repr__(self) -> str:
        return f"Article(id={self.id!r}, title={self.title!r}, state={self.workflow_state!r})"