from groq import Groq
from app.integrations.clients.google_rss_client import GoogleRSSClient
from app.integrations.clients.groq_client import GroqClient


def get_news_client() -> GoogleRSSClient:
    """Dependency provider for GoogleRSSClient"""
    return GoogleRSSClient()

def get_groq_client() -> GroqClient:
    """Dependency provider for GroqClient"""
    return GroqClient(client=Groq())