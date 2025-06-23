from fastapi import APIRouter, Depends

from app.modules.news_scraping.dependencies import get_link_resolution_service
from app.modules.news_scraping.schemas import ResolveLinksRequest, ResolveLinksResponse
from app.modules.news_scraping.services import LinkResolutionService

router = APIRouter(prefix="/news/scraping")


@router.post("/resolve-links", response_model=ResolveLinksResponse)
async def resolve_links(
    payload: ResolveLinksRequest,
    service: LinkResolutionService = Depends(get_link_resolution_service),
) -> ResolveLinksResponse:
    results = await service.resolve_links(payload.article_ids)
    return ResolveLinksResponse(results=results)