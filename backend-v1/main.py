from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.security import configure_security

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)

# === MIDDLEWARES ===
configure_security(app)

# === GLOBAL ERROR HANDLER ===
register_exception_handlers(app)


# === ROUTES ===
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Return the basic application health status."""
    return {"status": "ok"}