from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Union, Any
import os
from dotenv import load_dotenv
from sqlmodel import Session, create_engine
from sqlalchemy import select
from fastapi import Depends

from app.models.auth import UserAuthModel
from app.db import engine

# ДЛЯ ТЕСТОВ!
# engine = create_engine("sqlite:///test.db", echo=True)

# для работы с .env
load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 минут
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 дней
ALGORITHM = "HS256"
JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']   # обязательно сохранять в секрете
JWT_REFRESH_SECRET_KEY = os.environ['JWT_REFRESH_SECRET_KEY']   # обязательно сохранять в секрете

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

# функция для создания JWT токена
def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
    return encoded_jwt

# функция для входа пользователя
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        statement = select(UserAuthModel).where(UserAuthModel.email == form_data.username) # form_data.username содержит email в OAuth2PasswordRequestForm
        user = session.exec(statement).scalars().first()
    if user is None:
        ...
        return None
    # TODO проверка пароля

    # возвращает JWT токены
    return {
        "access_token": create_access_token(user.email),
        "refresh_token": create_refresh_token(user.email),
    }