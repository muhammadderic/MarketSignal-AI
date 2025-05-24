from app.integrations.clients.google_rss_client import GoogleRSSClient
from app.modules.news.news_schemas import NewsFeedResponse, NewsArticleData


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
        feed_title, formatted_update_date = self.client.get_feed_global_info(feed_data)
        
        # 3. Filter recent news (starting from feed's updated date)
        filtered_articles, start_date, end_date = self.client.filter_recent_news(
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
