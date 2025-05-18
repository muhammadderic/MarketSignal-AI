from fastapi import FastAPI
from app.api.router import router

app = FastAPI(title="MarketSignal AI")
app.include_router(router)
