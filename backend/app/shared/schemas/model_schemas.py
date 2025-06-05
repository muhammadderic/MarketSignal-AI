from pydantic import BaseModel, Field
from typing import Optional


class ModelInfo(BaseModel):
    id: str = Field(..., description="Model identifier")
    object: str = Field(..., description="Object type")
    created: Optional[int] = Field(None, description="Creation timestamp")
    owned_by: Optional[str] = Field(None, description="Owner of the model")
    active: bool = Field(default=True, description="Whether the model is currently active")
    context_window: Optional[int] = Field(None, description="Maximum context window token limit")


class ModelsResponse(BaseModel):
    models: list[ModelInfo] = Field(..., description="List of available models")
    count: int = Field(default=0, description="Total number of models available")