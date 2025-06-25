from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)


# === ROUTES ===
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Return the basic application health status."""
    return {"status": "ok"}