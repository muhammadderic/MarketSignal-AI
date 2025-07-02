"""Global pytest fixtures for the MarketSignal AI backend.

Provides:

* ``test_db_engine`` — a per-module async SQLAlchemy engine backed by a fresh
  file-based SQLite database in WAL mode, with all Alembic migrations applied.
* ``db_session`` — an ``AsyncSession`` bound to an outer transaction that is
  rolled back after each test, keeping tests isolated and fast.
* ``async_client`` — an ``httpx.AsyncClient`` bound to the FastAPI ``app`` with
  ``get_async_db`` overridden to yield the fixture ``db_session``.

All external I/O is disabled in tests: fixtures never construct
``app.db.database.async_engine`` (which uses the developer's local DB) and no
live HTTP calls are performed.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from httpx import ASGITransport, AsyncClient

from app.db.database import get_async_db
from main import app as fastapi_app

REPO_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"


def _apply_sqlite_pragmas(dbapi_connection: object, _record: object) -> None:
    """Mirror production pragmas on every test connection (ARC-002)."""
    cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
    try:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
    finally:
        cursor.close()


def _run_alembic_upgrade(database_url: str) -> None:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    print(f"[conftest] Running Alembic against: {database_url}")
    command.upgrade(cfg, "head")

    # database_url format: sqlite+aiosqlite:///C:/path/to/file.db
    prefix = "sqlite+aiosqlite:///"
    assert database_url.startswith(prefix), database_url
    db_file = Path(database_url[len(prefix):])
    print(f"[conftest] DB exists: {db_file.exists()}  path={db_file}")

    import sqlite3
    if db_file.exists():
        with sqlite3.connect(db_file) as conn:
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
            print(f"[conftest] tables after upgrade: {sorted(tables)}")
            assert "articles" in tables, f"articles missing; found: {sorted(tables)}"


@pytest.fixture(scope="module")
def test_database_url(tmp_path_factory: pytest.TempPathFactory) -> Generator[str, None, None]:
    db_dir = tmp_path_factory.mktemp("marketsignal-test-db")
    db_path = (db_dir / "test_marketsignal.db").resolve()
    url = f"sqlite+aiosqlite:///{db_path.as_posix()}"

    _run_alembic_upgrade(url)

    yield url


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def test_db_engine(test_database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """Module-scoped async engine bound to the migrated test database."""
    engine = create_async_engine(test_database_url, echo=False, future=True)
    event.listen(engine.sync_engine, "connect", _apply_sqlite_pragmas)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a session bound to an outer transaction rolled back per test.

    This guarantees each test starts from the same migrated schema with no
    residual rows, without re-running Alembic between tests.
    """
    connection = await test_db_engine.connect()
    outer_tx = await connection.begin()

    session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )

    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

    await outer_tx.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """ASGI test client with ``get_async_db`` overridden to ``db_session``."""

    async def _override_get_async_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_async_db] = _override_get_async_db
    transport = ASGITransport(app=fastapi_app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        fastapi_app.dependency_overrides.pop(get_async_db, None)
