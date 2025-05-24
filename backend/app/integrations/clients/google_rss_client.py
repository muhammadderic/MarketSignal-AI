import feedparser
import time
import logging
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class GoogleRSSClient:
    """Client for fetching and parsing Google News RSS feeds"""
    
    # Locale configurations for different regions
    LOCALES: Dict[str, str] = {
        "ID": "hl=en-ID&gl=ID&ceid=ID:en",
        "US": "hl=en-US&gl=US&ceid=US:en"
    }
    
    BASE_URL = "https://news.google.com/news/rss/headlines/section/topic/BUSINESS"
    SQLITE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    def __init__(self, locale: str = "ID"):
        """
        Initialize Google RSS client.
        
        Args:
            locale: Locale code (e.g., 'ID', 'US'). Defaults to 'ID'.
        """
        self.locale = locale
        self.locale_params = self.LOCALES.get(locale)
        
        if not self.locale_params:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported locale: {locale}. Supported: {list(self.LOCALES.keys())}"
            )
    
    def fetch_feed(self) -> Dict[str, Any]:
        """
        Fetch and parse the RSS feed.
        
        Returns:
            Dict[str, Any]: Parsed feed data containing 'feed' and 'entries'
        """
        url = f"{self.BASE_URL}?{self.locale_params}"
        
        try:
            logger.info(f"Fetching Google RSS feed for locale: {self.locale}")
            feed = feedparser.parse(url)
            
            if feed.bozo:  # Check for parsing errors
                logger.warning(f"Feed parsing warning: {feed.bozo_exception}")
            
            return {
                "feed": feed.feed,
                "entries": feed.entries
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch Google RSS feed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch news feed from Google RSS: {str(e)}"
            )
    
    def get_feed_global_info(self, feed_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
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
            formatted_update_date = time.strftime(self.SQLITE_FORMAT, updated_tuple)
        else:
            formatted_update_date = None
        
        return feed_title, formatted_update_date
    
    def filter_recent_news(
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
        # Helper parser for incoming string or datetime arguments
        def parse_input_date(val, default_val):
            if val is None:
                return default_val
            if isinstance(val, str):
                return datetime.strptime(val, self.SQLITE_FORMAT)
            if isinstance(val, datetime) and val.tzinfo is not None:
                return val.astimezone(timezone.utc).replace(tzinfo=None)
            return val

        # 1. Establish naive UTC datetime boundaries for fast comparison
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        end_date = parse_input_date(end_date, now)
        start_date = parse_input_date(start_date, end_date - timedelta(days=1))

        filtered_articles = []

        # 2. Iterate and screen the article elements
        for entry in feed_entries:
            pub_tuple = entry.get('published_parsed')
            if not pub_tuple:
                continue

            # Convert time.struct_time to naive UTC datetime
            article_time = datetime(*pub_tuple[:6])

            # Check if the article falls within the timeline threshold
            if start_date <= article_time <= end_date:
                source_name = entry.source.get('title', 'Unknown Source') if 'source' in entry else 'Unknown Source'

                # Construct core data payload with SQLite-aligned standard string
                article_data = {
                    "title": entry.get('title', None),
                    "source": source_name,
                    "published_at": article_time.strftime(self.SQLITE_FORMAT)
                }

                if with_link:
                    article_data["link"] = entry.get('link', None)

                filtered_articles.append(article_data)

        logger.debug(f"End Datetime  : {end_date.strftime(self.SQLITE_FORMAT)} UTC")
        logger.debug(f"Start Datetime: {start_date.strftime(self.SQLITE_FORMAT)} UTC")
        logger.info(f"Total News    : {len(filtered_articles)} articles found within this window.")

        return filtered_articles, start_date, end_date
