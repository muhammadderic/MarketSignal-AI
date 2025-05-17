import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from groq import AsyncGroq
from dotenv import load_dotenv

app = FastAPI(title="MarketSignal AI")

load_dotenv()

client = AsyncGroq()  # Automatic reads GROQ api key

# Updated Request Body: Accepts a list of news title strings
class BatchTitleRequest(BaseModel):
    titles: List[str] = Field(
        ..., 
        example=[
            "TechCorp announces $50M share buyback program",
            "Top 5 tech gadgets to buy this weekend"
        ]
    )


# Output Schema for a single title score
class ScoringResult(BaseModel):
    cleaned_title: str
    relevance_score: int = Field(..., description="Score from 1 to 10")
    reason: str


# Updated Batch Async Route: Returns a lust of ScoringResult objects
@app.post("/score-titles", response_model=list[ScoringResult])
async def score_titles(payload: BatchTitleRequest):
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

    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Score these titles: {json.dumps(payload.titles)}",
                },
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},  # Allowed because "JSON" is in system prompt
            temperature=0.0,
        )

        response_content = chat_completion.choices[0].message.content
        parsed_json = json.loads(response_content)

        # Extract array from the returned JSON wrapper
        return parsed_json.get("results", [])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Processing Error: {str(e)}")