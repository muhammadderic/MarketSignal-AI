from pydantic import BaseModel, Field

from app.modules.news_scoring.constants import NEWS_SCORING_MIN_TITLE_PAIRS, NEWS_SCORING_MAX_TITLE_PAIRS


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
    """Request body for scoring a batch of news articles."""

    news_ids: list[int] = Field(
        ...,
        min_length=NEWS_SCORING_MIN_TITLE_PAIRS,
        max_length=NEWS_SCORING_MAX_TITLE_PAIRS,
        description="Between 10 and 20 unique news article IDs to score",
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


class ArticleTitleData(BaseModel):
    """Schema for an article's id and title pair."""
    
    id: int = Field(..., description="Article ID")
    title: str = Field(..., description="Article title")
    