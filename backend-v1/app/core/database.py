from pathlib import Path
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings

database_url = settings.DATABASE_URL

# SQLite async URLs must use an async driver, such as aiosqlite.
if database_url.startswith("sqlite:///"):
    database_url = database_url.replace(
        "sqlite:///", "sqlite+aiosqlite:///", 1
    )

if database_url.startswith("sqlite:///./"):
    # database.py is located in backend/app/core/.
    project_root = Path(__file__).resolve().parents[3]
    relative_path = database_url.removeprefix("sqlite:///./")
    database_path = project_root / relative_path

    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"

engine = create_async_engine(
    database_url,
    echo=False,
)

if database_url.startswith("sqlite+aiosqlite://"):
    @event.listens_for(engine.sync_engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection, connection_record
    ):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)