"""Unit tests for :class:`app.services.ingestion.IngestionService`.

Covers FEAT-001 acceptance criteria:

* AC-001 — RSS XML fetched and parsed into Article rows.
* AC-002 — UTC normalization of ``published_at`` + ``published_at_date``.
* AC-003 — SHA-256 ``url_hash`` derived from ``google_url``.
* AC-005 — initial states are ``Ingested`` / ``PENDING`` with null fields.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Article
from app.services.ingestion import IngestionService
from app.db.repositories.article_repository import ArticleRepository


# ----------------
# RSS XML fixtures
# ----------------
_RSS_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>Test Feed</title>
  <link>https://news.google.com/</link>
  <description>Test channel</description>
"""

_RSS_FOOTER = """
</channel>
</rss>
"""


def _item(
    *,
    title: str | None = "Market rallies on rate-cut hopes",
    link: str | None = "https://news.google.com/rss/articles/CBMiTEST1",
    pub_date: str | None = "Mon, 21 Oct 2026 12:00:00 GMT",
    source: str | None = "Reuters",
) -> str:
    parts: list[str] = ["  <item>"]
    if title is not None:
        parts.append(f"    <title>{title}</title>")
    if link is not None:
        parts.append(f"    <link>{link}</link>")
    if pub_date is not None:
        parts.append(f"    <pubDate>{pub_date}</pubDate>")
    if source is not None:
        parts.append(f'    <source url="https://example.com">{source}</source>')
    parts.append("  </item>")
    return "\n".join(parts)


def _build_rss(*items: str) -> str:
    return _RSS_HEADER + "\n".join(items) + _RSS_FOOTER


_VALID_RSS = _build_rss(
    _item(
        title="Central Bank Signals Rate Adjustments",
        link="https://news.google.com/rss/articles/CBMiA",
        pub_date="Mon, 21 Oct 2026 08:30:00 GMT",
        source="Financial News",
    ),
    _item(
        title="Tech Stocks Surge on Earnings Beat",
        link="https://news.google.com/rss/articles/CBMiB",
        pub_date="Mon, 21 Oct 2026 10:15:00 GMT",
        source="Bloomberg",
    ),
    _item(
        title="Oil Prices Dip on Supply Glut Concerns",
        link="https://news.google.com/rss/articles/CBMiC",
        pub_date="Tue, 22 Oct 2026 06:00:00 GMT",
        source="Reuters",
    ),
)


# ----------------------
# HTTP mock helpers (D1)
# ----------------------
def _patch_async_client(
    monkeypatch: pytest.MonkeyPatch,
    handler: httpx.MockTransport,
) -> None:
    """Replace ``IngestionService``'s ``httpx.AsyncClient`` factory.

    Captures the real ``httpx.AsyncClient`` *before* patching so the factory
    body cannot recurse into itself (``httpx.AsyncClient`` is the same object
    referenced by every module-level ``httpx`` binding).
    """

    real_async_client = httpx.AsyncClient  # snapshot before patching

    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        # Ignore the service's timeout kwarg; MockTransport does not need it.
        del args, kwargs
        return real_async_client(transport=handler)

    monkeypatch.setattr(
        "app.services.ingestion.httpx.AsyncClient",
        _factory,
    )


def _make_service() -> IngestionService:
    """Construct a fresh IngestionService with a short timeout."""
    return IngestionService(article_repository=ArticleRepository(), timeout_seconds=1.0)


def _ok_handler(body: str) -> httpx.MockTransport:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=body)

    return httpx.MockTransport(handler)


@pytest.fixture
def patched_sleep(monkeypatch: pytest.MonkeyPatch) -> Iterator[AsyncMock]:
    """Patch ``asyncio.sleep`` inside the ingestion module (D5)."""
    mock = AsyncMock(return_value=None)
    monkeypatch.setattr("app.services.ingestion.asyncio.sleep", mock)
    yield mock


@pytest.fixture
def service() -> IngestionService:
    return IngestionService(article_repository=ArticleRepository(), timeout_seconds=1.0)


# ----------------------------------------------
# AC-001 / AC-002 / AC-003 / AC-005 — happy path
# ----------------------------------------------
async def test_ingest_persists_articles_with_utc_and_hash(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _make_service()
    _patch_async_client(monkeypatch, _ok_handler(_VALID_RSS))

    result = await service.ingest_google_news(db_session)

    assert result.status == "success"
    assert result.ingested_count == 3
    assert result.duplicate_count == 0
    assert result.failed_count == 0
    assert result.ingested_at.tzinfo is not None

    rows = (await db_session.execute(select(Article).order_by(Article.id))).scalars().all()
    assert len(rows) == 3

    by_title = {row.title: row for row in rows}
    assert set(by_title) == {
        "Central Bank Signals Rate Adjustments",
        "Tech Stocks Surge on Earnings Beat",
        "Oil Prices Dip on Supply Glut Concerns",
    }

    for row in rows:
        # AC-002 — SQLite stores UTC; on read the driver returns a naive
        # datetime because SQLite has no native tz-aware type. The stored
        # instant must equal the expected UTC value.
        published_utc = row.published_at.replace(tzinfo=UTC) if row.published_at.tzinfo is None else row.published_at.astimezone(UTC)
        assert published_utc.tzinfo is not None
        assert row.published_at_date == published_utc.date()
        assert row.published_at_date.isoformat() == published_utc.date().isoformat()

        # AC-003 — SHA-256 over normalized google_url
        expected_hash = hashlib.sha256(
            row.google_url.strip().encode("utf-8")
        ).hexdigest()
        assert row.url_hash == expected_hash
        assert len(row.url_hash) == 64

        # AC-005 — initial states + null downstream fields
        assert row.workflow_state == "Ingested"
        assert row.scraping_status == "PENDING"
        assert row.relevance_score is None
        assert row.relevance_reasoning is None
        assert row.resolved_url is None
        assert row.scraped_content is None
        assert row.financial_insight is None
        assert row.scraping_error is None