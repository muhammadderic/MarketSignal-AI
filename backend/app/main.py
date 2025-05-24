from fastapi import FastAPI
from app.api.router import router as scoring_routes
from app.modules.news.routes import router as news_routes

app = FastAPI(title="MarketSignal AI")
app.include_router(scoring_routes)
app.include_router(news_routes)
