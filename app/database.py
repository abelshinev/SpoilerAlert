import aiosqlite
from app.config import settings
from collections.abc import AsyncGenerator

async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    FastAPI dependency that provides an async SQLite connection.
    Ensures foreign keys are enabled for each connection.
    """
    async with aiosqlite.connect(settings.DATABASE_URL) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        yield db
