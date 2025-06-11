from datetime import datetime
from pydantic import BaseModel, Field


class ExternalModelInfo(BaseModel):
    """Persistence-agnostic schema for an LLM model coming from an
    external provider.

    Has no `id` because the DB assigns the primary key on insert, and
    no wrapper container because the adapter returns a plain list —
    counting is the service's responsibility.
    """

    model_id: str = Field(..., description="Model identifier from the provider")
    object_type: str = Field(..., description="Object type")
    owned_by: str = Field(..., description="Owner of the model")
    active: bool = Field(default=True, description="Whether the model is currently active")
    context_window: int = Field(..., description="Maximum context window token limit")
    created_date: datetime = Field(..., description="UTC-aware creation timestamp")
    