"""
SQLAlchemy async database engine and session management.
Uses aiosqlite for async SQLite support.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        # Ensure database parent directory exists
        settings.data_dir
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            future=True,
        )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db():
    """FastAPI dependency for database sessions."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def _column_exists(conn, table: str, column: str) -> bool:
    r = await conn.execute(text(f"PRAGMA table_info({table})"))
    rows = r.fetchall()
    return any(row[1] == column for row in rows)


async def migrate_schema(conn) -> None:
    """Apply additive SQLite migrations for existing databases."""
    # resumes.dataset_split
    if not await _column_exists(conn, "resumes", "dataset_split"):
        await conn.execute(text("ALTER TABLE resumes ADD COLUMN dataset_split VARCHAR(10)"))

    # iteration_metrics extended columns
    for col, ddl in (
        ("train_accuracy", "ALTER TABLE iteration_metrics ADD COLUMN train_accuracy FLOAT"),
        ("val_accuracy", "ALTER TABLE iteration_metrics ADD COLUMN val_accuracy FLOAT"),
        ("test_accuracy", "ALTER TABLE iteration_metrics ADD COLUMN test_accuracy FLOAT"),
        ("overfit_gap", "ALTER TABLE iteration_metrics ADD COLUMN overfit_gap FLOAT"),
        ("stop_reason", "ALTER TABLE iteration_metrics ADD COLUMN stop_reason VARCHAR(64)"),
    ):
        if not await _column_exists(conn, "iteration_metrics", col):
            await conn.execute(text(ddl))


async def init_db():
    """Create all tables and run lightweight migrations."""
    engine = get_engine()
    async with engine.begin() as conn:
        from backend.models.db_models import (  # noqa: F401
            CandidatePrediction,
            CoreValue,
            Evaluation,
            IterationMetrics,
            Job,
            LLMUsageLog,
            PromptEvolutionLog,
            Resume,
            TalentLens,
        )
        await conn.run_sync(Base.metadata.create_all)
        await migrate_schema(conn)
