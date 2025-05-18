from pydantic import BaseModel, Field
from typing import List


class BatchTitleRequest(BaseModel):
    titles: List[str] = Field(
        ..., 
        example=[
            "TechCorp announces $50M share buyback program",
            "Top 5 tech gadgets to buy this weekend"
        ]
    )


class ScoringResult(BaseModel):
    cleaned_title: str
    relevance_score: int = Field(..., description="Score from 1 to 10")
    reason: str
    