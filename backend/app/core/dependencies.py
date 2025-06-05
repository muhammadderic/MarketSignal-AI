from functools import lru_cache
from fastapi import Depends

from app.integrations.clients import GoogleRSSClient, GroqClient
from app.integrations.adapters import GroqAdapter


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
    