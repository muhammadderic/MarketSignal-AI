from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionFactory


class UnitOfWork:
    def __init__(self) -> None:
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = AsyncSessionFactory()
        return self

    async def __aexit__(
        self, exc_type, exc_value, traceback
    ) -> None:
        try:
            if self.session is not None:
                if exc_type is not None:
                    await self.session.rollback()
        finally:
            if self.session is not None:
                await self.session.close()

    async def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork has not been entered")
        await self.session.commit()

    async def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork has not been entered")
        await self.session.rollback()