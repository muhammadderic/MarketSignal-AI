from datetime import datetime, date as date_type
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


class NewsArticleResponse(BaseModel):
    """Full news article payload returned to the client."""

    id: int = Field(..., description="Article ID")
    title: str | None = Field(None, description="Article title")
    source: str = Field(..., description="Source publisher name")
    published_at: datetime = Field(..., description="UTC publish timestamp")
    link: str | None = Field(None, description="Original article URL")
    locale: ArticleLocale = Field(..., description="Article locale")
    relevance_score: int | None = Field(
        None, description="LLM financial relevance score (1-5)"
    )
    relevance_reason: str | None = Field(
        None, description="LLM explanation for the relevance score"
    )

    model_config = ConfigDict(from_attributes=True)


class DailyNewsResponse(BaseModel):
    """Envelope for a day's worth of news articles."""

    date: date_type = Field(..., description="The queried UTC date (YYYY-MM-DD)")
    items: list[NewsArticleResponse] = Field(
        ..., description="Articles published on that date, newest first"
    )