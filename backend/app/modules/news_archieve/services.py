import logging
from datetime import date
from typing import Sequence

from fastapi import HTTPException, status

from app.integrations.adapters import GoogleRSSAdapter
from app.modules.news_archieve.constants import ArticleLocale
from app.modules.news_archieve.schemas import ArchiveCountItem, ArchiveCountsResponse, DailyNewsResponse, NewsArticleResponse
from app.modules.news_archieve.cache import archive_counts_cache
from app.modules.news_archieve.utils import parse_month, build_utc_day_bounds
from app.modules.news_archieve.repositories import ArchiveCountRow, NewsArchieveRepo

logger = logging.getLogger(__name__)


class NewsArchieveService:
    """Business logic for news ingestion and archival."""

    def __init__(
        self,
        repo: NewsArchieveRepo,
        rss_adapter: GoogleRSSAdapter,
    ):
        self.repo = repo
        self.rss_adapter = rss_adapter

    # === PUBLIC METHODS ===

    def get_archive_counts(
        self,
        *,
        month: str,
        locale: ArticleLocale,
    ) -> ArchiveCountsResponse:
        """
        Return per-day article counts for the given month and locale.
        Falls back to RSS ingestion when the DB has no rows for the window.
        """
        # 1. Validate month
        try:
            start, end = parse_month(month)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        cache_key = (month, locale.value)

        # 2. Cache lookup (failure falls back to DB)
        cached = self._safe_cache_get(cache_key)
        if cached is not None:
            logger.info("Archive counts cache HIT for %s", cache_key)
            return cached

        logger.info("Archive counts cache MISS for %s", cache_key)

        # 3. DB query
        rows = self._query_counts(locale=locale, start=start, end=end)

        # 4. Empty → ingest from RSS, then re-query
        if not rows:
            logger.info(
                "No rows for month=%s locale=%s; ingesting from RSS", month, locale.value
            )
            self._ingest_from_rss(locale=locale)
            rows = self._query_counts(locale=locale, start=start, end=end)

        # 5. Build response (exclude zero-count dates — grouped query already does)
        counts = [
            ArchiveCountItem(date=row_day if isinstance(row_day, date) else row_day.date(), total=total)
            for row_day, total in rows
            if total > 0
        ]
        counts.sort(key=lambda item: item.date, reverse=True)

        response = ArchiveCountsResponse(
            month=month,
            locale=locale,
            counts=counts,
        )

        # 6. Cache write (best-effort)
        self._safe_cache_set(cache_key, response)

        return response

    def get_news_by_published_date(
        self,
        published_date: date,
        locale: ArticleLocale,
    ) -> DailyNewsResponse:
        """
        Retrieve all articles published on a given UTC calendar date,
        scoped to a locale, wrapped in a daily envelope.

        Args:
            published_date: The UTC date to filter articles by.
            locale: Target locale (e.g. ArticleLocale.ID).

        Returns:
            A DailyNewsResponse containing the queried date and the
            list of articles published that day, newest first.
        """
        start_date, end_date = build_utc_day_bounds(published_date)

        rows = self.repo.get_all_by_published_date(
            start_date=start_date,
            end_date=end_date,
            locale=locale.value,
        )

        items = [
            NewsArticleResponse(
                id=row.id,
                title=row.title,
                source=row.source,
                published_at=row.published_at,
                link=row.link,
                locale=row.locale,
                score=row.relevance_score,
                reason=row.relevance_reason,
            )
            for row in rows
        ]

        return DailyNewsResponse(date=published_date, items=items)

    # === PRIVATE METHODS ===

    def _query_counts(
        self,
        *,
        locale: ArticleLocale,
        start,
        end,
    ) -> Sequence[ArchiveCountRow]:
        try:
            return self.repo.get_archive_counts(locale=locale, start=start, end=end)
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                "DB failure while querying archive counts (locale=%s, %s..%s): %s",
                locale.value,
                start,
                end,
                exc,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve archive counts.",
            ) from exc

    def _ingest_from_rss(self, *, locale: ArticleLocale) -> None:
        try:
            articles = self.rss_adapter.to_articles(locale=locale.value)
            self.repo.insert_articles(articles)
        except Exception as exc:
            logger.error("RSS ingestion failed for locale=%s: %s", locale.value, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to ingest news articles.",
            ) from exc

    @staticmethod
    def _safe_cache_get(key) -> ArchiveCountsResponse | None:
        try:
            return archive_counts_cache.get(key)
        except Exception as exc:
            logger.warning("Cache read failure for key=%s: %s", key, exc)
            return None

    @staticmethod
    def _safe_cache_set(key, value: ArchiveCountsResponse) -> None:
        try:
            archive_counts_cache[key] = value
        except Exception as exc:
            logger.warning("Cache write failure for key=%s: %s", key, exc)