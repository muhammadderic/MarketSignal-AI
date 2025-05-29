from datetime import datetime
from pydantic import BaseModel, Field

from app.modules.news.news_constants import ArticleLocale


class NewsArticle(BaseModel):
    """Schema for individual news article data"""
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
    