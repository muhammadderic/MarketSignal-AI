from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from app.core.apis.v1 import basic_router

load_dotenv()

app = FastAPI(
    title="MarketSignal AI", 
    version="0.2.0"
)

# === MIDDLEWARES ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ROUTES ===
app.include_router(basic_router)
