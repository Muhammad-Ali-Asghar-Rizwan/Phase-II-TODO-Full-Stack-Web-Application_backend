"""Database configuration and session management supporting both PostgreSQL and SQLite."""

import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Handle different database types
if DATABASE_URL.startswith("sqlite"):
    # For SQLite, use aiosqlite
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
    
    # Create async engine with connection pooling optimized for serverless
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=1,  # Serverless functions are short-lived, use minimal pool
        max_overflow=0,  # No overflow for serverless
        pool_recycle=300,  # Recycle connections after 5 minutes
        connect_args={"check_same_thread": False},
    )
else:
    # For PostgreSQL, use asyncpg
    # Convert synchronous URL to async for PostgreSQL.
    # NOTE: asyncpg does not accept libpq-style query params like `sslmode`.
    # Neon requires SSL, so we drop those params and enable SSL via connect_args.
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

    # Strip libpq params that break asyncpg
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("?sslmode=require&channel_binding=require", "")
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("&sslmode=require&channel_binding=require", "")
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("?sslmode=require", "")
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("&sslmode=require", "")
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("?channel_binding=require", "")
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("&channel_binding=require", "")

    # Create async engine with connection pooling optimized for serverless
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=1,  # Serverless functions are short-lived, use minimal pool
        max_overflow=0,  # No overflow for serverless
        pool_recycle=300,  # Recycle connections after 5 minutes
        connect_args={
            "ssl": True,
            "server_settings": {"jit": "off"},  # Disable JIT for faster cold starts
            "command_timeout": 10,  # 10 second timeout for commands
        },
    )

# Create async session factory
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with async_session_maker() as session:
        yield session


# Also provide sync engine for migrations (Alembic)
sync_engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


def get_sync_session() -> Session:
    """Get synchronous database session."""
    with Session(sync_engine) as session:
        yield session


async def init_db():
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
