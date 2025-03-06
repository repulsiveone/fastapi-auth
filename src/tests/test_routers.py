from fastapi.testclient import TestClient
from app.main import app, auth_router
from sqlmodel import Session
from app.models.auth import UserAuthModel, CreateUserModel
from app.db import get_session
from app.services.hashers import get_password

app.include_router(auth_router)

client = TestClient(app)

def test_signup(test_session):
    app.dependency_overrides[get_session] = lambda: test_session
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Passw!@#ord123!"
    }

    response = client.post('/signup', json=user_data)
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["username"] == user_data["username"]
    assert response_data["email"] == user_data["email"]

    user = test_session.get(UserAuthModel, response_data["id"])
    assert user is not None
    assert user.username == user_data["username"]
    assert user.email == user_data["email"]
    # проверка что пароль захэширован
    assert user.password != user_data["password"]
    assert get_password(user_data["password"], user.password) == True

    app.dependency_overrides = {}