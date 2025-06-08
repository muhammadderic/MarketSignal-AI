"""
External API contract tests for GoogleRSSClient.

These tests hit the REAL Google News RSS endpoint to verify the live
contract still matches what `GoogleRSSClient.fetch_feed()` expects.

Run them explicitly:
    pytest tests/external -m external -v

Exclude them from the normal suite:
    pytest -m "not external"
"""
import pytest
import httpx
import feedparser

from app.integrations.clients import GoogleRSSClient


pytestmark = pytest.mark.external


# ---------- Contract: raw HTTP endpoint ----------

@pytest.mark.parametrize("locale", ["ID", "US"])
def test_google_rss_endpoint_is_reachable_and_returns_xml(locale):
    """The URL our client builds must return 200 + XML-like content."""
    client = GoogleRSSClient(locale=locale)
    url = f"{client.BASE_URL}?{client.locale_params}"

    response = httpx.get(url, timeout=15.0, follow_redirects=True)

    assert response.status_code == 200, (
        f"Google RSS returned {response.status_code} for locale={locale}"
    )
    content_type = response.headers.get("content-type", "")
    assert "xml" in content_type.lower() or response.text.lstrip().startswith("<?xml"), (
        f"Unexpected content-type for locale={locale}: {content_type}"
    )
    # Sanity: the body must actually contain an RSS document
    assert "<rss" in response.text[:2000].lower()


# ---------- Contract: feedparser output shape ----------

@pytest.mark.parametrize("locale", ["ID", "US"])
def test_fetch_feed_returns_expected_shape(locale):
    """fetch_feed() must return {'feed': ..., 'entries': [...]} with non-empty entries."""
    client = GoogleRSSClient(locale=locale)

    result = client.fetch_feed()

    # Top-level contract
    assert isinstance(result, dict)
    assert set(result.keys()) >= {"feed", "entries"}

    feed = result["feed"]
    entries = result["entries"]

    # feed metadata
    assert feed is not None
    assert "title" in feed, "RSS <channel> is missing <title>"
    assert "link" in feed, "RSS <channel> is missing <link>"

    # entries
    assert isinstance(entries, list)
    assert len(entries) > 0, f"Google RSS returned zero entries for locale={locale}"

    # Each entry must expose the fields our NewsService depends on
    first = entries[0]
    for field in ("title", "link"):
        assert field in first, f"Entry missing required field: {field}"
        assert first[field], f"Entry field '{field}' is empty for locale={locale}"


# ---------- Contract: locale routing ----------

def test_id_and_us_locales_return_different_feeds():
    """Different locales must produce different URLs and (usually) different feeds."""
    id_client = GoogleRSSClient(locale="ID")
    us_client = GoogleRSSClient(locale="US")

    assert id_client.locale_params != us_client.locale_params
    assert "gl=ID" in id_client.locale_params
    assert "gl=US" in us_client.locale_params

    id_feed = id_client.fetch_feed()
    us_feed = us_client.fetch_feed()

    assert id_feed["feed"]["title"] != us_feed["feed"]["title"] or \
           id_feed["entries"][0]["link"] != us_feed["entries"][0]["link"], (
        "ID and US locales returned identical content — locale routing may be broken."
    )


# ---------- Contract: raw parse parity (feedparser vs client) ----------

def test_client_output_matches_direct_feedparser_parse():
    """
    Guards against accidental drift: our client should return exactly what
    feedparser produces for the same URL (no silent truncation/reshaping).
    """
    client = GoogleRSSClient(locale="ID")
    url = f"{client.BASE_URL}?{client.locale_params}"

    raw = feedparser.parse(url)
    via_client = client.fetch_feed()

    assert len(via_client["entries"]) == len(raw.entries)
    assert via_client["feed"].get("title") == raw.feed.get("title")


# ---------- Contract: unsupported locale ----------

def test_unsupported_locale_raises_before_any_network_call():
    """Bad locale must fail fast with HTTP 400, no HTTP request needed."""
    with pytest.raises(Exception) as exc_info:
        GoogleRSSClient(locale="XX")

    # FastAPI HTTPException has .status_code
    assert getattr(exc_info.value, "status_code", None) == 400