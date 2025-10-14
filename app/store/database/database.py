from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.store.database.sqlalchemy_db import BaseModel

if TYPE_CHECKING:
    from app.web.app import Application


class Database:
    def __init__(self, app: "Application") -> None:
        self.app = app
        self.cls = True

        self.engine: AsyncEngine | None = None
        self._db: type[DeclarativeBase] = BaseModel
        self.session: async_sessionmaker[AsyncSession] | None = None

    async def connect(self, *args: Any, **kwargs: Any) -> None:
        if not self.app.config.database:
            return
        self.engine = create_async_engine(
            "".join(
                [
                    "postgresql+asyncpg://",
                    self.app.config.database.user,
                    ":",
                    str(self.app.config.database.password),
                    "@",
                    self.app.config.database.host,
                    ":",
                    str(self.app.config.database.port),
                    "/",
                    self.app.config.database.database,
                ]
            ),
            echo=True,
            pool_size=10,
            pool_pre_ping=True,
            max_overflow=10,
            future=True,
        )
        self.session = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    async def disconnect(self, *args: Any, **kwargs: Any) -> None:
        await self.engine.dispose()
