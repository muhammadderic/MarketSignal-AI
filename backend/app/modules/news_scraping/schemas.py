from pydantic import BaseModel, Field

from app.modules.news_scraping.constants import LinkResolutionStatus


# === REQUESTS ===

class ResolveLinksRequest(BaseModel):
    article_ids: list[int] = Field(
    ...,
    min_length=1,
    max_length=30,
    description="IDs of NewsArticleData rows to resolve (max 30 per request)",
)


# === RESPONSES ===

class ResolvedLinkResult(BaseModel):
    id: int
    status: LinkResolutionStatus
    resolved_link: str | None = None
    error: str | None = None


class ResolveLinksResponse(BaseModel):
    results: list[ResolvedLinkResult]