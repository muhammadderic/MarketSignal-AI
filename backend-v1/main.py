from fastapi import FastAPI


app = FastAPI(
    title="MarketSignal AI API",
    version="1.0.0",
)


# === ROUTES ===
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Return the basic application health status."""
    return {"status": "ok"}