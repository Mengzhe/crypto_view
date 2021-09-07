from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

# DATABASE_URL = "sqlite+aiosqlite:///./test.db"

db_password = "postgres"
DATABASE_URL = f"postgresql+asyncpg://postgres:{db_password}@localhost:5434/crypto"

engine = create_async_engine(DATABASE_URL, echo=False)

Base = declarative_base()
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# clear and recreate the database table
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

# Dependency
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session