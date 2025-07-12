"""Integration tests for ``POST /api/v1/ingest``.

Exercises the FastAPI route mounted on ``app.main:app`` via the shared
``async_client`` fixture (``get_async_db`` overridden to ``db_session``).

Network I/O uses :class:`respx` for deterministic, offline responses.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Article


RSS_URL_DEFAULT_MATCH = "https://news.google.com/rss/search"

_RSS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Test</title>
  <link>https://news.google.com/</link>
  <description>Feed</description>
  <item>
    <title>{title}</title>
    <link>{link}</link>
    <pubDate>Mon, 21 Oct 2026 12:00:00 GMT</pubDate>
    <source url="https://example.com">Reuters</source>
  </item>
</channel>
</rss>
"""


def _rss(title: str = "Test Headline", link: str = "https://news.google.com/rss/articles/1") -> str:
    return _RSS_TEMPLATE.format(title=title, link=link)

# ----------
# Happy path
# ----------
async def test_ingest_returns_200_and_persists_rows(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get(url__startswith=RSS_URL_DEFAULT_MATCH).mock(
            return_value=httpx.Response(200, text=_rss())
        )
        response = await async_client.post("/api/v1/ingest", json={})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert body["ingested_count"] == 1
    assert body["duplicate_count"] == 0
    assert body["failed_count"] == 0
    assert body["ingested_at"].endswith("Z") or "+" in body["ingested_at"]

    rows = (await db_session.execute(select(Article))).scalars().all()
    assert len(rows) == 1
    assert rows[0].workflow_state == "Ingested"
    assert rows[0].scraping_status == "PENDING"


async def test_ingest_accepts_empty_body(
    async_client: AsyncClient,
) -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get(url__startswith=RSS_URL_DEFAULT_MATCH).mock(
            return_value=httpx.Response(200, text=_rss())
        )
        response = await async_client.post("/api/v1/ingest")

    assert response.status_code == 200, response.text


async def test_ingest_honors_feed_url_override(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    override_url = "https://example.com/custom/feed.xml"

    # assert_all_called=False: the default route is registered specifically to
    # prove it is NOT called; we assert that explicitly below.
    with respx.mock(assert_all_called=False) as router:
        override_route = router.get(override_url).mock(
            return_value=httpx.Response(
                200, 
                text=_rss(
                    title="Override Title", 
                    link="https://news.google.com/rss/articles/OVR"
                )
            )
        )
        default_route = router.get(url__startswith=RSS_URL_DEFAULT_MATCH).mock(
            return_value=httpx.Response(200, text=_rss())
        )

        response = await async_client.post(
            "/api/v1/ingest", json={"feed_url": override_url}
        )

    assert response.status_code == 200, response.text
    assert override_route.called is True
    assert default_route.called is False

    rows = (await db_session.execute(select(Article))).scalars().all()
    assert len(rows) == 1
    assert rows[0].title == "Override Title"


# ----------------------------------------
# AC-004 — re-ingesting returns duplicates
# ----------------------------------------
async def test_reingest_reports_duplicates(
    async_client: AsyncClient,
) -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get(url__startswith=RSS_URL_DEFAULT_MATCH).mock(
            return_value=httpx.Response(200, text=_rss())
        )
        first = await async_client.post("/api/v1/ingest", json={})
        second = await async_client.post("/api/v1/ingest", json={})

    assert first.status_code == 200
    assert first.json()["ingested_count"] == 1

    assert second.status_code == 200
    second_body = second.json()
    assert second_body["ingested_count"] == 0
    assert second_body["duplicate_count"] == 1


# ------------------------------------------------
# AC-007 — HTTP 502 on exhausted upstream failures
# ------------------------------------------------
async def test_ingest_returns_502_when_feed_unreachable(
    async_client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Retries would otherwise take 4s; patch sleep to keep the test fast.
    from unittest.mock import AsyncMock

    monkeypatch.setattr(
        "app.services.ingestion.asyncio.sleep", AsyncMock(return_value=None)
    )

    with respx.mock(assert_all_called=False) as router:
        route = router.get(url__startswith=RSS_URL_DEFAULT_MATCH).mock(
            return_value=httpx.Response(503, text="unavailable")
        )
        response = await async_client.post("/api/v1/ingest", json={})

    assert response.status_code == 502, response.text
    assert route.call_count == 3  # 1 attempt + 2 retries

    body = response.json()
    assert body["error_code"] == "EXTERNAL_SERVICE_ERROR"
    assert "detail" in body

    assert (await db_session.execute(select(Article))).scalars().all() == []