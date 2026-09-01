from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config.config import settings

async_engine = create_async_engine(url=settings.DATABASE_URL_aiosqlite,echo=True)
async_session_factory = async_sessionmaker(async_engine,expire_on_commit=False)