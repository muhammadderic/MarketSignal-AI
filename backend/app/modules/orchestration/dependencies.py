from fastapi import Depends

from app.modules.news_archieve.services import NewsArchieveService
from app.modules.news_archieve.dependencies import get_news_archieve_service
from app.modules.news_scoring.dependencies import get_news_scoring_service
from app.modules.news_scoring.ns_service import NewsScoringService
from app.modules.orchestration.news_scoring_orctr import NewsScoringOrchestrator


# --- Service Dependencies ---
def get_news_scoring_orchestrator(
    news: NewsArchieveService = Depends(get_news_archieve_service),
    news_scoring: NewsScoringService = Depends(get_news_scoring_service)
) -> NewsScoringOrchestrator:
    """Dependency provider for NewsScoringOrchestrator"""
    return NewsScoringOrchestrator(
        news=news,
        news_scoring=news_scoring
    )