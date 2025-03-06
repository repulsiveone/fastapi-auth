import pytest
from sqlmodel import SQLModel, create_engine, Session

from app.models.auth import UserAuthModel, CreateUserModel
from app.services.hashers import make_password

@pytest.fixture(name="test_session")
def session_fixture():
    # Создаем движок для SQLite в памяти
    engine = create_engine("sqlite:///test.db", echo=True)
    
    # Создаем таблицы
    SQLModel.metadata.create_all(engine)
    
    # Возвращаем сессию
    with Session(engine) as session:
        yield session

    # Удаляем все таблицы после завершения теста
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="test_user")
def user_fixture(test_session):
    # Создаём тестового пользователя
    user = UserAuthModel.create_user(
        username="testuser",
        email="test@example.com",
        password="Passw!@#ord123!",
        session=test_session,
    )
    return user