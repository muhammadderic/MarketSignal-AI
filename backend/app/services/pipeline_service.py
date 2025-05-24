import json

from app.clients import GroqClient
from app.schemas import ScoringResult
from app.constants import finance_decision_scoring_dummy


class PipelineService:
    def __init__(self):
        self.groq_client = GroqClient()
    
    async def score_titles(self, titles: list[str]) -> list[ScoringResult]:
        response_content = await self.groq_client.score_titles(titles, finance_decision_scoring_dummy)
        parsed_json = json.loads(response_content)
        return parsed_json.get("results", [])
        