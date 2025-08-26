"""Publisher URL resolution service.

Decodes Google News URLs (``google_url``) into canonical publisher URLs
(``resolved_url``) using ``googlenewsdecoder``, which interrogates Google's
``batchexecute`` RPC endpoint (FEAT-005 v2 §3.4). Decoding is synchronous;
it is offloaded to a thread pool via ``asyncio.to_thread`` and bounded by
``asyncio.wait_for(timeout=settings.SCRAPER_TIMEOUT_SECONDS)`` (ARC-002).
Per-article failures are isolated (ARC-006) and batch decoding is throttled
by ``asyncio.Semaphore(5)`` (INTEGRATIONS.md).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

from googlenewsdecoder import gnewsdecoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Article
from app.db.repositories.article_repository import ArticleRepository
from app.schemas.resolver import (
    ArticleResolveItemResult,
    ArticleResolveURLResponse,
)

logger = logging.getLogger(__name__)

_CONCURRENCY_LIMIT = 5

# Small public-suffix-aware set covering common financial publishers.
# Fallback is ``<registrable-label>.<tld>`` → title-cased label.
_SECOND_LEVEL_SUFFIXES: frozenset[str] = frozenset(
    {
        "co.uk",
        "org.uk",
        "com.au",
        "net.au",
        "co.jp",
        "co.in",
        "com.br",
        "com.mx",
        "co.nz",
        "co.za",
    }
)

# Fixed seed mapping (Q6 option a). Domain → canonical display name.
_PUBLISHER_DISPLAY_NAMES: dict[str, str] = {
    "reuters.com": "Reuters",
    "bloomberg.com": "Bloomberg",
    "wsj.com": "The Wall Street Journal",
    "ft.com": "Financial Times",
    "cnbc.com": "CNBC",
    "cnn.com": "CNN",
    "nytimes.com": "The New York Times",
    "theguardian.com": "The Guardian",
    "bbc.com": "BBC",
    "bbc.co.uk": "BBC",
    "apnews.com": "Associated Press",
    "marketwatch.com": "MarketWatch",
    "barrons.com": "Barron's",
    "economist.com": "The Economist",
    "nikkei.com": "Nikkei",
    "asia.nikkei.com": "Nikkei Asia",
    "bisnis.com": "Bisnis.com",
    "kontan.co.id": "Kontan",
    "cnbcindonesia.com": "CNBC Indonesia",
    "antaranews.com": "Antara News",
}

# Generic source names eligible for normalization (Q7(b)).
_GENERIC_SOURCE_NAMES: frozenset[str] = frozenset({"google news"})


class ResolverService:
    """Batch resolution of Google News redirect URLs to publisher URLs."""

    def __init__(self, article_repo: ArticleRepository) -> None:
        self.article_repo = article_repo
        self._semaphore = asyncio.Semaphore(_CONCURRENCY_LIMIT)

    # --------------
    # --- PUBLIC ---
    # --------------

    async def resolve_article_urls_batch(
        self,
        db: AsyncSession,
        article_ids: list[int],
    ) -> ArticleResolveURLResponse:
        """Decode the URLs of the requested articles.

        Args:
            db: Active async session.
            article_ids: Requested article IDs (deduplicated inside).

        Returns:
            Aggregated :class:`ArticleResolveURLResponse`.
        """
        unique_ids = list(dict.fromkeys(article_ids))
        articles = await self.article_repo.get_by_ids(db, unique_ids)
        articles_by_id = {a.id: a for a in articles}

        results: list[ArticleResolveItemResult] = []
        pending: list[Article] = []

        for article_id in unique_ids:
            article = articles_by_id.get(article_id)
            if article is None:
                results.append(
                    ArticleResolveItemResult(
                        article_id=article_id,
                        status="FAILED",
                        error=f"Article ID {article_id} not found.",
                    )
                )
            else:
                pending.append(article)

        if pending:
            gathered = await asyncio.gather(
                *(self._resolve_one(article) for article in pending),
                return_exceptions=True,
            )
            for article, outcome in zip(pending, gathered):
                if isinstance(outcome, Exception):
                    logger.exception(
                        "Unexpected resolver failure for article %d",
                        article.id,
                        exc_info=outcome,
                    )
                    results.append(
                        ArticleResolveItemResult(
                            article_id=article.id,
                            status="FAILED",
                            error=f"Unexpected resolver error: {outcome}",
                        )
                    )
                else:
                    results.append(outcome)

        success_updates: list[dict[str, Any]] = [
            {
                "id": item.article_id,
                "resolved_url": item.resolved_url,
                "source_name": self._lookup_source_for_update(
                    articles_by_id[item.article_id], item.resolved_url or ""
                ),
            }
            for item in results
            if item.status == "SUCCESS" and item.resolved_url
        ]

        if success_updates:
            # DB failures must roll back and propagate (not become per-item
            # failures) so the global handler reports a 500 envelope.
            await self.article_repo.update_resolution_results(
                db, success_updates
            )

        return self._aggregate(results)

    # ---------------
    # --- PRIVATE ---
    # ---------------

    async def _resolve_one(
        self,
        article: Article,
    ) -> ArticleResolveItemResult:
        """Resolve a single article's ``google_url`` with fault isolation."""
        async with self._semaphore:
            resolved_url, error = await self._decode_url(article.google_url)

        if resolved_url is None:
            logger.info(
                "URL resolution failed",
                extra={
                    "context": {
                        "article_id": article.id,
                        "error": error,
                    }
                },
            )
            return ArticleResolveItemResult(
                article_id=article.id,
                status="FAILED",
                error=error or "Unknown resolution failure.",
            )

        return ArticleResolveItemResult(
            article_id=article.id,
            status="SUCCESS",
            resolved_url=resolved_url,
        )

    async def _decode_url(
        self,
        google_url: str,
    ) -> tuple[str | None, str | None]:
        """Decode a Google News URL via ``googlenewsdecoder.gnewsdecoder``.

        ``gnewsdecoder`` is synchronous and performs an internal
        ``batchexecute`` RPC; it is executed in a worker thread so the asyncio
        event loop remains non-blocking. The whole call is bounded by
        ``settings.SCRAPER_TIMEOUT_SECONDS`` in two complementary ways:

        * ``timeout=settings.SCRAPER_TIMEOUT_SECONDS`` passed to ``gnewsdecoder``
          so its internal HTTP call respects the budget.
        * ``asyncio.wait_for(..., timeout=settings.SCRAPER_TIMEOUT_SECONDS)``
          guarding the thread hop so a hung decoder cannot stall the batch.

        Returns:
            ``(resolved_url, None)`` on success; ``(None, error)`` on failure.
        """
        try:
            decoded = await asyncio.wait_for(
                asyncio.to_thread(
                    gnewsdecoder,
                    google_url,
                    interval=1,
                    timeout=float(settings.SCRAPER_TIMEOUT_SECONDS),
                ),
                timeout=settings.SCRAPER_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            return None, (
                f"Decoder timed out after "
                f"{settings.SCRAPER_TIMEOUT_SECONDS}s."
            )
        except ValueError as exc:
            return None, f"Decoder rejected the URL: {exc}"
        except Exception as exc:  # noqa: BLE001 — per-item fault isolation
            return None, f"Decoder error: {exc}"

        # Confirmed shape (googlenewsdecoder 0.2.2):
        #   {"success": True, "decoded_url": "https://..."}
        if not isinstance(decoded, dict):
            return None, "Decoder returned an unexpected payload."
        if not decoded.get("success"):
            return None, "Decoder reported failure."
        resolved = decoded.get("decoded_url")
        if not isinstance(resolved, str) or not resolved.strip():
            return None, "Decoder returned no URL."

        resolved = resolved.strip()
        scheme = urlparse(resolved).scheme.lower()
        if scheme not in ("http", "https"):
            return None, f"Decoded URL has unsupported scheme: {resolved}"

        return resolved, None

    @staticmethod
    def _lookup_source_for_update(
        article: Article,
        resolved_url: str,
    ) -> str | None:
        """Return a normalized publisher name or ``None`` if no change is needed.

        Only fill missing/generic ``source_name``; do not overwrite an existing
        meaningful value (R-006).
        """
        current = (article.source_name or "").strip()
        if current and current.lower() not in _GENERIC_SOURCE_NAMES:
            return None

        host = urlparse(resolved_url).hostname or ""
        if not host:
            return None
        return _derive_publisher_name(host)

    @staticmethod
    def _aggregate(
        results: list[ArticleResolveItemResult],
    ) -> ArticleResolveURLResponse:
        success = sum(1 for r in results if r.status == "SUCCESS")
        failed = sum(1 for r in results if r.status == "FAILED")
        return ArticleResolveURLResponse(
            processed_count=len(results),
            success_count=success,
            failed_count=failed,
            results=results,
        )

# ---------------
# --- HELPERS ---
# ---------------
def _derive_publisher_name(host: str) -> str | None:
    """Derive a display publisher name from a host string.

    Strips ``www.``, applies the fixed mapping, then falls back to the
    registrable label title-cased (``example.co.uk`` → ``"Example"``).
    """
    host = host.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return None

    if host in _PUBLISHER_DISPLAY_NAMES:
        return _PUBLISHER_DISPLAY_NAMES[host]

    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in _SECOND_LEVEL_SUFFIXES:
        label = parts[-3]
    elif len(parts) >= 2:
        label = parts[-2]
    else:
        label = parts[0]

    return label.replace("-", " ").title() or None