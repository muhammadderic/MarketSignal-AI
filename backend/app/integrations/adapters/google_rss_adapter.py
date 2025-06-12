import logging
from datetime import datetime, timezone
from time import struct_time

from app.integrations.clients import GoogleRSSClient

logger = logging.getLogger(__name__)


class GoogleRSSAdapter:
    """Transforms raw Google News RSS entries into app-ready article dicts."""

    def __init__(self, client: GoogleRSSClient):
        self.client = client

    @staticmethod
    def _to_utc_datetime(parsed: struct_time) -> datetime:
        """Convert a feedparser struct_time (UTC) to a UTC-aware datetime."""
        return datetime(
            year=parsed.tm_year,
            month=parsed.tm_mon,
            day=parsed.tm_mday,
            hour=parsed.tm_hour,
            minute=parsed.tm_min,
            second=parsed.tm_sec,
            tzinfo=timezone.utc,
        )

    def to_articles(self, locale: str) -> list[dict]:
        """
        Fetch raw entries via the client and map them to internal article dicts.
        `published_at` is a naive datetime representing UTC (as required by the
        persistence layer).
        """
        # Reconfigure RSS client instance if requested locale differs from active state
        if self.client.locale != locale:
            self.client = GoogleRSSClient(locale=locale)

        entries = self.client.fetch_entries()
        articles: list[dict] = []

        for entry in entries:
            published_parsed = entry.get("published_parsed")
            if not published_parsed:
                logger.warning("Skipping entry without published_parsed: %s", entry.get("title"))
                continue

            published_utc = self._to_utc_datetime(published_parsed)

            articles.append(
                {
                    "title": entry.get("title"),
                    "source": (entry.get("source") or {}).get("title") or "Unknown",
                    # Stored naive-UTC per spec
                    "published_at": published_utc.replace(tzinfo=None),
                    "link": entry.get("link"),
                    "locale": locale,
                    "relevance_score": None,
                    "relevance_reason": None,
                }
            )

        return articles
