from app.modules.news_scoring.ns_schemas import (
    BatchScoringResponse,
    NewsScoreBatchRequest
)
from app.modules.news_scoring.ns_utils import validate_batch_size
from app.modules.news_scoring.ns_service import NewsScoringService
from app.modules.news.news_services import NewsService
from app.modules.news.news_utils import sanitize_article_titles


class NewsScoringOrchestrator:
    def __init__(
        self,
        news: NewsService,
        news_scoring: NewsScoringService
    ):
        self.news = news
        self.news_scoring = news_scoring

    def sync_and_get_news_scores(
        self, 
        payload: NewsScoreBatchRequest
    ) -> BatchScoringResponse:
        # 1. Check total data retrieved (min: 10 and max: 20)
        validate_batch_size(payload.article_ids)

        # 2. Get all news titles from database
        news_titles_and_id = self.news.get_titles_by_ids(payload.article_ids)

        # 3. Sanitize titles by removing source suffix
        news_titles_and_id = sanitize_article_titles(news_titles_and_id)

        # 4. Scoring titles
        scoring_response = self.news_scoring.score_titles(news_titles_and_id)

        return scoring_response
