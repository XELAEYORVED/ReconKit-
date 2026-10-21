"""Async database session management for ReconKit."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import get_settings
from .models import Base

_engine = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _ensure_engine() -> async_sessionmaker[AsyncSession]:
    global _engine, _sessionmaker
    if _sessionmaker is None:
        settings = get_settings()
        _engine = create_async_engine(settings.database_url, future=True, echo=False)
        _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    return _sessionmaker


async def init_db() -> None:
    """Create all tables if they do not exist."""
    _ensure_engine()
    assert _engine is not None
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope around a series of operations."""
    maker = _ensure_engine()
    session = maker()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields a session (commits on success)."""
    maker = _ensure_engine()
    session = maker()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
