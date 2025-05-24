from app.integrations.clients.google_rss_client import GoogleRSSClient


def get_news_client() -> GoogleRSSClient:
    """Dependency provider for GoogleRSSClient"""
    return GoogleRSSClient()
    