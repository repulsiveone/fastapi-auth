import pytest
from sqlmodel import SQLModel, create_engine, Session
from app.models.auth import UserAuthModel, CreateUserModel

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
