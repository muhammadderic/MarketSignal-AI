from fastapi import APIRouter, status, Depends

from app.modules.news_scoring.ns_schemas import (
    NewsScoreBatchRequest,
    BatchScoringResponse
)
from app.modules.orchestration.dependencies import get_news_scoring_orchestrator
from app.modules.orchestration.news_scoring_orctr import NewsScoringOrchestrator

router = APIRouter(prefix="/news-scoring")


@router.post(
    "/",
    response_model=BatchScoringResponse,
    status_code=status.HTTP_200_OK
)
async def scoring_news_titles(
    payload: NewsScoreBatchRequest,
    orchestrator: NewsScoringOrchestrator = Depends(get_news_scoring_orchestrator)
) -> BatchScoringResponse:
    """
    Scoring news titles.

    Args:

    Returns:
    """
    return await orchestrator.sync_and_get_news_scores(payload)
