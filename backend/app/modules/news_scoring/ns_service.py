from app.integrations.clients.groq_client import GroqClient
from app.modules.news_scoring.ns_schemas import BatchScoringResponse
from app.modules.news_scoring.constants import finance_decision_scoring_usage_2
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
        # 1. Transform Pydantic models into list[dict[int, str]]
        # Output structure: [{item.id: item.title} for item in article_title_data]
        articles_payload: list[dict[int, str]] = [
            {item.id: item.title} for item in article_title_data
        ]

        scoring_response_str = await self.groq_client.score_titles(
            articles_payload, 
            finance_decision_scoring_usage_2
        )

        # 3. Parse raw JSON string into Pydantic schema
        return BatchScoringResponse.model_validate_json(scoring_response_str)
        