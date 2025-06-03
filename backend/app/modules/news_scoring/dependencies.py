from fastapi import Depends

from app.core.dependencies import get_groq_client
from app.integrations.clients.groq_client import GroqClient
from app.modules.news_scoring.ns_service import NewsScoringService


# --- Service Dependencies ---
def get_news_scoring_service(
    groq_client: GroqClient = Depends(get_groq_client),
) -> NewsScoringService:
    """Dependency provider for NewsScoringService"""
    return NewsScoringService(
        groq_client=groq_client
    )