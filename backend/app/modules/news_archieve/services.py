import logging
from datetime import date, datetime, timezone, timedelta
from calendar import timegm

from fastapi import HTTPException, status

from app.integrations.adapters import GoogleRSSAdapter
from app.shared.utils import to_utc_aware
from app.modules.news_archieve.constants import ArticleLocale, ARCHIVE_FRESHNESS_THRESHOLD_HOURS
from app.modules.news_archieve.cache import archive_counts_cache
from app.modules.news_archieve.schemas import (
    ArchiveCountItem, 
    ArchiveCountsResponse, 
    DailyNewsResponse, 
    NewsArticleResponse, 
    ArticleTitleData,
)
from app.modules.news_archieve.utils import parse_month, build_utc_day_bounds, extract_original_url
from app.modules.news_archieve.repositories import NewsArchieveRepo
from app.modules.news_scoring.ns_schemas import BatchScoringResponse
from app.modules.news_scraping.constants import LinkResolutionStatus

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

    # ======================
    # === PUBLIC METHODS ===
    # ======================

    # === READ ===
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

        # 3. Query daily archive counts and the newest publication timestamp.
        rows, newest_published_at = self.repo.get_archive_counts_with_latest_timestamp(locale=locale, start=start, end=end)

        # 4. Determine whether existing archive data is stale.
        should_ingest = False

        if newest_published_at is not None:
            # Refresh the archive when the newest publication is older than 5 hours.
            should_ingest = not self._is_archive_fresh(newest_published_at)

        # Also ingest when no archive counts exist for the requested month.
        if not rows:
            should_ingest = True

        if should_ingest:
            logger.info("Refreshing archive counts for month=%s locale=%s", month, locale.value)

            # Ingest RSS articles before retrieving the updated archive counts.
            self._ingest_from_rss(locale=locale, latest_date=newest_published_at)

            # Re-query daily counts after ingestion.
            rows = self.repo.get_archive_counts(
                locale=locale,
                start=start,
                end=end,
            )

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

    def get_titles_by_ids(self, article_ids: list[int]) -> list[ArticleTitleData]:
        """
        Retrieve article id-title pairs for the given IDs, skipping null titles.
        
        Args:
            article_ids: List of article IDs to look up.
            
        Returns:
            List of ArticleTitleData schemas for articles with non-null titles.
        """
        if not article_ids:
            return []
        
        rows = self.repo.get_id_title_pairs_by_ids(article_ids)
        
        return [
            ArticleTitleData(id=row.id, title=row.title)
            for row in rows
            if row.title is not None
        ]

    # === UPDATE ===
    def update_news_scores(
        self,
        scoring_response: BatchScoringResponse,
    ) -> None:
        """
        Persist LLM relevance scores and reasons back onto existing
        news rows, keyed by article id.

        This is a pure update path — no inserts, no upserts.

        Args:
            scoring_response: Parsed batch response from the scoring
                service. Each `ArticleScoreResult` carries the target
                `id` plus `relevance_score` and `relevance_reason`.

        Returns:
            None. Side effect: rows in `news_article_data` are updated.
        """
        if not scoring_response.results:
            return

        score_payload = [
            {
                "target_id": result.id,
                "relevance_score": result.relevance_score,
                "relevance_reason": result.relevance_reason,
            }
            for result in scoring_response.results
        ]

        self.repo.update_news_scores(score_payload)

    # =======================
    # === PRIVATE METHODS ===
    # =======================
    def _ingest_from_rss(self, *, locale: ArticleLocale, latest_date: datetime) -> None:
        try:
            articles = self.rss_adapter.to_articles(locale=locale.value)

            # Filter entries and extract only the fields required by the database.
            filtered_articles = self._filter_recent_news(
                feed_entries=articles,
                latest_date=latest_date,
            )

            # Add locale and default scoring fields before bulk insertion.
            article_dicts = [
                {
                    **article,
                    "locale": locale.value,
                    "relevance_score": None,
                    "relevance_reason": None,
                    "resolved_link": None,
                    "link_resolution_status": LinkResolutionStatus.PENDING,
                }
                for article in filtered_articles
            ]

            self.repo.insert_articles(article_dicts)
        except Exception as exc:
            logger.error("RSS ingestion failed for locale=%s: %s", locale.value, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to ingest news articles.",
            ) from exc

    def _is_archive_fresh(
        self,
        newest_published_at: datetime | None,
    ) -> bool:
        if newest_published_at is None:
            return False

        # Treat naive datetimes as UTC.
        if newest_published_at.tzinfo is None:
            newest_published_at = newest_published_at.replace(
                tzinfo=timezone.utc
            )

        age = datetime.now(timezone.utc) - newest_published_at
        return age <= timedelta(hours=ARCHIVE_FRESHNESS_THRESHOLD_HOURS)

    def _filter_recent_news(
        self,
        feed_entries: list[dict[str, any]],
        latest_date: datetime | None,
    ) -> list[dict[str, any]]:
        now = datetime.now(timezone.utc)
        latest_date = latest_date or (now - timedelta(days=1))

        filtered_entries = []

        for entry in feed_entries:
            published_at = entry.get("published_at")
            if not isinstance(published_at, datetime):
                continue

            published_at = to_utc_aware(published_at)

            if not latest_date < published_at <= now:
                continue

            raw_link = entry.get("link")

            filtered_entries.append(
                {
                    "title": entry["title"],
                    "source": entry["source"],
                    "published_at": published_at,
                    "link": extract_original_url(raw_link) if raw_link else None,
                }
            )

        return filtered_entries

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
