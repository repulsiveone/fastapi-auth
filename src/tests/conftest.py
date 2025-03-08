import pytest_asyncio
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.auth import UserAuthModel, CreateUserModel
from app.services.hashers import make_password

@pytest_asyncio.fixture(name="test_session")
async def session_fixture():
    # Создаем движок для SQLite
    engine = create_async_engine("sqlite+aiosqlite:///test.db", echo=True)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Создаем таблицы асинхронно 
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Возвращаем сессию
    async with async_session() as session:
        yield session

    # Удаляем все таблицы асинхронно после завершения теста
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest_asyncio.fixture(name="test_user")
async def user_fixture(test_session: AsyncSession):
    # Создаём тестового пользователя
    user = await UserAuthModel.create_user(
        username="testuser",
        email="test@example.com",
        password="Passw!@#ord123!",
        session=test_session,
    )
    return user