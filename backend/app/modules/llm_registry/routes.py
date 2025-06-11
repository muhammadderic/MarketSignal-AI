from fastapi import APIRouter, Depends, HTTPException

from app.shared.schemas import ModelsResponse
from app.modules.llm_registry.llmg_service import LLMRegistryService
from app.modules.llm_registry.dependencies import get_llm_registry_service

router = APIRouter(prefix="/models")


@router.get(
    "/",
    response_model=ModelsResponse,
)
async def list_available_models(
    service: LLMRegistryService = Depends(get_llm_registry_service),
) -> ModelsResponse:
    """
    Retrieve the list of available LLM models.

    The service reads from the local database when populated, and
    falls back to the external provider (Groq) otherwise, persisting
    the results before returning.
    """
    try:
        return await service.fetch_list_models()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching models: {str(e)}",
        )
