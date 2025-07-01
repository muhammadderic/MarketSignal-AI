"""Mock factories for Google News RSS XML payloads.

Used by unit and integration tests for the ingestion pipeline (TESTING_STRATEGY §2).
No live HTTP requests are performed; the returned XML is intended to be fed to
``feedparser`` or an ``httpx`` mock (``respx``).
"""

from __future__ import annotations

from xml.sax.saxutils import escape


def mock_rss_feed_xml(
    *,
    entries: list[dict[str, str]] | None = None,
    channel_title: str = "Google News",
) -> str:
    """Build a valid Google News RSS feed XML string.

    Args:
        entries: Each dict must contain ``title``, ``link``, ``pubDate``, and
            optionally ``source_name``. Defaults to one well-formed entry.
        channel_title: Channel title emitted in the ``<channel>`` block.

    Returns:
        A UTF-8-decodable RSS 2.0 XML document.
    """
    if entries is None:
        entries = [
            {
                "title": "Acme Corp reports record Q3 earnings",
                "link": "https://news.google.com/rss/articles/AAAA?oc=5",
                "pubDate": "Tue, 28 Oct 2026 12:00:00 GMT",
                "source_name": "Reuters",
            }
        ]

    items_xml = "\n".join(_render_item(e) for e in entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        f"    <title>{escape(channel_title)}</title>\n"
        "    <link>https://news.google.com/</link>\n"
        "    <description>Google News RSS</description>\n"
        f"    {items_xml}\n"
        "  </channel>\n"
        "</rss>\n"
    )


def mock_rss_feed_malformed_xml() -> str:
    """Return a truncated/invalid RSS XML string for negative-path tests."""
    return "<rss><channel><title>oops</title></channel"  # intentionally unterminated


def _render_item(entry: dict[str, str]) -> str:
    source = entry.get("source_name")
    source_xml = (
        f'<source url="https://example.com">{escape(source)}</source>' if source else ""
    )
    return (
        "<item>\n"
        f"  <title>{escape(entry['title'])}</title>\n"
        f"  <link>{escape(entry['link'])}</link>\n"
        f"  <pubDate>{escape(entry['pubDate'])}</pubDate>\n"
        f"  {source_xml}\n"
        "</item>"
    )