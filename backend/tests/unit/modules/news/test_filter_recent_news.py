"""
Unit tests for NewsService._filter_recent_news.

Two minimal contracts only:
    1. Returns data filtered correctly (only entries within the last 24h, up to now).
    2. Returned items contain ONLY the required properties.

Command:
    pytest tests/unit/modules/news/test_filter_recent_news.py -v
"""
from datetime import datetime, timedelta, timezone
from time import gmtime

import pytest

from app.modules.news.news_services import NewsService


# ---------- Helpers ----------

def _struct_time(dt: datetime):
    """Build a UTC struct_time the way feedparser produces published_parsed."""
    return gmtime(dt.timestamp())


def _make_entry(title: str, source_title: str, published_dt: datetime, link: str) -> dict:
    """Minimal feedparser-like entry with all properties the method may touch."""
    return {
        "title": title,
        "link": link,
        "published_parsed": _struct_time(published_dt),
        "source": {"href": "https://example.com", "title": source_title},
        # extra noise fields to prove the output drops them
        "summary": "<p>noise</p>",
        "id": "noise-id",
        "guidislink": False,
    }


@pytest.fixture
def service() -> NewsService:
    """Instantiate without wiring real repo/client — only the method under test is used."""
    return NewsService(repo=None, client=None)


# ---------- Contract 1: filtering is correct ----------

def test_filter_recent_news_keeps_only_entries_within_last_24h(service):
    now = datetime.now(timezone.utc)

    fresh = _make_entry("fresh", "Src A", now - timedelta(hours=1), "https://a")
    boundary_old = _make_entry("too old", "Src B", now - timedelta(days=2), "https://b")
    future = _make_entry("future", "Src C", now + timedelta(hours=1), "https://c")

    result = service._filter_recent_news([fresh, boundary_old, future])

    titles = [r["title"] for r in result]
    assert titles == ["fresh"], f"Expected only the fresh entry, got: {titles}"


# ---------- Contract 2: output has only required properties ----------

def test_filter_recent_news_returns_only_required_properties(service):
    now = datetime.now(timezone.utc)
    entry = _make_entry("hello", "Src A", now - timedelta(hours=2), "https://a")

    result = service._filter_recent_news([entry])

    assert len(result) == 1
    assert set(result[0].keys()) == {"title", "source", "published_parsed", "link"}

    item = result[0]
    assert item["title"] == "hello"
    assert item["source"] == "Src A"  # source is flattened to its title
    assert item["link"] == "https://a"
    assert item["published_parsed"] == entry["published_parsed"]

# ---------- Contract 3: start_date near 'now' still works ----------

def test_filter_recent_news_with_start_date_close_to_now(service):
    """
    When start_date is only ~30 minutes before 'now', the window shrinks to
    [now - 30min, now]. Entries inside that narrow window are kept; entries
    just outside it (older or future) are dropped.
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(minutes=30)

    inside = _make_entry("inside", "Src A", now - timedelta(minutes=10), "https://in")
    just_before = _make_entry("before", "Src B", now - timedelta(minutes=45), "https://b")
    future = _make_entry("future", "Src C", now + timedelta(minutes=5), "https://f")

    result = service._filter_recent_news(
        [inside, just_before, future],
        start_date=start_date,
    )

    titles = [r["title"] for r in result]
    assert titles == ["inside"], f"Expected only 'inside', got: {titles}"