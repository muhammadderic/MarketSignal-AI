import json
from groq import Groq
from dotenv import load_dotenv
from typing import List, Any

load_dotenv()


class GroqClient:
    def __init__(self):
        self.client = Groq()
    
    async def list_available_models(self) -> List[Any]:
        """Fetch all available models from Groq API"""
        models_response = self.client.models.list()
        return models_response.data
        
    async def score_titles(self, titles: list[str], system_prompt: str) -> str:
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Score these titles: {json.dumps(titles)}"},
            ],
            model="openai/gpt-oss-20b",
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        return chat_completion.choices[0].message.content
    
        