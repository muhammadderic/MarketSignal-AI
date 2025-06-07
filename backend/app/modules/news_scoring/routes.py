from fastapi import APIRouter, status, Depends, Query
from datetime import date

from app.modules.news_scoring.ns_schemas import NewsScoreBatchRequest, BatchScoringResponse
from app.modules.orchestration.dependencies import get_news_scoring_orchestrator
from app.modules.orchestration.news_scoring_orctr import NewsScoringOrchestrator

router = APIRouter(prefix="/news-scoring")


@router.post(
    "/batch-by-ids",
    response_model=BatchScoringResponse,
    status_code=status.HTTP_200_OK
)
async def scoring_news_titles(
    payload: NewsScoreBatchRequest,
    orchestrator: NewsScoringOrchestrator = Depends(get_news_scoring_orchestrator)
) -> BatchScoringResponse:
    """
    Scoring news titles.
    """
    return await orchestrator.sync_and_get_news_scores(payload.article_ids)


@router.get(
    "/",
    response_model=BatchScoringResponse,
    status_code=status.HTTP_200_OK,
)
async def get_titles_for_scoring(
    target_date: date = Query(
        ..., 
        alias="date", 
        description="Filter scores by published date (YYYY-MM-DD)"
    ),
    orchestrator: NewsScoringOrchestrator = Depends(get_news_scoring_orchestrator),
):
    """
    Retrieve article (id, title) pairs for a given published date,
    validated against the minimum-pairs threshold required for
    downstream LLM scoring.

    Args:

    Returns:
        A list of ArticleTitleData ready for LLM relevance scoring.
    """
    scores = await orchestrator.get_titles_for_scoring(target_date)
    return scores
