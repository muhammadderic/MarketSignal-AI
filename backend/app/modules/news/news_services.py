import logging
from calendar import timegm
from datetime import date, datetime, timedelta, timezone
from typing import Sequence
from fastapi import HTTPException, status
from cachetools.func import ttl_cache

from app.integrations.clients.google_rss_client import GoogleRSSClient
from app.modules.news.news_constants import ArticleLocale
from app.modules.news.news_schemas import (
    ArticleTitleData,
    NewsFeedResponse, 
    NewsArticle,
    DateMetadataSchema,
    NewsArticleResponse
)
from app.modules.news.news_utils import (
    extract_original_url,
    is_data_fresh,
    get_max_age_cutoff,
    validate_locale
)
from app.modules.news.news_repo import NewsRepository, NewsDateSummaryRow
from app.modules.news_scoring.ns_schemas import BatchScoringResponse

logger = logging.getLogger(__name__)

class NewsService:
    """Service for news-related operations"""

    def __init__(
        self, 
        repo: NewsRepository,
        client: GoogleRSSClient
    ):
        self.repo = repo
        self.client = client
    
    # === READ ===
    @ttl_cache(maxsize=128, ttl=600)
    def get_available_dates(self) -> list[DateMetadataSchema]:
        raw_rows = self.repo.get_distinct_published_dates()
        transformed_data = self._transform_date_summary_rows(raw_rows)
        return [DateMetadataSchema(**item) for item in transformed_data]

    def get_business_news(self, locale: str = "ID") -> NewsFeedResponse:
        """
        Fetch and filter business news from Google RSS feed with caching strategy.
        
        Args:
            locale: Locale code (e.g., 'ID', 'US'). Defaults to 'ID'.
            
        Returns:
            NewsFeedResponse: Filtered news feed response containing articles payload.
        """
        # 1. Validate locale
        validated_locale = validate_locale(locale)
        if validated_locale is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or unsupported locale '{locale}'."
            )

        # 2. Evaluate cache fresh status against database threshold
        # 2.1. Retrieve the timestamp of the most recent article in persistent storage
        latest_date = self.repo.get_latest_published_at()
        
        # 2.2. Validate data staleness based on configured maximum allowable age
        is_fresh = is_data_fresh(
            last_published_at=latest_date,
            max_age_hours=5
        )

        # 3. Pipeline routing based on cache freshness status
        if not is_fresh:
            # 3.1. Reconfigure RSS client instance if requested locale differs from active state
            if self.client.locale != validated_locale:
                self.client = GoogleRSSClient(locale=validated_locale)

            # 3.2. Harvest raw news payload from external Google RSS endpoint
            feed_data = self.client.fetch_feed()

            # 3.3. Screen feed entries published after the last database checkpoint
            filtered_articles = self._filter_recent_news(
                feed_entries=feed_data.get("entries", []),
                start_date=latest_date,
            )

            # 3.4. Extract raw dictionary payloads and execute bulk persistence with deduplication
            article_dicts: list[dict[str, str | None]] = [
                {
                    "title": article["title"],
                    "source": article["source"],
                    "published_at": article["published_at"],
                    "link": article["link"],
                    "locale": validated_locale,
                    "relevance_score": None,
                    "relevance_reason": None,
                }
                for article in filtered_articles
            ]
            self.repo.save_filtered_articles(article_dicts)

            # 3.5. Clear cache for get_available_dates()
            self.get_available_dates.cache_clear()
            
        # 4. Determine lookback cutoff timestamp for cached article retrieval
        start_date = get_max_age_cutoff()

        # 5. Query persisted news articles within the active timeline boundary
        filtered_articles = self.repo.get_articles_from_date(
            start_date=start_date,
            locale=validated_locale
        )

        # 6. Transform filtered article payloads into Pydantic response models
        articles_schema = [
            NewsArticle(**(article._asdict() if hasattr(article, "_asdict") else article))
            for article in filtered_articles
        ]
        
        # 7. Construct and return final HTTP news feed response payload
        return NewsFeedResponse(
            articles=articles_schema,
            total_count=len(articles_schema)
        )

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

    def get_titles_by_published_date(
        self,
        date: date | None,
    ) -> list[ArticleTitleData]:
        """
        Retrieve (id, title) pairs for articles published on the given
        UTC calendar date.

        Args:
            date: The UTC published date to filter by. If None, returns
                an empty list (defensive short-circuit).

        Returns:
            A list of ArticleTitleData. Empty list if no date is provided,
            if the repository returns no rows, or if all rows have a null
            title.
        """
        if not date:
            return []

        rows = self.repo.get_id_title_pairs_by_published_date(date)

        if not rows:
            return []

        return [
            ArticleTitleData(id=row.id, title=row.title)
            for row in rows
            if row.title is not None
        ]

    def get_news_by_published_date(
        self,
        published_date: date,
        locale: ArticleLocale,
    ) -> list[NewsArticleResponse]:
        """
        Retrieve all articles published on a given UTC calendar date,
        scoped to a locale.

        Args:
            published_date: The UTC date to filter articles by.
            locale: Target locale (e.g. ArticleLocale.ID).

        Returns:
            A list of NewsArticleResponse payloads, newest first.
        """
        rows = self.repo.get_all_by_published_date(
            published_date=published_date,
            locale=locale.value,
        )

        return [
            NewsArticleResponse(
                id=row.id,
                title=row.title,
                source=row.source,
                published_at=row.published_at,
                link=row.link,
                locale=row.locale,
                relevance_score=row.relevance_score,
                relevance_reason=row.relevance_reason,
            )
            for row in rows
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

        score_payload: list[dict[str, any]] = [
            {
                "id": result.id,
                "relevance_score": result.relevance_score,
                "relevance_reason": result.relevance_reason,
            }
            for result in scoring_response.results
        ]

        self.repo.update_news_scores(score_payload)

    # =======================
    # === PRIVATE METHODS ===
    # =======================
    def _filter_recent_news(
        self,
        feed_entries: list[dict[str, any]],
        start_date: datetime | None = None,
    ) -> list[dict[str, any]]:
        now = datetime.now(timezone.utc)
        cutoff = start_date or (now - timedelta(days=1))

        filtered_entries = []

        for entry in feed_entries:
            published_at = datetime.fromtimestamp(
                timegm(entry["published_parsed"]),
                tz=timezone.utc,
            )

            if not cutoff <= published_at <= now:
                continue

            raw_link = entry.get("link")

            filtered_entries.append(
                {
                    "title": entry["title"],
                    "source": entry["source"]["title"],
                    "published_at": published_at,
                    "link": extract_original_url(raw_link) if raw_link else None,
                }
            )

        return filtered_entries

    def _transform_date_summary_rows(
        self, rows: Sequence[NewsDateSummaryRow]
    ) -> list[dict[str, any]]:
        """Private helper to convert database Row tuples into API-ready dictionaries."""
        return [
            {"date": row.news_date, "total_articles": row.total_articles}
            for row in rows
        ]
