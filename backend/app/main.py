from fastapi import FastAPI
from dotenv import load_dotenv

from app.core.apis.v1 import basic_router

load_dotenv()

app = FastAPI(
    title="MarketSignal AI", 
    version="0.2.0"
)

# === ROUTES ===
app.include_router(basic_router)
