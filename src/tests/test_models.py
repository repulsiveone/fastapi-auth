import pytest
from app.models.auth import UserAuthModel
from app.db import get_session
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

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
    