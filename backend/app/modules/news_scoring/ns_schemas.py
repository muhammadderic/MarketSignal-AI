from pydantic import BaseModel, Field


class ScoringResult(BaseModel):
    cleaned_title: str
    relevance_score: int = Field(
        ..., 
        description="Score from 1 to 5"
    )
    reason: str = Field(
        ..., 
        description="Detailed explanation and reasoning from the LLM justifying the assigned relevance score."
    )


class NewsScoreBatchRequest(BaseModel):
    article_ids: list[int] = Field(
        ...,
        min_length=10,
        max_length=20,
        description="List of integer article IDs to synchronize and score (between 10 and 20 items)."
    )


class ArticleScoreResult(BaseModel):
    id: int = Field(
        ..., 
        description="Exact integer ID matching the input article"
    )
    relevance_score: int = Field(
        ..., 
        ge=1, 
        le=5, 
        description="Financial impact score from 1 to 5"
    )
    relevance_reason: str = Field(
        ..., 
        description="Brief title-specific explanation for the score"
    )


class BatchScoringResponse(BaseModel):
    results: list[ArticleScoreResult]
