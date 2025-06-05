from fastapi import APIRouter

from app.core.routes.system import router as system_routes
from app.modules.news.routes import router as news_routes
from app.modules.news_scoring.routes import router as news_scoring_routes

basic_router = APIRouter(prefix="/api/v1")

# === FEATURE ROUTERS ===
# BASIC
basic_router.include_router(system_routes, tags=["System"])
basic_router.include_router(news_routes, tags=["News"])
basic_router.include_router(news_scoring_routes, tags=["News Scoring"])