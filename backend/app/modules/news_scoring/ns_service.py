from app.integrations.clients.groq_client import GroqClient
from app.modules.news_scoring.ns_schemas import BatchScoringResponse
from app.modules.news_scoring.ns_constants import finance_decision_scoring_usage_2
from app.modules.news.news_schemas import ArticleTitleData


class NewsScoringService:
    def __init__(
        self,
        groq_client: GroqClient
    ):
        self.groq_client = groq_client
    
    async def score_titles(
        self, 
        article_title_data: list[ArticleTitleData]
    ) -> BatchScoringResponse:
        scoring_response = await self.groq_client.score_titles(
            article_title_data, 
            finance_decision_scoring_usage_2
        )

        return scoring_response
        