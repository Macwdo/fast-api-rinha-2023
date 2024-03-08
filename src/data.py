from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

async_engine = create_async_engine(
    'postgresql+asyncpg://postgres:12345@localhost/db', echo=True
)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class PersonEntity(Base):
    __tablename__ = 'person'
    id: Mapped[UUID] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    birth_date: Mapped[date]
    stack: Mapped[str]


async_session = async_sessionmaker(async_engine, expire_on_commit=False)


async def create_all():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
