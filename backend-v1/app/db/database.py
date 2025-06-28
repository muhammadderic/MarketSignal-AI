"""Async SQLAlchemy engine, session factory, and FastAPI dependency.

Configures SQLite in Write-Ahead Logging (WAL) mode with ``synchronous=NORMAL``
for safe high-throughput local writes (ARC-002). The declarative ``Base`` is the
metadata root used by Alembic autogenerate and by the ``Article`` model.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative ORM metadata root for all MarketSignal AI models."""


def _set_sqlite_pragmas(dbapi_connection: object, _connection_record: object) -> None:
    """Apply WAL and NORMAL synchronous pragmas on every new SQLite connection.

    Args:
        dbapi_connection: Raw ``aiosqlite``-backed sqlite3 connection.
        _connection_record: SQLAlchemy pool record (unused).
    """
    cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
    try:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
    finally:
        cursor.close()


async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

event.listen(async_engine.sync_engine, "connect", _set_sqlite_pragmas)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an ``AsyncSession`` with automatic lifecycle.

    Commits on successful request completion; rolls back on unhandled
    exceptions. The session is always closed by the context manager.

    Yields:
        An active :class:`AsyncSession` bound to the async engine.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise