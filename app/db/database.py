"""Async SQLAlchemy engine and session lifecycle."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

_settings = get_settings()
engine = create_async_engine(
    _settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    pool_size=_settings.DB_POOL_SIZE,
    max_overflow=_settings.DB_MAX_OVERFLOW,
)
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async session."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create ORM tables when schema is managed by the app (not Alembic)."""
    from app.config import get_settings
    from app.models.db_models import Base

    if get_settings().DATABASE_SCHEMA_MANAGED_BY == "alembic":
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
