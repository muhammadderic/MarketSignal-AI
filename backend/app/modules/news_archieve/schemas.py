from datetime import date as date_type
from pydantic import BaseModel, Field

from app.modules.news.news_constants import ArticleLocale


class ArchiveCountItem(BaseModel):
    """A single per-day article count."""

    date: date_type
    total: int = Field(..., ge=1)


class ArchiveCountsResponse(BaseModel):
    """Response payload for the archive counts endpoint."""

    month: str
    locale: ArticleLocale
    counts: list[ArchiveCountItem]