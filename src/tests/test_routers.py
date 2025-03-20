from fastapi import HTTPException
import pytest
from fastapi.testclient import TestClient
from app.main import app, auth_router
from sqlmodel import Session
from app.models.auth import UserAuthModel, CreateUserModel, TokenModel
from sqlalchemy import select
from app.db import get_session
from app.services.hashers import get_password
from app.services.auth import current_user, login
from app.services.tokens import get_refresh_token, decode_access_token
from fastapi.security import OAuth2PasswordRequestForm
from app.services.roles import require_role

app.include_router(auth_router)

client = TestClient(app)

@pytest.mark.asyncio
async def test_signup(test_user, test_session): # test_user добавлен для заполнения таблицы данными, для првоерки email_exists
    app.dependency_overrides[get_session] = lambda: test_session
    user_data = {
        "username": "testuser",
        "email": "new_test@example.com",
        "password": "Passw!@#ord123!"
    }

    response = client.post('/signup', json=user_data)
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["username"] == user_data["username"]
    assert response_data["email"] == user_data["email"]

    user = await test_session.get(UserAuthModel, response_data["id"])
    assert user is not None
    assert user.username == user_data["username"]
    assert user.email == user_data["email"]
    # проверка что пароль захэширован
    assert user.password != user_data["password"]
    assert get_password(user_data["password"], user.password) == True

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_login(test_user, test_session):
    app.dependency_overrides[get_session] = lambda: test_session
    form_data = {
        "username": "test@example.com",
        "password": "Passw!@#ord123!"
    }

    response = client.post('/login', data=form_data)
    assert response.status_code == 200

    assert 'access_token' in response.json()
    
    assert await get_refresh_token() is not None
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_myself_info(test_user, test_current_user):
    # переопределение зависимостей для теста
    app.dependency_overrides[current_user] = lambda: test_current_user

    response = client.get('/me')

    assert response.status_code == 200

    response_data = response.json()
    assert response_data['username'] == test_user.username
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_refresh_token_response(test_current_user, test_session):
    app.dependency_overrides[get_session] = lambda: test_session
    statement = select(TokenModel).where(TokenModel.user_id == test_current_user.id)
    db_token = await test_session.execute(statement)
    result = db_token.scalar_one_or_none()
    app.dependency_overrides[get_refresh_token] = lambda: result.token

    assert result is not None

    response = client.post('/refresh_token')
    assert response.status_code == 200
    
    response_data = response.json()
    # возвращает access_token в котором access_token и token_type
    assert decode_access_token(response_data['access_token']['access_token'])['sub'] == test_current_user.email

@pytest.mark.asyncio
async def test_logout_response(test_current_user, test_session):
    app.dependency_overrides[get_session] = lambda: test_session
    statement = select(TokenModel).where(TokenModel.user_id == test_current_user.id)
    db_token = await test_session.execute(statement)
    result = db_token.scalar_one_or_none()
    app.dependency_overrides[get_refresh_token] = lambda: result.token
    # проверяем что токен активен
    assert result.invalidated == False

    response = client.post('/logout')
    assert response.status_code == 200
    
    statement = select(TokenModel).where(TokenModel.user_id == test_current_user.id)
    db_token = await test_session.execute(statement)
    result = db_token.scalar_one_or_none()
    # проверяем что токен неактивен
    assert result.invalidated == True

    response_data = response.json()
    assert response_data['message'] == 'Logged out successfully'

@pytest.mark.asyncio
async def test_logout_all_response(test_session, test_current_user):
    app.dependency_overrides[get_session] = lambda: test_session
    app.dependency_overrides[current_user] = lambda: test_current_user

    response = client.post('/logout_all')
    assert response.status_code == 200

    statement = select(TokenModel).where(TokenModel.user_id == test_current_user.id)
    refresh_token = await test_session.execute(statement)
    result = refresh_token.scalars().all()
    # првоеряем что все токены невалидные
    for token in result:
        assert token.invalidated == True

    response_data = response.json()
    assert response_data['message'] == 'Logged out from all devices successfully'

@pytest.mark.asyncio
async def test_change_password(test_session, test_current_user):
    app.dependency_overrides[get_session] = lambda: test_session
    app.dependency_overrides[current_user] = lambda: test_current_user

    password_data = {
        'current_password': "Passw!@#ord123!",
        'new_password': 'newPassword!@32#'
    }

    response = client.post('/change_password', json=password_data)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_admin_success(roles, test_session, test_current_user):
    app.dependency_overrides[current_user] = lambda: test_current_user

    test_result = await UserAuthModel.set_role(test_current_user.id, "admin", test_session)
    check_role = await UserAuthModel.check_user_role(test_current_user.id, test_session)

    response = client.post('/admin')
    assert response.status_code == 200

    assert response.json()["message"] == "success"

@pytest.mark.asyncio
async def test_admin_raise(roles, test_session, test_current_user):
    app.dependency_overrides[current_user] = lambda: test_current_user

    test_result = await UserAuthModel.set_role(test_current_user.id, "user", test_session)
    check_role = await UserAuthModel.check_user_role(test_current_user.id, test_session)

    response = client.post('/admin')
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_none_role(roles, test_session, test_current_user):
    app.dependency_overrides[current_user] = lambda: test_current_user
    response = client.post('/admin')
    assert response.status_code == 403