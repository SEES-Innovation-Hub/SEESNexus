from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

if settings.is_sqlite:
    engine = create_async_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        # Managed Postgres closes idle connections; check before use rather
        # than hand a request a dead one.
        pool_pre_ping=True,
        pool_recycle=1800,
    )
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_models() -> None:
    """Create tables. Used for local/dev/test convenience; production uses Alembic (§9.2)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
