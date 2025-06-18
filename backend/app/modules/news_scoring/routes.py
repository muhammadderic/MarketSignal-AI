from fastapi import APIRouter, status, Depends, Query
from datetime import date

from app.modules.news_archieve.schemas import DailyNewsResponse
from app.modules.news_scoring.ns_schemas import NewsScoreBatchRequest, BatchScoringResponse
from app.modules.orchestration.dependencies import get_news_scoring_orchestrator
from app.modules.orchestration.news_scoring_orctr import NewsScoringOrchestrator

router = APIRouter(prefix="/news-scoring")


@router.post(
    "/batch-by-ids",
    response_model=DailyNewsResponse,
    status_code=status.HTTP_200_OK
)
async def scoring_news_titles(
    payload: NewsScoreBatchRequest,
    date: date = Query(..., description="Article date in YYYY-MM-DD format"),
    orchestrator: NewsScoringOrchestrator = Depends(get_news_scoring_orchestrator)
) -> DailyNewsResponse:
    """"
    Score a selected batch of news articles synchronously, persist the
    results, and return the news data for the requested publication
    date with the latest scoring results.

    Args:
        payload: Batch request body containing `news_ids` (10-20 unique IDs).
        date: Publication date to return news for (YYYY-MM-DD).
        orchestrator: Injected scoring orchestrator.

    Returns:
        A DailyNewsResponse for `date`, with freshly persisted scores.
    """
    return await orchestrator.sync_and_get_news_scores(
        article_ids=payload.news_ids,
        published_date=date,
    )


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
