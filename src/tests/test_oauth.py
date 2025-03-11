import pytest
import time
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException
from app.models.auth import TokenModel
from sqlmodel import select

from app.services.oauth import create_access_token, create_refresh_token, login, decode_access_token, current_user, refresh_access_token


def test_create_access_token():
    access_token = create_access_token('xpfxz@bk.ru')
    assert access_token is not None

def test_create_refresh_token():
    refresh_token = create_refresh_token('xpfz@bk.ru')
    assert refresh_token is not None

@pytest.mark.asyncio
async def test_login_success(test_user, test_session):
    form_data = OAuth2PasswordRequestForm(username="test@example.com", password="Passw!@#ord123!")

    user = await login(form_data=form_data, db=test_session)

    assert "access_token" in user
    assert "refresh_token" in user

    access_token = user["access_token"]
    refresh_token = user["refresh_token"]

    statement = select(TokenModel).where(TokenModel.user_id==1)
    db_token = await test_session.execute(statement)
    result = db_token.scalar_one_or_none()

    assert result is not None
    
    # assert access_token == {'exp': 1741335236, 'sub': 'test@example.com'}
    # assert _access_token(access_token) == True

    # проверяем что JWT токен создался и это строка
    assert isinstance(access_token, str)
    assert isinstance(refresh_token, str)

@pytest.mark.asyncio
async def test_current_user_success(test_user, test_session):
    ...
    form_data = OAuth2PasswordRequestForm(username="test@example.com", password="Passw!@#ord123!")

    user = await login(form_data=form_data, db=test_session)

    access_token = user['access_token']

    curr = await current_user(access_token, db=test_session)

    assert curr is not None
    assert curr.email == "test@example.com"
    

@pytest.mark.asyncio
async def test_current_user_raise(test_user, test_session):
    invalid_token = "yrwey36$YR^rgfg$^&4wfGfysgf"
    
    with pytest.raises(HTTPException) as exc_info:
        await current_user(invalid_token)

    assert exc_info.value.detail == 'Could not validate credentials'


@pytest.mark.asyncio
async def test_refresh_token_raise(test_user, test_session):
    invalid_token = "yrwey36$YR^rgfg$^&4wfGfysgf"
    
    with pytest.raises(HTTPException) as exc_info:
        await current_user(invalid_token)

    assert exc_info.value.detail == 'Could not validate credentials'


@pytest.mark.asyncio
async def test_refresh_token(test_user, test_session):
    form_data = OAuth2PasswordRequestForm(username="test@example.com", password="Passw!@#ord123!")

    user = await login(form_data=form_data, db=test_session)
    token = user['refresh_token']

    new_token = await refresh_access_token(token, test_session)
    
    assert new_token is not None

    curr = await current_user(new_token.get('access_token'), db=test_session)

    assert curr.email == "test@example.com"


# установить ACCESS_TOKEN_EXPIRE_MINUTES = 1 для правильной работы теста
# @pytest.mark.asyncio
# async def test_refresh_work(test_user, test_session):
#     form_data = OAuth2PasswordRequestForm(username="test@example.com", password="Passw!@#ord123!")

#     user = await login(form_data=form_data, db=test_session)
#     token = user['access_token']
#     ref_token = user['refresh_token']

#     curr = await current_user(token, db=test_session)

#     assert curr.email == "test@example.com"

#     time.sleep(80)

#     with pytest.raises(HTTPException) as exc_info:
#         await current_user(token, db=test_session)

#     assert exc_info.value.detail == 'Could not validate credentials'

#     new_token = await refresh_token(ref_token)
    
#     assert new_token is not None

#     curr = await current_user(new_token.get('access_token'), db=test_session)

#     assert curr.email == "test@example.com"
