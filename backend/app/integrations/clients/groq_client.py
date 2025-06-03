import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class GroqClient:
    def __init__(
        self, 
        client: Groq
    ):
        self.client = client
        
    async def score_titles(
        self, 
        input_articles: list[dict[int, str]],
        system_prompt: str
    ) -> str:
        """
        Evaluates a batch of news titles using Groq structured JSON outputs.
        """
        chat_completion = self.client.chat.completions.create(
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
    