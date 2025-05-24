from pydantic import BaseModel, Field
from typing import List


class NewsArticleData(BaseModel):
    """Schema for individual news article data"""
    title: str | None = Field(
        default=None,
        description="Article headline/title"
    )
    source: str = Field(
        ...,
        description="News source name"
    )
    published_at: str = Field(
        ...,
        description="Article publication timestamp in SQLite format (YYYY-MM-DD HH:MM:SS)"
    )
    link: str | None = Field(
        default=None,
        description="URL link to the full article"
    )


class NewsFeedResponse(BaseModel):
    """Response schema for news feed data"""
    feed_title: str = Field(
        ...,
        description="Title of the RSS feed"
    )
    formatted_update_date: str | None = Field(
        default=None,
        description="Feed last updated timestamp in SQLite format (YYYY-MM-DD HH:MM:SS)"
    )
    articles: List[NewsArticleData] = Field(
        default_factory=list,
        description="List of filtered news articles"
    )
    total_count: int = Field(
        ...,
        description="Total number of articles in the response"
    )
    