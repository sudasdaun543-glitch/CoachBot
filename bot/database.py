from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import DATABASE_URL
from bot.models import Base

# Создаём асинхронный движок (SQLite или PostgreSQL)
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# Фабрика сессий
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """Создаёт все таблицы, если их нет."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Возвращает новую асинхронную сессию."""
    async with async_session_factory() as session:
        yield session
