import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status

from app.integrations.clients.google_rss_client import GoogleRSSClient
from app.modules.news.news_schemas import NewsFeedResponse, NewsArticle
from app.modules.news.news_utils import (
    parse_input_date, 
    extract_original_url,
    is_data_fresh,
    get_max_age_cutoff,
    validate_locale
)
from app.modules.news.news_constants import SQLITE_FORMAT, ArticleLocale
from app.modules.news.news_repo import NewsRepository

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
        latest_data = self.repo.get_latest_published_at()
        
        # 2.2. Validate data staleness based on configured maximum allowable age
        data_freshness = is_data_fresh(
            last_published_at=latest_data,
            max_age_hours=5
        )

        # 3. Pipeline routing based on cache freshness status
        if data_freshness:
            # 3a.1. Determine lookback cutoff timestamp for cached article retrieval
            start_date = get_max_age_cutoff()

            # 3a.2. Query persisted news articles within the active timeline boundary
            filtered_articles = self.repo.get_articles_from_date(
                start_date=start_date,
                locale=validated_locale
            )
        else:
            # 3b.1. Reconfigure RSS client instance if requested locale differs from active state
            if self.client.locale != validated_locale:
                self.client = GoogleRSSClient(locale=validated_locale)

            # 3b.2. Harvest raw news payload from external Google RSS endpoint
            feed_data = self.client.fetch_feed()
        
            # 3b.3. Screen feed entries published after the last database checkpoint
            filtered_articles = self._filter_recent_news(
                feed_entries=feed_data.get("entries", []),
                locale=validated_locale,
                start_date=latest_data,
                with_link=True
            )

            # 3b.4. Extract raw dictionary payloads and execute bulk persistence with deduplication
            article_dicts: list[dict[str, str | None]] = [
                {
                    "title": article["title"],
                    "source": article["source"],
                    "published_at": article["published_at"],
                    "link": article["link"],
                    "locale": article["locale"]
                }
                for article in filtered_articles
            ]
            self.repo.save_filtered_articles(article_dicts)

        # 4. Transform filtered article payloads into Pydantic response models
        articles_schema = [
            NewsArticle(**(article._asdict() if hasattr(article, "_asdict") else article))
            for article in filtered_articles
        ]
        
        # 5. Construct and return final HTTP news feed response payload
        return NewsFeedResponse(
            articles=articles_schema,
            total_count=len(articles_schema)
        )

    def _filter_recent_news(
        self,
        feed_entries: list[dict[str, any]],
        locale: ArticleLocale | str = ArticleLocale.ID,
        start_date: str | datetime | None = None,
        end_date: str | datetime | None = None,
        with_link: bool = True
    ) -> list[dict[str, any]]:
        """
        Filters Google News feed entries within a precise time window and attaches locale metadata.

        Args:
            feed_entries: List of feed entries from parsed feed.
            locale: Target locale code or ArticleLocale Enum for the articles. Defaults to ArticleLocale.ID.
            start_date: Start boundary (datetime or 'YYYY-MM-DD HH:MM:SS'). Defaults to 24h ago.
            end_date: End boundary (datetime or 'YYYY-MM-DD HH:MM:SS'). Defaults to right now.
            with_link: Whether to include the article URL link in the output payload.

        Returns:
            list[dict[str, Any]]: Filtered article dictionaries containing native datetime objects for database compatibility.
        """
        # 1. Establish naive UTC datetime boundaries for fast comparison
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        end_date = parse_input_date(end_date, now)
        start_date = parse_input_date(start_date, end_date - timedelta(days=1))

        # Resolve locale string representation if an Enum member was passed
        locale_str = locale.value if isinstance(locale, ArticleLocale) else locale

        filtered_articles: list[dict[str, any]] = []

        # 2. Iterate and screen the article elements
        for entry in feed_entries:
            # 2.1. Extract published timestamp from feed entry
            pub_tuple = entry.get('published_parsed')
            if not pub_tuple:
                continue

            # 2.2. Convert time.struct_time to naive UTC datetime
            article_time = datetime(*pub_tuple[:6])

            # 2.3. Check if the article falls within the timeline threshold
            if start_date <= article_time <= end_date:
                # 2.3.1. Extract source name from feed entry metadata
                source_name = entry.source.get('title', 'Unknown Source') if 'source' in entry else 'Unknown Source'

                # 2.3.2. Construct core data payload with native datetime object for database compatibility
                article_data: dict[str, any] = {
                    "title": entry.get('title', None),
                    "source": source_name,
                    "published_at": article_time,  # <--- UPDATED LINE 1
                    "locale": locale_str,
                }

                # 2.3.3. Include and extract original article URL if requested
                if with_link:
                    raw_link = entry.get('link', None)
                    article_data["link"] = extract_original_url(raw_link) if raw_link else None

                filtered_articles.append(article_data)

        # 3. Sorting articles by Published Date
        filtered_articles.sort(
            key=lambda x: x["published_at"],  # <--- UPDATED LINE 2
            reverse=True  # Newest first
        )

        logger.debug(f"Target Locale : {locale_str}")
        logger.debug(f"End Datetime  : {end_date.strftime(SQLITE_FORMAT)} UTC")
        logger.debug(f"Start Datetime: {start_date.strftime(SQLITE_FORMAT)} UTC")
        logger.info(f"Total News    : {len(filtered_articles)} articles found within this window.")

        return filtered_articles
