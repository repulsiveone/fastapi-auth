import pytest
from fastapi.security import OAuth2PasswordRequestForm

from app.services.oauth import create_access_token, create_refresh_token, login

def test_create_access_token():
    access_token = create_access_token('xpfxz@bk.ru')
    assert access_token is not None

def test_create_refresh_token():
    refresh_token = create_refresh_token('xpfz@bk.ru')
    assert refresh_token is not None

def test_login_success(test_user, test_session):
    form_data = OAuth2PasswordRequestForm(username="test@example.com", password="Passw!@#ord123!")

    user = login(form_data=form_data)

    assert "access_token" in user
    assert "refresh_token" in user

    access_token = user["access_token"]
    refresh_token = user["refresh_token"]
    # проверяем что JWT токен создался и это строка
    assert isinstance(access_token, str)
    assert isinstance(refresh_token, str)

    