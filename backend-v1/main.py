from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan
)


# === ROUTES ===
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Return the basic application health status."""
    return {"status": "ok"}