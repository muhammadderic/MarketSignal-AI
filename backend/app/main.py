from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import ollama

app = FastAPI(title="MarketSignal AI")

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
@app.post("/score-titles", response_model=List[ScoringResult])
async def score_titles(payload: BatchTitleRequest):
    system_prompt = """
    You are a financial news classification engine. Evaluate the financial impact of the news title on a scale of 1 to 10.
    - 9-10: M&A, share buybacks, bankruptcies, major corporate actions.
    - 6-8 : Earnings reports, revenue beats/misses, major layoffs, dividends.
    - 3-5 : General stock price movements, analyst opinions, broad market news.
    - 1-2 : Non-financial news, consumer reviews, clickbait, general noise.
    """
    
    results = []
    client = ollama.AsyncClient()
    
    try:
        # Loop over every title in the incoming list
        for title in payload.titles:
            response = await client.chat(
                model="llama3.2:1b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": title}
                ],
                format=ScoringResult.model_json_schema(),
                options={"temperature": 0.0}
            )
            
            # Parse response into Pydantic model
            result = ScoringResult.model_validate_json(response.message.content)
            results.append(result)
            
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Processing Error: {str(e)}")