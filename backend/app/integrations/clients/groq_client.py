import json
from groq import Groq
from dotenv import load_dotenv

from app.modules.news.news_schemas import ArticleTitleData
from app.modules.news_scoring.ns_schemas import BatchScoringResponse

load_dotenv()


class GroqClient:
    def __init__(
        self, 
        client: Groq
    ):
        self.client = client
        
    async def score_titles(
        self, 
        input_articles: list[ArticleTitleData],
        system_prompt: str
    ) -> BatchScoringResponse:
        """
        Evaluates a batch of news titles using Groq structured JSON outputs.
        """
        # Serialize input objects cleanly
        articles_payload = [article.model_dump() for article in input_articles]

        chat_completion = self.client.chat.completions.parse(
            messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": f"Score these articles: {json.dumps(articles_payload)}"
                },
            ],
            model="llama-3.1-8b-instant",
            response_format=BatchScoringResponse,
            temperature=0.0,
        )
        
        # Returns the parsed Pydantic object directly
        return chat_completion.choices[0].message.parsed
    