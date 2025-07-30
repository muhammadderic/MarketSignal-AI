"""Tests for the FEAT-003 article metadata list endpoint.

Covers ``GET /api/v1/articles`` against the migrated test schema provided by
``tests/conftest.py``. No external I/O is performed; all tests run against the
isolated async SQLite fixture (ARC-002 / AS-007).

Acceptance criteria mapped (FEAT-003 §9):
    * AC-001 — 200 OK paginated payload; heavy columns
      (``scraped_content``, ``financial_insight``) excluded from items.
    * AC-002 — Items ordered by ``published_at`` descending.
    * AC-007 — ``limit`` / ``offset`` paginate correctly across a data set.

Business rules (API_CONTRACTS.md §List Articles):
    * ``date`` (YYYY-MM-DD) filters on ``published_at_date``.
    * ``workflow_state`` filters on the lifecycle state.
    * ``limit`` defaults to 50, max 200; ``offset`` defaults to 0.
    * Unknown ``workflow_state`` and out-of-range ``limit``/``offset`` are
      rejected by Pydantic-native validation (422).
    * Malformed ``date`` strings are rejected (422).
"""

from __future__ import annotations

import hashlib
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Article, ScrapingStatus, WorkflowState

ENDPOINT = "/api/v1/articles"


# ---------------
# Seeding helpers
# ---------------
def _hash(*parts: str) -> str:
    """Return a stable 64-char SHA-256 hex digest for synthetic URLs."""
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()


def _article(
    *,
    title: str,
    published_at: datetime,
    url_suffix: str,
    workflow_state: WorkflowState = WorkflowState.INGESTED,
    scraping_status: ScrapingStatus = ScrapingStatus.PENDING,
    relevance_score: int | None = None,
    relevance_reasoning: str | None = None,
    scraped_content: str | None = None,
    financial_insight: str | None = None,
) -> Article:
    """Build a fully populated ``Article`` ORM instance for seeding.

    ``url_hash`` derives from ``url_suffix`` so seeded rows stay unique against
    ``ix_articles_url_hash`` and ``uq_articles_title_published_at_date``.
    """
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=UTC)
    return Article(
        google_url=f"https://news.google.com/rss/articles/{url_suffix}",
        resolved_url=None,
        url_hash=_hash(url_suffix),
        title=title,
        source_name="Reuters",
        published_at=published_at,
        published_at_date=published_at.date(),
        workflow_state=workflow_state.value,
        scraping_status=scraping_status.value,
        relevance_score=relevance_score,
        relevance_reasoning=relevance_reasoning,
        scraped_content=scraped_content,
        financial_insight=financial_insight,
    )


@pytest_asyncio.fixture
async def seeded_mixed(db_session: AsyncSession) -> AsyncGenerator[AsyncSession]:
    """Seed six articles spanning two dates, two states, and heavy-column data.

    Layout (``published_at`` descending):
        * 2026-10-21T18:00Z — Financial Insight Extracted / SUCCESS
          (scraped_content and financial_insight populated — must NOT appear
          in the list payload).
        * 2026-10-21T15:00Z — Relevance Scored (score=4, reasoning set)
        * 2026-10-21T09:00Z — Ingested
        * 2026-10-21T06:00Z — Ingested
        * 2026-10-20T23:00Z — Ingested (different date — must be excluded by
          ``date=2026-10-21`` filters)
        * 2026-10-19T12:00Z — URL Resolved (used to isolate ``workflow_state``
          filter counts)
    """
    rows = [
        _article(
            title="Oct21 18h Insight",
            published_at=datetime(2026, 10, 21, 18, 0, tzinfo=UTC),
            url_suffix="OCT21_18",
            workflow_state=WorkflowState.FINANCIAL_INSIGHT_EXTRACTED,
            scraping_status=ScrapingStatus.SUCCESS,
            relevance_score=5,
            relevance_reasoning="Critical macro signal.",
            scraped_content="Body text that must be excluded from list payloads.",
            financial_insight="Insight text that must be excluded from list payloads.",
        ),
        _article(
            title="Oct21 15h Scored",
            published_at=datetime(2026, 10, 21, 15, 0, tzinfo=UTC),
            url_suffix="OCT21_15",
            workflow_state=WorkflowState.RELEVANCE_SCORED,
            relevance_score=4,
            relevance_reasoning="Direct macro impact.",
        ),
        _article(
            title="Oct21 09h Ingested",
            published_at=datetime(2026, 10, 21, 9, 0, tzinfo=UTC),
            url_suffix="OCT21_09",
        ),
        _article(
            title="Oct21 06h Ingested",
            published_at=datetime(2026, 10, 21, 6, 0, tzinfo=UTC),
            url_suffix="OCT21_06",
        ),
        _article(
            title="Oct20 23h Ingested",
            published_at=datetime(2026, 10, 20, 23, 0, tzinfo=UTC),
            url_suffix="OCT20_23",
        ),
        _article(
            title="Oct19 12h URLResolved",
            published_at=datetime(2026, 10, 19, 12, 0, tzinfo=UTC),
            url_suffix="OCT19_12",
            workflow_state=WorkflowState.URL_RESOLVED,
        ),
    ]
    db_session.add_all(rows)
    await db_session.flush()
    yield db_session


# -------------------------------
# AC-001 — 200 OK + field shape
# -------------------------------
async def test_list_returns_200_and_paginated_envelope(
    async_client: AsyncClient,
    seeded_mixed: AsyncSession,
) -> None:
    """Response envelope contains ``total``/``limit``/``offset``/``items``."""
    response = await async_client.get(ENDPOINT)

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body.keys()) == {"total", "limit", "offset", "items"}
    assert body["total"] == 6
    assert body["limit"] == 50  # documented default
    assert body["offset"] == 0
    assert isinstance(body["items"], list)
    assert len(body["items"]) == 6


async def test_list_items_exclude_heavy_text_columns(
    async_client: AsyncClient,
    seeded_mixed: AsyncSession,
) -> None:
    """``scraped_content`` and ``financial_insight`` MUST be absent from items."""
    response = await async_client.get(ENDPOINT, params={"date": "2026-10-21"})

    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert items, "expected seeded Oct 21 articles"
    for item in items:
        assert "scraped_content" not in item
        assert "financial_insight" not in item


async def test_list_item_contains_documented_fields(
    async_client: AsyncClient,
    seeded_mixed: AsyncSession,
) -> None:
    """Each item exposes the metadata fields enumerated in API_CONTRACTS.md."""
    response = await async_client.get(ENDPOINT, params={"date": "2026-10-21"})

    assert response.status_code == 200, response.text
    item = response.json()["items"][0]
    expected_fields = {
        "id",
        "title",
        "source_name",
        "published_at",
        "published_at_date",
        "google_url",
        "resolved_url",
        "relevance_score",
        "relevance_reasoning",
        "scraping_status",
        "workflow_state",
        "created_at",
        "updated_at",
    }
    assert expected_fields.issubset(item.keys())


async def test_list_relevance_fields_serialize_when_present(
    async_client: AsyncClient,
    seeded_mixed: AsyncSession,
) -> None:
    """Scored articles expose ``relevance_score`` / ``relevance_reasoning``."""
    response = await async_client.get(ENDPOINT, params={"date": "2026-10-21"})
    items = response.json()["items"]

    by_title = {item["title"]: item for item in items}
    scored = by_title["Oct21 15h Scored"]
    assert scored["relevance_score"] == 4
    assert scored["relevance_reasoning"] == "Direct macro impact."

    unscored = by_title["Oct21 09h Ingested"]
    assert unscored["relevance_score"] is None
    assert unscored["relevance_reasoning"] is None