from pathlib import Path
from functools import lru_cache
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or ``.env``.

    Attributes:
        GROQ_API_KEY: Groq LLM API credential. Stored as ``SecretStr`` so it is
            never rendered in logs or error messages.
        DATABASE_URL: SQLAlchemy async connection string for the local SQLite
            database.
        LOG_LEVEL: Python logging level name (e.g. ``INFO``, ``DEBUG``).
        HOST: Bind address for the local Uvicorn server.
        PORT: Bind port for the local Uvicorn server.
        ENVIRONMENT: Deployment environment label (``development`` or
            ``production``).
    """

    APP_NAME: str = "MarketSignal AI API"

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/marketsignal.db"

    CORS_ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    GROQ_API_KEY: SecretStr = Field(
        ...,
        description="Groq LLM API key. Required; no default provided.",
    )
    LOG_LEVEL: str = Field(default="INFO", description="Application log level.")
    HOST: str = Field(default="127.0.0.1", description="Uvicorn bind host.")
    PORT: int = Field(default=8000, ge=1, le=65535, description="Uvicorn bind port.")
    ENVIRONMENT: str = Field(
        default="development",
        description="Deployment environment label.",
    )

    @model_validator(mode="after")
    def _ensure_sqlite_paths(self) -> "Settings":
        """Create the SQLite parent directory and file if they do not exist.

        SQLite refuses to open a database whose parent directory is missing, and
        Alembic ``--autogenerate`` requires the file to exist so it can inspect
        the current schema. This validator normalizes that behavior regardless
        of whether the URL is absolute or relative.
        """
        url = self.DATABASE_URL
        if not url.startswith("sqlite"):
            return self

        # Strip the SQLAlchemy scheme prefix: ``sqlite+aiosqlite:///`` →
        # ``sqlite:///`` → path portion. Handles both 3-slash (relative) and
        # 4-slash (absolute) forms.
        if ":///" not in url:
            return self
        path_part = url.split(":///", 1)[1]

        # Ignore in-memory databases.
        if not path_part or path_part.startswith(":memory:"):
            return self

        # Query string suffix (e.g. ``?cache=shared``) is not part of the path.
        path_part = path_part.split("?", 1)[0]

        db_path = Path(path_part).expanduser()
        if not db_path.is_absolute():
            db_path = (Path.cwd() / db_path).resolve()

        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.touch(exist_ok=True)
        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()