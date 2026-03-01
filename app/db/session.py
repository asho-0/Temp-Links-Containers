import logging
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from typing import AsyncIterator, Optional

from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.db.exceptions import DBPoolError, DBSessionError, DBTransactionError

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL_asyncpg,
    **settings.engine_options,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


_session_ctx: ContextVar[Optional[AsyncSession]] = ContextVar(
    "_session_ctx", default=None
)


def get_session() -> AsyncSession:
    session = _session_ctx.get()
    if session is None:
        raise DBSessionError(
            "No active session. "
            "Did you add `Depends(db_dependency)` to your route?"
        )
    return session


@asynccontextmanager
async def db_lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Connecting to database…")
    try:
        async with engine.connect() as conn:
            await conn.run_sync(lambda _: None)
        logger.info("Database connection pool ready")
    except SQLAlchemyError as exc:
        logger.critical("Cannot connect to database: %s", exc, exc_info=True)
        raise DBPoolError(f"Could not connect to the database: {exc}") from exc

    yield

    await engine.dispose()
    logger.info("Database connection pool closed")


async def db_dependency() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        token: Token = _session_ctx.set(session)
        logger.debug("Session %s opened", id(session))
        try:
            yield session
        except SQLAlchemyError as exc:
            logger.error("DB error, rolling back: %s", exc, exc_info=True)
            await session.rollback()
            raise DBSessionError(f"Database error: {exc}") from exc
        except Exception:
            await session.rollback()
            raise
        finally:
            _session_ctx.reset(token)
            logger.debug("Session %s closed", id(session))


@asynccontextmanager
async def transaction() -> AsyncIterator[AsyncSession]:
    session = get_session()
    if session.in_transaction():
        logger.debug(
            "Nested transaction (savepoint) on session %s", id(session)
        )
        async with session.begin_nested():
            yield session
        return

    async with session.begin():
        logger.debug("Transaction started on session %s", id(session))
        try:
            yield session
            logger.debug("Transaction committed on session %s", id(session))
        except SQLAlchemyError as exc:
            logger.error(
                "SQLAlchemy error on session %s: %s",
                id(session),
                exc,
                exc_info=True,
            )
            raise DBTransactionError(f"Transaction failed: {exc}") from exc
        except Exception as exc:
            logger.error(
                "Unexpected error on session %s: %s",
                id(session),
                exc,
                exc_info=True,
            )
            raise


async def commit_db_session() -> None:
    session = get_session()
    try:
        await session.commit()
    except SQLAlchemyError as exc:
        logger.error("Commit failed: %s", exc, exc_info=True)
        await session.rollback()
        raise DBTransactionError(f"Commit failed: {exc}") from exc


async def rollback_db_session() -> None:
    try:
        session = get_session()
        await session.rollback()
    except DBSessionError:
        pass
