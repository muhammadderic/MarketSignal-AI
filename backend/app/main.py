from fastapi import FastAPI

from app.core.apis.v1 import basic_router

app = FastAPI(
    title="MarketSignal AI", 
    version="0.1.0"
)

# === ROUTES ===
app.include_router(basic_router)
