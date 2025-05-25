import time
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Dict, Any, Optional

from app.integrations.clients.google_rss_client import GoogleRSSClient
from app.modules.news.news_schemas import NewsFeedResponse, NewsArticleData
from app.modules.news.news_utils import parse_input_date, extract_original_url
from app.modules.news.news_constants import SQLITE_FORMAT

logger = logging.getLogger(__name__)

class NewsService:
    """Service for news-related operations"""

    def __init__(self, client: GoogleRSSClient):
        self.client = client
    
    def get_business_news(self, locale: str = "ID") -> NewsFeedResponse:
        """
        Fetch and filter business news from Google RSS feed.
        
        Args:
            locale: Locale code (e.g., 'ID', 'US'). Defaults to 'ID'.
            
        Returns:
            NewsFeedResponse: Filtered news feed response
        """
        # Update client locale if different
        if self.client.locale != locale:
            self.client = GoogleRSSClient(locale=locale)
        
        # 1. Fetch raw feed data
        feed_data = self.client.fetch_feed()
        
        # 2. Extract global feed info
        feed_title, formatted_update_date = self._get_feed_global_info(feed_data)
        
        # 3. Filter recent news (starting from feed's updated date)
        filtered_articles, start_date, end_date = self._filter_recent_news(
            feed_entries=feed_data.get("entries", []),
            # start_date=formatted_update_date, // TEST: just for get 1 day data list
            with_link=True
        )
        
        # 4. Convert to schema
        articles_schema = [
            NewsArticleData(**article) for article in filtered_articles
        ]
        
        # 5. Build response
        return NewsFeedResponse(
            feed_title=feed_title,
            formatted_update_date=formatted_update_date,
            articles=articles_schema,
            total_count=len(articles_schema)
        )

    def _get_feed_global_info(self, feed_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """
        Extract global feed information.
        
        Args:
            feed_data: Parsed feed data from fetch_feed()
            
        Returns:
            Tuple[str, Optional[str]]: (feed_title, formatted_update_date)
        """
        feed_metadata = feed_data.get("feed", {})
        
        feed_title = feed_metadata.get('title', 'Unknown Feed Title')
        updated_tuple = feed_metadata.get('updated_parsed')
        
        if updated_tuple:
            formatted_update_date = time.strftime(SQLITE_FORMAT, updated_tuple)
        else:
            formatted_update_date = None
        
        return feed_title, formatted_update_date

    def _filter_recent_news(
        self,
        feed_entries: List[Any],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        with_link: bool = True
    ) -> Tuple[List[Dict[str, Any]], datetime, datetime]:
        """
        Filters Google News feed entries within a precise time window.

        Args:
            feed_entries: List of feed entries from parsed feed.
            start_date: Start boundary (datetime or 'YYYY-MM-DD HH:MM:SS'). Defaults to 24h ago.
            end_date: End boundary (datetime or 'YYYY-MM-DD HH:MM:SS'). Defaults to right now.
            with_link: Whether to include the article URL link in the output payload.

        Returns:
            Tuple[List[Dict[str, Any]], datetime]: (filtered_articles list, end_date datetime)
        """
        # 1. Establish naive UTC datetime boundaries for fast comparison
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        end_date = parse_input_date(end_date, now)
        start_date = parse_input_date(start_date, end_date - timedelta(days=1))

        filtered_articles = []

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

                # 2.3.2. Construct core data payload with SQLite-aligned standard string
                article_data = {
                    "title": entry.get('title', None),
                    "source": source_name,
                    "published_at": article_time.strftime(SQLITE_FORMAT)
                }

                # 2.3.3. Include and extract original article URL if requested
                if with_link:
                    raw_link = entry.get('link', None)
                    article_data["link"] = extract_original_url(raw_link) if raw_link else None

                filtered_articles.append(article_data)

        # 3. Sorting articles by Published Date
        filtered_articles.sort(
            key=lambda x: datetime.strptime(x["published_at"], SQLITE_FORMAT),
            reverse=True  # Newest first
        )

        logger.debug(f"End Datetime  : {end_date.strftime(SQLITE_FORMAT)} UTC")
        logger.debug(f"Start Datetime: {start_date.strftime(SQLITE_FORMAT)} UTC")
        logger.info(f"Total News    : {len(filtered_articles)} articles found within this window.")

        return filtered_articles, start_date, end_date
