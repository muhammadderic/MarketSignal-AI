"""Tests for the FEAT-002 monthly archive calendar backend.

Covers ``ArticleRepository.get_archive_counts`` and
``GET /api/v1/archive-counts`` against the migrated test schema provided by
``tests/conftest.py``. No external I/O is performed; everything runs against
the isolated async SQLite fixture (ARC-002 / AS-007).

Acceptance criteria mapped:
    * AC-001 — 200 OK array of ``{date, count}`` for dates with articles.
    * AC-002 — 400 for out-of-range ``month`` or invalid ``year``; 422 for
      missing / non-integer query params.

Month-boundary inclusion/exclusion and the December → January rollover are
verified directly against the repository's date-range filter.
"""

from __future__ import annotations

import hashlib
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Article, ScrapingStatus, WorkflowState
from app.db.repositories.article_repository import ArticleRepository


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
) -> Article:
    """Build a fully populated ``Article`` ORM instance for seeding.

    ``url_hash`` is derived from ``url_suffix`` so every seeded row is unique
    against the ``ix_articles_url_hash`` and the composite
    ``(title, published_at_date)`` constraints.
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
        workflow_state=WorkflowState.INGESTED.value,
        scraping_status=ScrapingStatus.PENDING.value,
    )


@pytest_asyncio.fixture
async def seeded_october_2026(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncSession]:
    """Seed three articles across October 2026 plus boundary/adjacent dates.

    Rows planted:
        * 2026-10-01 (2 articles)
        * 2026-10-15 (1 article)
        * 2026-09-30 (out of range — must not be counted)
        * 2026-11-01 (out of range — must not be counted)
    """
    rows = [
        _article(
            title="Oct 1 A",
            published_at=datetime(2026, 10, 1, 8, 0, tzinfo=UTC),
            url_suffix="OCT1A",
        ),
        _article(
            title="Oct 1 B",
            published_at=datetime(2026, 10, 1, 18, 0, tzinfo=UTC),
            url_suffix="OCT1B",
        ),
        _article(
            title="Oct 15",
            published_at=datetime(2026, 10, 15, 12, 0, tzinfo=UTC),
            url_suffix="OCT15",
        ),
        _article(
            title="Sep 30",
            published_at=datetime(2026, 9, 30, 23, 59, tzinfo=UTC),
            url_suffix="SEP30",
        ),
        _article(
            title="Nov 1",
            published_at=datetime(2026, 11, 1, 0, 0, tzinfo=UTC),
            url_suffix="NOV1",
        ),
    ]
    db_session.add_all(rows)
    await db_session.flush()
    yield db_session


# ----------------------
# Repository-level tests
# ----------------------
async def test_repository_groups_by_date_and_orders_ascending(
    seeded_october_2026: AsyncSession,
) -> None:
    """Counts are grouped per day, ascending, and bounded to the month."""
    repo = ArticleRepository()
    rows = await repo.get_archive_counts(seeded_october_2026, year=2026, month=10)

    assert rows == [
        (date(2026, 10, 1), 2),
        (date(2026, 10, 15), 1),
    ]


async def test_repository_excludes_adjacent_month_boundaries(
    seeded_october_2026: AsyncSession,
) -> None:
    """Sep 30 and Nov 1 rows must never appear in the October aggregate."""
    repo = ArticleRepository()
    rows = await repo.get_archive_counts(seeded_october_2026, year=2026, month=10)

    returned_dates = {d for d, _ in rows}
    assert date(2026, 9, 30) not in returned_dates
    assert date(2026, 11, 1) not in returned_dates


async def test_repository_returns_empty_for_month_without_articles(
    db_session: AsyncSession,
) -> None:
    repo = ArticleRepository()
    rows = await repo.get_archive_counts(db_session, year=2024, month=1)
    assert rows == []


async def test_repository_december_rollover_includes_dec_31(
    db_session: AsyncSession,
) -> None:
    """December range ends at ``year+1-01-01`` exclusive; Dec 31 counts."""
    db_session.add(
        _article(
            title="Dec 31",
            published_at=datetime(2025, 12, 31, 23, 0, tzinfo=UTC),
            url_suffix="DEC31",
        )
    )
    # A January 1st row must not be counted.
    db_session.add(
        _article(
            title="Jan 1",
            published_at=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
            url_suffix="JAN1",
        )
    )
    await db_session.flush()

    repo = ArticleRepository()
    rows = await repo.get_archive_counts(db_session, year=2025, month=12)

    assert rows == [(date(2025, 12, 31), 1)]


# -------------------------------------
# API-level tests — happy path (AC-001)
# -------------------------------------
async def test_endpoint_returns_200_and_expected_payload(
    async_client: AsyncClient,
    seeded_october_2026: AsyncSession,
) -> None:
    response = await async_client.get(
        "/api/v1/archive-counts",
        params={"year": 2026, "month": 10},
    )

    assert response.status_code == 200, response.text
    assert response.json() == [
        {"date": "2026-10-01", "count": 2},
        {"date": "2026-10-15", "count": 1},
    ]


async def test_endpoint_returns_empty_array_when_no_articles(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get(
        "/api/v1/archive-counts",
        params={"year": 2024, "month": 1},
    )

    assert response.status_code == 200, response.text
    assert response.json() == []


# -------------------------------------
# API-level tests — validation (AC-002)
# -------------------------------------
@pytest.mark.parametrize("month", [0, -1, 13, 99])
async def test_endpoint_month_out_of_range_returns_400(
    async_client: AsyncClient,
    month: int,
) -> None:
    response = await async_client.get(
        "/api/v1/archive-counts",
        params={"year": 2026, "month": month},
    )

    assert response.status_code == 400, response.text
    body = response.json()
    assert body["error_code"] == "BAD_REQUEST"
    assert "month" in body["detail"]


@pytest.mark.parametrize("year", [1999, 2000, 0, -2026])
async def test_endpoint_year_not_greater_than_min_returns_400(
    async_client: AsyncClient,
    year: int,
) -> None:
    """Boundary: ``year <= 2000`` is rejected per R-001."""
    response = await async_client.get(
        "/api/v1/archive-counts",
        params={"year": year, "month": 1},
    )

    assert response.status_code == 400, response.text
    body = response.json()
    assert body["error_code"] == "BAD_REQUEST"
    assert "year" in body["detail"]


async def test_endpoint_year_just_above_min_returns_200(
    async_client: AsyncClient,
) -> None:
    """Boundary: ``year = 2001`` is accepted (empty result permitted)."""
    response = await async_client.get(
        "/api/v1/archive-counts",
        params={"year": 2001, "month": 1},
    )

    assert response.status_code == 200, response.text
    assert response.json() == []