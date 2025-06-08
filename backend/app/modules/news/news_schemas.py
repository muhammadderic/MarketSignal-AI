from datetime import datetime, date as DateType
from pydantic import BaseModel, Field, ConfigDict

from app.modules.news.news_constants import ArticleLocale


class NewsArticle(BaseModel):
    """Schema for individual news article data"""
    id: int = Field(
        ..., 
        description="Primary key identifier for the news article"
    )
    title: str | None = Field(
        default=None,
        description="Article headline/title"
    )
    source: str = Field(
        ...,
        description="News source name"
    )
    published_at: datetime = Field(
        ...,
        description="Article publication timestamp in SQLite format (YYYY-MM-DD HH:MM:SS)"
    )
    link: str | None = Field(
        default=None,
        description="URL link to the full article"
    )
    locale: ArticleLocale = Field(
        default=ArticleLocale.UNASSIGNED,
        description="Target locale/country code for the news article (e.g., 'ID', 'US')"
    )
    relevance_score: int | None = Field(
        default=None, description="LLM relevance score from 1 to 5"
    )
    relevance_reason: str | None = Field(
        default=None, description="LLM reasoning justifying the score"
    )


class NewsFeedResponse(BaseModel):
    """Response schema for news feed data"""
    articles: list[NewsArticle] = Field(
        default_factory=list,
        description="List of filtered news articles"
    )
    total_count: int = Field(
        ...,
        description="Total number of articles in the response"
    )


class ArticleTitleData(BaseModel):
    """Schema for an article's id and title pair."""
    
    id: int = Field(..., description="Article ID")
    title: str = Field(..., description="Article title")


class DateMetadataSchema(BaseModel):
    """Represents a single available news date along with total article counts."""

    date: DateType = Field(
        ...,
        description="Published date for available news articles (YYYY-MM-DD)",
    )
    total_articles: int = Field(
        ..., ge=0, description="Total count of articles published on this date"
    )

    model_config = ConfigDict(from_attributes=True)
