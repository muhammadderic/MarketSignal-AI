from fastapi import FastAPI

from app.api.router import router as scoring_routes
from app.modules.news.routes import router as news_routes
from app.modules.news_scoring.routes import router as news_scoring_routes

app = FastAPI(
    title="MarketSignal AI", 
    version="0.1.0"
)

# === ROUTES ===
app.include_router(scoring_routes)
app.include_router(news_routes)
app.include_router(news_scoring_routes)
