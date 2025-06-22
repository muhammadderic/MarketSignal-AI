from pydantic import BaseModel, Field


class ArticleTitleData(BaseModel):
    """Schema for an article's id and title pair."""
    
    id: int = Field(..., description="Article ID")
    title: str = Field(..., description="Article title")
