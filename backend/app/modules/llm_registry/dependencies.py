from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_groq_adapter
from app.integrations.adapters import GroqAdapter
from app.modules.llm_registry.llmg_repo import LLMRegistryRepo
from app.modules.llm_registry.llmg_service import LLMRegistryService


def get_llm_registry_repo(db: Session = Depends(get_db)) -> LLMRegistryRepo:
    """LLM registry repository with database session injection."""
    return LLMRegistryRepo(db=db)


def get_llm_registry_service(
    repo: LLMRegistryRepo = Depends(get_llm_registry_repo),
    adapter: GroqAdapter = Depends(get_groq_adapter),
) -> LLMRegistryService:
    """LLM registry service with repo and adapter injection."""
    return LLMRegistryService(repo=repo, adapter=adapter)
    