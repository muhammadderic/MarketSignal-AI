from functools import lru_cache
from fastapi import Depends

from app.integrations.clients import GoogleRSSClient, GroqClient
from app.integrations.adapters import GroqAdapter, GoogleRSSAdapter


# === Client Dependencies ===
def get_news_client() -> GoogleRSSClient:
    """Dependency provider for GoogleRSSClient"""
    return GoogleRSSClient()

@lru_cache
def get_groq_client() -> GroqClient:
    """Dependency provider for GroqClient"""
    return GroqClient()


# === Adapter Dependencies ===
def get_groq_adapter(
    client: GroqClient = Depends(get_groq_client)
) -> GroqAdapter:
    """Groq adapter instance with client injection"""
    return GroqAdapter(client=client)

def get_google_rss_adapter(
    client: GoogleRSSClient = Depends(get_news_client),
) -> GoogleRSSAdapter:
    """Provide a GoogleRSSAdapter wrapping the RSS client."""
    return GoogleRSSAdapter(client=client)