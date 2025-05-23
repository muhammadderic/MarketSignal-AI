from fastapi import APIRouter, HTTPException

from app.schemas import (
    BatchTitleRequest, 
    ScoringResult, 
    ModelsResponse
)
from app.services import PipelineService, ModelsService

router = APIRouter()


@router.get(
    "/models", 
    response_model=ModelsResponse
)
async def list_available_models():
    service = ModelsService()
    try:
        return await service.list_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")

        
@router.post(
    "/score-titles", 
    response_model=list[ScoringResult]
)
async def score_titles(payload: BatchTitleRequest):
    service = PipelineService()
    try:
        return await service.score_titles(payload.titles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Processing Error: {str(e)}")
        