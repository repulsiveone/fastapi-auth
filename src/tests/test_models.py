import pytest
from app.models.auth import UserAuthModel
from app.db import get_session
from pydantic import ValidationError


def test_usermodel(test_session):
    user = UserAuthModel.create_user(username='xpfxz', email='xpfxz@bk.ru', password='qwe123QW$#!', session=test_session)
    
    assert user.id is not None
    assert user.username == 'xpfxz'
    assert user.email == 'xpfxz@bk.ru'


def test_usermodel_validation_errors(test_session):
    with pytest.raises(ValidationError) as exc_info:
        user = UserAuthModel.create_user(username='xpfxz', email='xpfxz@bk', password='qwerty32', session=test_session)

    errors = exc_info.value.errors()

    assert errors[0]['msg'] == "Value error, Must be a valid email address"
    assert errors[1]['msg'] == "Value error, Password are incorrect"
    