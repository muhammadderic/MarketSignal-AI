import json

from app.clients import GroqClient
from app.schemas import ScoringResult


class PipelineService:
    def __init__(self):
        self.groq_client = GroqClient()
    
    async def score_titles(self, titles: list[str]) -> list[ScoringResult]:
        system_prompt = """
            You are a financial news classification engine. Evaluate the financial impact of the news title on a scale of 1 to 10.
            - 9-10: M&A, share buybacks, bankruptcies, major corporate actions.
            - 6-8 : Earnings reports, revenue beats/misses, major layoffs, dividends.
            - 3-5 : General stock price movements, analyst opinions, broad market news.
            - 1-2 : Non-financial news, consumer reviews, clickbait, general noise.

            Output format requirement:
            Provide your response strictly as a JSON object containing an array under the Structure:
            {
            "results": [
                    {
                    "cleaned_title": "Cleaned version of title",
                    "relevance_score": 1-10 integer score,
                    "reason": "Short explanation"
                    }
                ]
            }
            """
        
        response_content = await self.groq_client.score_titles(titles, system_prompt)
        parsed_json = json.loads(response_content)
        return parsed_json.get("results", [])
        