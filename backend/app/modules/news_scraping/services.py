import asyncio
import logging

from app.integrations.adapters import GoogleNewsLinkAdapter
from app.modules.news_scraping.constants import LinkResolutionStatus
from app.modules.news_scraping.schemas import ResolvedLinkResult
from app.modules.news_scraping.utils import LinkDecodingError
from app.modules.news_scraping.repositories import NewsArticleRepository

logger = logging.getLogger(__name__)

MAX_CONCURRENT_RESOLUTIONS = 5


class LinkResolutionService:
    def __init__(self, repository: NewsArticleRepository, adapter: GoogleNewsLinkAdapter):
        self._repository = repository
        self._adapter = adapter
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_RESOLUTIONS)

    async def resolve_links(self, article_ids: list[int]) -> list[ResolvedLinkResult]:
        articles = self._repository.get_by_ids(article_ids)
        found_ids = {a.id for a in articles}

        # Resolve concurrently (network-bound only, no DB access here —
        # AsyncSession isn't safe to use concurrently from multiple coroutines).
        resolved = await asyncio.gather(*(self._resolve_one(a.id, a.link) for a in articles))

        results: list[ResolvedLinkResult] = []
        for result in resolved:
            self._repository.update_resolution(result.id, result.resolved_link, result.status)
            results.append(result)

        results.extend(
            ResolvedLinkResult(id=missing_id, status=LinkResolutionStatus.FAILED, error="Article not found")
            for missing_id in article_ids
            if missing_id not in found_ids
        )
        return results

    async def _resolve_one(self, article_id: int, google_link: str | None) -> ResolvedLinkResult:
        if not google_link:
            return ResolvedLinkResult(id=article_id, status=LinkResolutionStatus.FAILED, error="No link stored")

        async with self._semaphore:
            try:
                resolved_url = await self._adapter.resolve(google_link)
            except LinkDecodingError as exc:
                logger.warning("Failed to resolve link for article %s: %s", article_id, exc)
                return ResolvedLinkResult(id=article_id, status=LinkResolutionStatus.FAILED, error=str(exc))

        return ResolvedLinkResult(id=article_id, status=LinkResolutionStatus.RESOLVED, resolved_link=resolved_url)