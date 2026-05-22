"""
database.py — Async SQLAlchemy Engine & Session Factory
Uses asyncpg driver for non-blocking PostgreSQL access.
Provides get_db() as a FastAPI dependency for route handlers.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from backend.app.core.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
# pool_pre_ping=True checks connection health before handing it out
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,       # Log SQL queries only in debug mode
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# ── Session Factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,    # Keep attributes accessible after commit
    autocommit=False,
    autoflush=False,
)


# ── Base Model ────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """All ORM models inherit from this base."""
    pass


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields a database session.
    Automatically commits on success and rolls back on error.

    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Table Creation ────────────────────────────────────────────────────────────
async def create_all_tables():
    """
    Create all database tables if they don't exist.
    Called once on application startup via lifespan event.

    IMPORTANT: All models MUST be imported here so SQLAlchemy's Base.metadata
    is populated before create_all is called. Without this, no tables are created.
    """
    # Import all models to register them with Base.metadata
    import backend.app.models.student      # noqa: F401
    import backend.app.models.faculty      # noqa: F401
    import backend.app.models.subject      # noqa: F401
    import backend.app.models.attendance   # noqa: F401
    import backend.app.models.timetable    # noqa: F401
    import backend.app.models.notice       # noqa: F401
    import backend.app.models.chat_history # noqa: F401
    import backend.app.models.assignment   # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
