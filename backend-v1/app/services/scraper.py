"""Article content scraping service.

Fetches publisher HTML from each article's ``resolved_url`` using
``httpx.AsyncClient``, strips boilerplate with BeautifulSoup4, extracts
cleaned body paragraphs, and persists the result with per-item fault
isolation (ARC-006). Requests are throttled by ``asyncio.Semaphore(5)``
(INTEGRATIONS.md) and bounded by ``settings.SCRAPER_TIMEOUT_SECONDS`` with
one retry on connection reset / socket timeout.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Article, ScrapingStatus
from app.db.repositories.article_repository import ArticleRepository
from app.schemas.scraper import (
    ArticleScrapeResponse,
    ArticleScrapeResult,
)

logger = logging.getLogger(__name__)

_CONCURRENCY_LIMIT = 5
_MIN_CONTENT_LENGTH = 100
_RETRY_DELAY_SECONDS = 1.0

# Tags removed unconditionally before paragraph extraction (FR-013 / R-002).
_BOILERPLATE_TAGS = (
    "script",
    "style",
    "nav",
    "footer",
    "header",
    "aside",
    "iframe",
    "form",
    "noscript",
    "svg",
)

_WHITESPACE_RE = re.compile(r"[ \t\u00a0]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


class ScraperService:
    """Batch scraping of article content from resolved publisher URLs."""

    def __init__(self, article_repo: ArticleRepository) -> None:
        self.article_repo = article_repo
        self._semaphore = asyncio.Semaphore(_CONCURRENCY_LIMIT)

    # --------------
    # --- PUBLIC ---
    # --------------

    async def scrape_articles_batch(
        self,
        db: AsyncSession,
        article_ids: list[int],
    ) -> ArticleScrapeResponse:
        """Scrape the resolved URLs of the requested articles.

        Args:
            db: Active async session.
            article_ids: Requested article IDs (deduplicated inside).

        Returns:
            Aggregated :class:`ArticleScrapeResponse`.

        Raises:
            BadRequestError: If any requested article is missing or has a
                null ``resolved_url``. Raised by the endpoint layer before
                this method executes.
        """
        unique_ids = list(dict.fromkeys(article_ids))
        articles = await self.article_repo.get_by_ids(db, unique_ids)
        articles_by_id = {a.id: a for a in articles}

        results: list[ArticleScrapeResult] = []
        pending: list[Article] = []

        for article_id in unique_ids:
            article = articles_by_id.get(article_id)
            if article is None:
                results.append(
                    ArticleScrapeResult(
                        article_id=article_id,
                        scraping_status=ScrapingStatus.FAILED,
                        error=f"Article ID {article_id} not found.",
                    )
                )
            else:
                pending.append(article)

        # Mark in-progress atomically per item, then execute concurrently.
        if pending:
            await self._mark_in_progress(db, [a.id for a in pending])

            gathered = await asyncio.gather(
                *(self._scrape_one(article) for article in pending),
                return_exceptions=True,
            )
            for article, outcome in zip(pending, gathered):
                if isinstance(outcome, Exception):
                    logger.exception(
                        "Unexpected scraper failure for article %d",
                        article.id,
                        exc_info=outcome,
                    )
                    results.append(
                        ArticleScrapeResult(
                            article_id=article.id,
                            scraping_status=ScrapingStatus.FAILED,
                            error=f"Unexpected scraper error: {outcome}",
                        )
                    )
                else:
                    results.append(outcome)

        # Persist outcomes. DB failures must roll back and propagate (500).
        success_updates: list[dict[str, Any]] = []
        failure_updates: list[dict[str, Any]] = []
        for item in results:
            if item.scraping_status == ScrapingStatus.SUCCESS:
                success_updates.append(
                    {
                        "id": item.article_id,
                        "scraped_content": item._content,  # type: ignore[attr-defined]
                    }
                )
            elif item.scraping_status == ScrapingStatus.FAILED and item.error:
                failure_updates.append(
                    {"id": item.article_id, "error": item.error}
                )

        if success_updates:
            await self.article_repo.update_scraping_results(
                db, success_updates
            )
        if failure_updates:
            await self.article_repo.update_scraping_failures(
                db, failure_updates
            )

        return self._aggregate(results)

    # ---------------
    # --- PRIVATE ---
    # ---------------

    async def _mark_in_progress(
        self, db: AsyncSession, article_ids: list[int]
    ) -> None:
        """Transition each article to ``IN_PROGRESS`` before fetching."""
        await self.article_repo.mark_scraping_in_progress(db, article_ids)

    async def _scrape_one(
        self, article: Article
    ) -> ArticleScrapeResult:
        """Scrape a single article's ``resolved_url`` with fault isolation."""
        async with self._semaphore:
            html, error = await self._fetch_html(article.resolved_url or "")

        if html is None:
            logger.info(
                "Scraping failed",
                extra={
                    "context": {
                        "article_id": article.id,
                        "error": error,
                    }
                },
            )
            return ArticleScrapeResult(
                article_id=article.id,
                scraping_status=ScrapingStatus.FAILED,
                error=error or "Unknown scraping failure.",
            )

        cleaned = self.clean_html(html)
        if len(cleaned) < _MIN_CONTENT_LENGTH:
            return ArticleScrapeResult(
                article_id=article.id,
                scraping_status=ScrapingStatus.FAILED,
                error=(
                    f"Extracted text too short ({len(cleaned)} chars, "
                    f"minimum {_MIN_CONTENT_LENGTH}). Page may be a paywall, "
                    f"CAPTCHA, or JS-only rendered."
                ),
            )

        result = ArticleScrapeResult(
            article_id=article.id,
            scraping_status=ScrapingStatus.SUCCESS,
            scraped_content_length=len(cleaned),
        )
        # Attach cleaned text for persistence without expanding the public
        # response schema.
        result._content = cleaned  # type: ignore[attr-defined]
        return result

    async def _fetch_html(
        self, url: str
    ) -> tuple[str | None, str | None]:
        """Fetch HTML with one retry on connection reset / socket timeout.

        Returns:
            ``(html, None)`` on success; ``(None, error)`` on failure.
        """
        if not url:
            return None, "Article has no resolved_url."

        headers = {"User-Agent": settings.SCRAPER_USER_AGENT}
        timeout = httpx.Timeout(settings.SCRAPER_TIMEOUT_SECONDS)

        last_error: str | None = None
        for attempt in range(2):  # 1 initial + 1 retry
            try:
                async with httpx.AsyncClient(
                    timeout=timeout,
                    follow_redirects=True,
                    headers=headers,
                ) as client:
                    response = await client.get(url)
            except (httpx.ConnectError, httpx.ReadTimeout) as exc:
                last_error = f"Connection error: {exc}"
                if attempt == 0:
                    await asyncio.sleep(_RETRY_DELAY_SECONDS)
                    continue
                return None, last_error
            except httpx.HTTPError as exc:
                return None, f"HTTP client error: {exc}"
            except Exception as exc:  # noqa: BLE001 — per-item fault isolation
                return None, f"Unexpected fetch error: {exc}"

            if response.status_code >= 400:
                return None, (
                    f"HTTP {response.status_code} {response.reason_phrase}"
                )
            return response.text, None

        return None, last_error or "Unknown fetch failure."

    # --------------
    # --- HELPERS ---
    # --------------

    @staticmethod
    def clean_html(html_content: str) -> str:
        """Strip boilerplate and extract clean paragraph text.

        Removes script/style/nav/footer/header/aside/iframe/form and similar
        non-content tags (R-002), extracts paragraphs from ``<p>`` and
        ``<article>`` tags, joins with double newlines, and normalizes
        whitespace.

        Args:
            html_content: Raw HTML string.

        Returns:
            Cleaned plain text; empty string if no content could be extracted.
        """
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, "html.parser")

        for tag_name in _BOILERPLATE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        paragraphs: list[str] = []
        for element in soup.find_all(["p", "article"]):
            text = element.get_text(" ", strip=True)
            if not text:
                continue
            # Normalize intra-paragraph whitespace.
            text = _WHITESPACE_RE.sub(" ", text).strip()
            if text:
                paragraphs.append(text)

        joined = "\n\n".join(paragraphs)
        return _MULTI_NEWLINE_RE.sub("\n\n", joined).strip()

    @staticmethod
    def _aggregate(
        results: list[ArticleScrapeResult],
    ) -> ArticleScrapeResponse:
        success = sum(
            1 for r in results if r.scraping_status == ScrapingStatus.SUCCESS
        )
        failed = sum(
            1 for r in results if r.scraping_status == ScrapingStatus.FAILED
        )
        return ArticleScrapeResponse(
            processed_count=len(results),
            success_count=success,
            failed_count=failed,
            results=results,
        )