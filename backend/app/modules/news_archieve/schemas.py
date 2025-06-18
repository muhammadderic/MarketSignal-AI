from datetime import datetime, date as date_type
from pydantic import BaseModel, Field, ConfigDict

from app.modules.news_archieve.constants import ArticleLocale

class ArticleTitleData(BaseModel):
    """Schema for an article's id and title pair."""
    
    id: int = Field(..., description="Article ID")
    title: str = Field(..., description="Article title")

# === News by Date ===

class NewsArticleResponse(BaseModel):
    """Full news article payload returned to the client."""

    id: int = Field(..., description="Article ID")
    title: str | None = Field(None, description="Article title")
    source: str = Field(..., description="Source publisher name")
    published_at: datetime = Field(..., description="UTC publish timestamp")
    link: str | None = Field(None, description="Original article URL")
    locale: ArticleLocale = Field(..., description="Article locale")
    score: int | None = Field(
        None, description="LLM financial relevance score (1-5)"
    )
    reason: str | None = Field(
        None, description="LLM explanation for the relevance score"
    )

    model_config = ConfigDict(from_attributes=True)


class DailyNewsResponse(BaseModel):
    """Envelope for a day's worth of news articles."""

    date: date_type = Field(..., description="The queried UTC date (YYYY-MM-DD)")
    items: list[NewsArticleResponse] = Field(
        ..., description="Articles published on that date, newest first"
    )

# === News Archieve with Counts ===

class ArchiveCountItem(BaseModel):
    """A single per-day article count."""

    date: date_type
    total: int = Field(..., ge=1)


class ArchiveCountsResponse(BaseModel):
    """Response payload for the archive counts endpoint."""

    month: str
    locale: ArticleLocale
    counts: list[ArchiveCountItem] # sorted by date descending (newest first)