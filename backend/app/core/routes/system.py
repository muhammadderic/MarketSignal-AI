from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_groq_adapter
from app.integrations.adapters import GroqAdapter
from app.shared.schemas import ModelsResponse

router = APIRouter()


@router.get(
    "/models", 
    response_model=ModelsResponse
)
async def list_available_models(
    adapter: GroqAdapter = Depends(get_groq_adapter)
):
    try:
        return await adapter.list_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")
