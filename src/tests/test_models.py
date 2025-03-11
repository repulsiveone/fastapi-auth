import pytest
from app.models.auth import UserAuthModel, TokenModel, ChangePasswordRequest
from app.db import get_session
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.oauth import current_user, create_refresh_token


@pytest.mark.asyncio
async def test_tokenmodel(test_user, test_session: AsyncSession):
    token = TokenModel(token=create_refresh_token(test_user.email), user_id=test_user.id)

    assert token is not None
    assert token.user_id == 1
    assert token.invalidated == False

@pytest.mark.asyncio
async def test_usermodel(test_session: AsyncSession):
    user = await UserAuthModel.create_user(
        username='xpfxz',
        email='xpfxz@bk.ru',
        password='qwe123QW$#!',
        session=test_session
        )

    assert user.id is not None
    assert user.username == 'xpfxz'
    assert user.email == 'xpfxz@bk.ru'
    assert user.is_active == True
    assert user.is_superuser == False

@pytest.mark.asyncio
async def test_usermodel_superuser(test_session: AsyncSession):
    user = await UserAuthModel.create_superuser(
        username='xpfxz',
        email='xpfxz@bk.ru',
        password='qwe123QW$#!',
        session=test_session
        )
    
    assert user.id is not None
    assert user.is_active == True
    assert user.is_superuser == True

@pytest.mark.asyncio
async def test_usermodel_validation_errors(test_session: AsyncSession):
    with pytest.raises(ValidationError) as exc_info:
        user = await UserAuthModel.create_user(username='xpfxz', email='xpfxz@bk', password='qwerty32', session=test_session)

    errors = exc_info.value.errors()

    assert errors[0]['msg'] == "Value error, Must be a valid email address"
    assert errors[1]['msg'] == "Value error, Password are incorrect"

@pytest.mark.asyncio
async def test_change_password_request(test_user):
    request_data = {
        'current_password': test_user.password,
        'new_password': 'newPassword!@32#'
    }
    change = ChangePasswordRequest(**request_data)

    assert change.new_password == 'newPassword!@32#'
    