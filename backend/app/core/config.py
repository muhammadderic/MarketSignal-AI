from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve absolute paths relative to this file (app/core/config.py)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
APP_DIR: Path = PROJECT_ROOT / "app"
DATA_DIR: Path = PROJECT_ROOT / "data"

class Settings(BaseSettings):
    # === DATABASE ===
    # Default filename if environment variable DB_FILENAME is not set
    DB_FILENAME: str = "database.db"

    @property
    def DB_FILE_PATH(self) -> Path:
        return DATA_DIR / self.DB_FILENAME

    @property
    def DATABASE_URL(self) -> str:
        return f"sqlite:///{self.DB_FILE_PATH}"

    # === Pydantic v2.0+ Configuration ===
    # Reads a local .env file if it exists automatically
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# === Automatic DB Directory and File Creation ===
DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.DB_FILE_PATH.touch(exist_ok=True)