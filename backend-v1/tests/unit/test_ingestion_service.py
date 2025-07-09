"""Unit tests for :class:`app.services.ingestion.IngestionService`.

Covers FEAT-001 acceptance criteria:

* AC-001 — RSS XML fetched and parsed into Article rows.
* AC-002 — UTC normalization of ``published_at`` + ``published_at_date``.
* AC-003 — SHA-256 ``url_hash`` derived from ``google_url``.
* AC-004 — duplicates via ``url_hash`` and ``(title, published_at_date)``
  do not insert new rows.
* AC-005 — initial states are ``Ingested`` / ``PENDING`` with null fields.
* AC-007 — retries on transport/5xx; HTTP 502 after exhaustion.
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

from app.core.error_handlers import ExternalServiceError
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


# Snapshot the real class once; the ingestion module references the same
# ``httpx`` object, so ``setattr`` on ``app.services.ingestion.httpx`` mutates
# the global ``httpx`` module attribute.
_REAL_ASYNC_CLIENT = httpx.AsyncClient


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

    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        # Ignore the service's timeout kwarg; MockTransport does not need it.
        del args, kwargs
        # return real_async_client(transport=handler)
        return _REAL_ASYNC_CLIENT(transport=handler)

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


async def test_ingest_normalizes_timestamp_to_utc(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-UTC RFC-822 pubDate must be converted, not truncated."""
    service = _make_service()
    rss = _build_rss(
        _item(
            title="Offset Feed Entry",
            link="https://news.google.com/rss/articles/CBMiOFF",
            pub_date="Mon, 21 Oct 2026 14:30:00 +0530",
        )
    )
    _patch_async_client(monkeypatch, _ok_handler(rss))

    result = await service.ingest_google_news(db_session)
    assert result.ingested_count == 1

    row = (await db_session.execute(select(Article))).scalar_one()
    expected = datetime(2026, 10, 21, 9, 0, 0, tzinfo=UTC)  # 14:30 +0530 → 09:00 UTC
    stored = row.published_at.replace(tzinfo=UTC) if row.published_at.tzinfo is None else row.published_at.astimezone(UTC)
    assert stored == expected
    assert row.published_at_date.isoformat() == "2026-10-21"


# --------------------------------------------------------------
# AC-004 — dedup via url_hash and via (title, published_at_date)
# --------------------------------------------------------------
async def test_duplicate_url_hash_is_skipped(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _make_service()
    _patch_async_client(monkeypatch, _ok_handler(_VALID_RSS))
    first = await service.ingest_google_news(db_session)
    assert first.ingested_count == 3

    # Second run, identical feed → all duplicates by url_hash
    second = await service.ingest_google_news(db_session)
    assert second.ingested_count == 0
    assert second.duplicate_count == 3
    assert second.failed_count == 0

    total = (await db_session.execute(select(Article))).scalars().all()
    assert len(total) == 3


async def test_composite_title_date_duplicate_is_skipped(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Different URL, same (title, published_at_date) → composite constraint."""
    service = _make_service()
    first_rss = _build_rss(
        _item(
            title="Same Headline",
            link="https://news.google.com/rss/articles/A",
            pub_date="Mon, 21 Oct 2026 08:00:00 GMT",
        )
    )
    _patch_async_client(monkeypatch, _ok_handler(first_rss))
    assert (await service.ingest_google_news(db_session)).ingested_count == 1

    second_rss = _build_rss(
        _item(
            title="Same Headline",
            link="https://news.google.com/rss/articles/B",  # different url_hash
            pub_date="Mon, 21 Oct 2026 20:00:00 GMT",  # same UTC date
        )
    )
    _patch_async_client(monkeypatch, _ok_handler(second_rss))
    second = await service.ingest_google_news(db_session)

    assert second.ingested_count == 0
    assert second.duplicate_count == 1
    assert second.failed_count == 0

    rows = (await db_session.execute(select(Article))).scalars().all()
    assert len(rows) == 1
    assert rows[0].google_url.endswith("/A")
    

async def test_mixed_batch_partial_duplicates(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Batch mixing new rows and an existing url_hash."""
    service = _make_service()
    first_rss = _build_rss(
        _item(
            title="Existing Article",
            link="https://news.google.com/rss/articles/EXIST",
            pub_date="Mon, 21 Oct 2026 09:00:00 GMT",
        )
    )
    _patch_async_client(monkeypatch, _ok_handler(first_rss))
    first = await service.ingest_google_news(db_session)
    assert first.ingested_count == 1

    mixed_rss = _build_rss(
        _item(
            title="Existing Article",
            link="https://news.google.com/rss/articles/EXIST",
            pub_date="Mon, 21 Oct 2026 09:00:00 GMT",
        ),
        _item(
            title="Fresh Article A",
            link="https://news.google.com/rss/articles/NEWA",
            pub_date="Tue, 22 Oct 2026 07:00:00 GMT",
        ),
        _item(
            title="Fresh Article B",
            link="https://news.google.com/rss/articles/NEWB",
            pub_date="Tue, 22 Oct 2026 08:00:00 GMT",
        ),
    )
    _patch_async_client(monkeypatch, _ok_handler(mixed_rss))
    result = await service.ingest_google_news(db_session)

    assert result.ingested_count == 2
    assert result.duplicate_count == 1
    assert result.failed_count == 0
    assert len((await db_session.execute(select(Article))).scalars().all()) == 3
    

# ----------------------------
# AC-007 — retries + final 502
# ----------------------------
async def test_retries_twice_then_succeeds(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    patched_sleep: AsyncMock,
) -> None:
    service = _make_service()
    calls: list[int] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) < 3:  # fail first two, then succeed
            return httpx.Response(500, text="upstream error")
        return httpx.Response(200, text=_VALID_RSS)

    _patch_async_client(monkeypatch, httpx.MockTransport(handler))

    result = await service.ingest_google_news(db_session)

    assert result.ingested_count == 3
    assert len(calls) == 3
    assert patched_sleep.await_count == 2  # 2 retries between 3 attempts
    assert patched_sleep.await_args is not None
    assert patched_sleep.await_args.args == (2.0,)


async def test_exhausted_retries_raise_external_service_error(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    patched_sleep: AsyncMock,
) -> None:
    service = _make_service()
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    _patch_async_client(monkeypatch, httpx.MockTransport(handler))

    with pytest.raises(ExternalServiceError) as excinfo:
        await service.ingest_google_news(db_session)

    assert excinfo.value.status_code == 502
    assert excinfo.value.error_code == "EXTERNAL_SERVICE_ERROR"
    assert patched_sleep.await_count == 2
    assert (await db_session.execute(select(Article))).scalars().all() == []


async def test_network_transport_error_triggers_retries(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    patched_sleep: AsyncMock,
) -> None:
    service = _make_service()
    calls: list[int] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        raise httpx.ConnectError("boom")

    _patch_async_client(monkeypatch, httpx.MockTransport(handler))

    with pytest.raises(ExternalServiceError):
        await service.ingest_google_news(db_session)

    assert len(calls) == 3
    assert patched_sleep.await_count == 2


async def test_feed_url_override_is_used(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _make_service()
    captured: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(str(request.url))
        return httpx.Response(200, text=_VALID_RSS)

    _patch_async_client(monkeypatch, httpx.MockTransport(handler))

    override = "https://news.google.com/rss/search?q=override"
    await service.ingest_google_news(db_session, feed_url_override=override)

    assert captured == [override]