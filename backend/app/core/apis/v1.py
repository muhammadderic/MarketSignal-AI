from fastapi import APIRouter

from app.modules.news_scoring.routes import router as news_scoring_routes
from app.modules.llm_registry.routes import router as llmg_routes
from app.modules.news_archieve.router import router as news_archieve_router

basic_router = APIRouter(prefix="/api/v1")

# === FEATURE ROUTERS ===
# BASIC
basic_router.include_router(llmg_routes, tags=["LLM Registry"])
basic_router.include_router(news_scoring_routes, tags=["News Scoring"])
basic_router.include_router(news_archieve_router, tags=["News Archieve"])