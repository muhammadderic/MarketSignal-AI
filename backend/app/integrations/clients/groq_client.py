import json
from groq import AsyncGroq


class GroqClient:        
    def __init__(self, api_key: str | None = None):
        self.client = AsyncGroq(api_key=api_key)

    async def score_titles(
        self, 
        input_articles: list[dict[int, str]],
        system_prompt: str
    ) -> str:
        """
        Evaluates a batch of news titles using Groq structured JSON outputs.
        """
        chat_completion = await self.client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": f"Score these articles: {json.dumps(input_articles)}"
                },
            ],
            model="openai/gpt-oss-20b",
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        
        return chat_completion.choices[0].message.content
    
    async def list_available_models(self) -> list[any]:
        """Fetch all available models from Groq API"""
        models_response = await self.client.models.list()
        return models_response.data
