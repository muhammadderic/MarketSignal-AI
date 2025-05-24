from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL, 
    # SQLite multi-threading support
    connect_args={"check_same_thread": False}
)

# Performance Pragmas via SQLAlchemy Events
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # Enable Write-Ahead Logging (WAL) mode for concurrent reads and writes
    cursor.execute("PRAGMA journal_mode=WAL;")
    # Optimize disk synchronization (NORMAL is safe and much faster in WAL mode)
    cursor.execute("PRAGMA synchronous=NORMAL;")
    # Store temporary tables and indices in system memory instead of disk
    cursor.execute("PRAGMA temp_store=MEMORY;")
    # Increase cache size to 2000 pages (roughly 8MB) to keep hot data in RAM
    cursor.execute("PRAGMA cache_size=-2000;")
    # Forces SQLite to execute your ON DELETE CASCADE constraints
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

Base = declarative_base()

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()