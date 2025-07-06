"""RSS feed ingestion domain service.

Implements FEAT-001:
    * Asynchronous fetch via ``httpx.AsyncClient`` (15s timeout, 2 retries on
      transport/5xx).
    * ``feedparser`` XML parsing with per-entry fault isolation (ARC-006).
    * UTC timestamp normalization (ARC-004).
    * SHA-256 ``url_hash`` derivation from normalized ``google_url``.
    * Batch persistence via :class:`ArticleRepository` using
      ``ON CONFLICT DO NOTHING``.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, Iterable

import feedparser
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.error_handlers import ExternalServiceError
from app.db.repositories.article_repository import ArticleRepository
from app.schemas.ingestion import ArticleIngestResponse

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 15.0
_MAX_FETCH_ATTEMPTS = 3  # initial attempt + 2 retries (R-007)
_RETRY_DELAY_SECONDS = 2.0


class IngestionService:
    """Orchestrates fetch → parse → normalize → persist for RSS feeds."""

    def __init__(
        self,
        article_repository: ArticleRepository,
        timeout_seconds: float | None = None,
    ) -> None:
        self._repo = article_repository
        self._timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else float(getattr(settings, "GOOGLE_RSS_TIMEOUT_SECONDS", _DEFAULT_TIMEOUT_SECONDS))
        )

    async def ingest_google_news(
        self,
        db: AsyncSession,
        feed_url_override: str | None = None,
    ) -> ArticleIngestResponse:
        """Fetch, parse, normalize, and persist new articles.

        Args:
            db: Active async session.
            feed_url_override: Optional URL override for this run.

        Returns:
            ArticleIngestResponse with ingestion metrics.

        Raises:
            ExternalServiceError: If the feed cannot be retrieved (network /
                HTTP 5xx after retries) or XML cannot be parsed.
        """
        feed_url = feed_url_override or settings.GOOGLE_NEWS_RSS_URL
        logger.info(
            "RSS ingestion starting",
            extra={"context": {"feed_url": feed_url, "timeout_s": self._timeout_seconds}},
        )

        raw_xml = await self._fetch_rss_xml(feed_url)
        parsed = self._parse_xml(raw_xml)

        candidates: list[dict[str, Any]] = []
        failed_count = 0
        for entry in parsed.entries:
            candidate = self._normalize_entry(entry)
            if candidate is None:
                failed_count += 1
                continue
            candidates.append(candidate)

        hashes = [c["url_hash"] for c in candidates]
        inserted_count = await self._repo.insert_unique(db, candidates)
        duplicate_count = len(candidates) - inserted_count

        if candidate_hashes_pre_exist := await self._repo.count_existing_hashes(db, hashes):
            logger.debug(
                "Pre-existing hashes detected",
                extra={"context": {"pre_existing": len(candidate_hashes_pre_exist)}},
            )

        response = ArticleIngestResponse(
            ingested_count=inserted_count,
            duplicate_count=duplicate_count,
            failed_count=failed_count,
        )
        logger.info(
            "RSS ingestion completed",
            extra={
                "context": {
                    "entries_total": len(parsed.entries),
                    "ingested_count": inserted_count,
                    "duplicate_count": duplicate_count,
                    "failed_count": failed_count,
                }
            },
        )
        return response

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _fetch_rss_xml(self, feed_url: str) -> str:
        """Fetch RSS XML with up to 2 retries on transport/5xx failures."""
        last_error: Exception | None = None
        for attempt in range(1, _MAX_FETCH_ATTEMPTS + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.get(
                        feed_url,
                        headers={"User-Agent": "MarketSignalAI/1.0 (+http://localhost)"},
                        follow_redirects=True,
                    )
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"RSS feed returned HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                return response.text
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt >= _MAX_FETCH_ATTEMPTS:
                    break
                logger.warning(
                    "RSS fetch attempt failed, retrying",
                    extra={
                        "context": {
                            "attempt": attempt,
                            "feed_url": feed_url,
                            "error": str(exc),
                        }
                    },
                )
                await asyncio.sleep(_RETRY_DELAY_SECONDS)

        raise ExternalServiceError(
            f"RSS feed unreachable after {_MAX_FETCH_ATTEMPTS} attempts: {last_error}",
            context={"feed_url": feed_url},
        )

    def _parse_xml(self, raw_xml: str) -> feedparser.FeedParserDict:
        """Parse RSS XML into a feedparser result; raise on fatal errors."""
        parsed = feedparser.parse(raw_xml)
        if getattr(parsed, "bozo", 0) and not parsed.entries:
            raise ExternalServiceError(
                "RSS feed returned unparseable XML with no entries",
                context={"bozo_exception": str(getattr(parsed, "bozo_exception", ""))},
            )
        return parsed

    def _normalize_entry(
        self, entry: feedparser.FeedParserDict
    ) -> dict[str, Any] | None:
        """Convert a feedparser entry into a normalized DB candidate.

        Returns:
            Dict of ORM column values, or ``None`` if required fields are
            missing/unparseable. Logs ``WARNING`` on rejection.
        """
        title = self._get_str(entry, "title")
        google_url = self._get_str(entry, "link")
        published_at = self._extract_published_at(entry)

        if not title or not google_url or published_at is None:
            logger.warning(
                "Skipping malformed RSS entry",
                extra={
                    "context": {
                        "title_present": bool(title),
                        "link_present": bool(google_url),
                        "published_at_present": published_at is not None,
                    }
                },
            )
            return None

        url_hash = hashlib.sha256(google_url.strip().encode("utf-8")).hexdigest()
        source_name = self._extract_source_name(entry)

        return {
            "google_url": google_url.strip(),
            "url_hash": url_hash,
            "title": title.strip(),
            "source_name": source_name,
            "published_at": published_at,
            "published_at_date": published_at.date(),
        }

    @staticmethod
    def _get_str(entry: feedparser.FeedParserDict, key: str) -> str:
        value = entry.get(key) if hasattr(entry, "get") else None
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _extract_source_name(entry: feedparser.FeedParserDict) -> str | None:
        source = entry.get("source") if hasattr(entry, "get") else None
        if isinstance(source, dict):
            name = source.get("title")
            if name:
                return str(name)
        # feedparser sometimes surfaces a flat ``source`` string.
        if isinstance(source, str) and source.strip():
            return source.strip()
        return None

    @staticmethod
    def _extract_published_at(
        entry: feedparser.FeedParserDict,
    ) -> datetime | None:
        """Return UTC-aware ``published_at``; ``None`` if unparseable.

        Prefers feedparser's already-UTC ``*_parsed`` struct to avoid host-TZ
        dependence (ARC-004).
        """
        for key in ("published_parsed", "updated_parsed", "created_parsed"):
            struct = getattr(entry, key, None)
            if struct is None:
                continue
            try:
                return datetime(*struct[:6], tzinfo=UTC)
            except (TypeError, ValueError):
                continue

        for key in ("published", "updated", "pubDate", "created"):
            raw = getattr(entry, key, None)
            if not raw:
                continue
            parsed = IngestionService._parse_rfc822(str(raw))
            if parsed is not None:
                return parsed

        return None

    @staticmethod
    def _parse_rfc822(raw: str) -> datetime | None:
        try:
            dt = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            return None
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)


__all__ = ["IngestionService"]


# Silence unused-import lint in some Ruff configs.
_ = (time, Iterable)