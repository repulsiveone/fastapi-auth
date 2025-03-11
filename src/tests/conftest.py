import pytest_asyncio
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.testclient import TestClient

from app.models.auth import UserAuthModel, CreateUserModel
from app.services.hashers import make_password
from app.services.oauth import login, current_user
from app.main import app

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

@pytest_asyncio.fixture(name="test_current_user")
async def curr_fixture(test_user, test_session: AsyncSession):
    form_data = OAuth2PasswordRequestForm(username="test@example.com", password="Passw!@#ord123!")

    user = await login(form_data=form_data, db=test_session)

    access_token = user['access_token']

    curr = await current_user(access_token, db=test_session)
    return curr