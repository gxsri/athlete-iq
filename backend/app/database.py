import logging
import sys
import os
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PGUUID

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("athleteiq")

DATABASE_URL = os.getenv("ATHLETEIQ_DATABASE_URL", "sqlite+aiosqlite:///./athleteiq.db")
_use_sqlite = "sqlite" in DATABASE_URL


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL UUID type, otherwise CHAR(36) with UUID-to-string conversion.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID())
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(value)
        return value


engine = create_async_engine(DATABASE_URL, echo=False, **({"connect_args": {"check_same_thread": False}} if _use_sqlite else {"pool_size": 20, "max_overflow": 10}))
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if _use_sqlite:
        import sqlite3
        sqlite3.register_adapter(uuid.UUID, lambda u: str(u))
        sqlite3.register_converter("UUID", lambda b: uuid.UUID(b.decode()))
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
