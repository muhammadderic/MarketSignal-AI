import logging

from app.integrations.clients.google_rss_client import GoogleRSSClient

from app.modules.news.news_repo import NewsRepository
from app.modules.news_scoring.ns_schemas import BatchScoringResponse

logger = logging.getLogger(__name__)

class NewsService:
    """Service for news-related operations"""

    def __init__(
        self, 
        repo: NewsRepository,
        client: GoogleRSSClient
    ):
        self.repo = repo
        self.client = client
    
    # === READ ===
    
    # === UPDATE ===
    def update_news_scores(
        self,
        scoring_response: BatchScoringResponse,
    ) -> None:
        """
        Persist LLM relevance scores and reasons back onto existing
        news rows, keyed by article id.

        This is a pure update path — no inserts, no upserts.

        Args:
            scoring_response: Parsed batch response from the scoring
                service. Each `ArticleScoreResult` carries the target
                `id` plus `relevance_score` and `relevance_reason`.

        Returns:
            None. Side effect: rows in `news_article_data` are updated.
        """
        if not scoring_response.results:
            return

        score_payload: list[dict[str, any]] = [
            {
                "id": result.id,
                "relevance_score": result.relevance_score,
                "relevance_reason": result.relevance_reason,
            }
            for result in scoring_response.results
        ]

        self.repo.update_news_scores(score_payload)

    # =======================
    # === PRIVATE METHODS ===
    # =======================
