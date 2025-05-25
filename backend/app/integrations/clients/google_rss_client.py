import feedparser
import logging
from fastapi import HTTPException, status
from typing import  Dict, Any

logger = logging.getLogger(__name__)


class GoogleRSSClient:
    """Client for fetching and parsing Google News RSS feeds"""
    
    # Locale configurations for different regions
    LOCALES: Dict[str, str] = {
        "ID": "hl=en-ID&gl=ID&ceid=ID:en",
        "US": "hl=en-US&gl=US&ceid=US:en"
    }
    
    BASE_URL = "https://news.google.com/news/rss/headlines/section/topic/BUSINESS"
    
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
    