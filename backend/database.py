from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        from models import MarketSnapshot, AIAnalysis, Signal, Opportunity, Bet, ScanRun, AppSecret  # noqa
        await conn.run_sync(Base.metadata.create_all)

    # Load persisted secrets into runtime store
    import config
    from sqlalchemy import text
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text("SELECT key, value FROM app_secrets"))
            for row in result:
                config._secrets[row.key] = row.value
        except Exception:
            pass  # Table may not exist on very first run
