from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Union, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import os
from dotenv import load_dotenv
from sqlmodel import Session, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select
from fastapi import Depends, HTTPException, status, Cookie

from app.models.auth import UserAuthModel, TokenModel
from app.db import engine, get_session

# ДЛЯ ТЕСТОВ!
engine = create_async_engine("sqlite+aiosqlite:///test.db", echo=True)

# для работы с .env
load_dotenv()

# ДлЯ ТЕСВТОВ!
# ACCESS_TOKEN_EXPIRE_MINUTES = 1

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

async def refresh_access_token(refresh_token: str, db: AsyncSession):
    ...
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
# TODO проверка refresh_token в базе данных
    try:
        payload = decode_refresh_token(refresh_token)
        email: str = payload.get('sub')
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Проверяем, что refresh-токен не истек
    if datetime.now(timezone.utc) > datetime.fromtimestamp(payload.get('exp'), timezone.utc):
        raise HTTPException(status_code=401, detail='Refresh token expired')
    
    new_access_token = create_access_token(email)
    return {'access_token': new_access_token, 'token_type': 'bearer'}

# refresh_token: - Это имя, которое используется внутри функции для доступа к значению Cookie.
async def get_refresh_token(refresh_token: str = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail='Refresh token is missing')
    return refresh_token


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, ALGORITHM)
        return payload
    except JWTError:
        return None
    
def decode_refresh_token(token: str):
    try:
        payload = jwt.decode(token, JWT_REFRESH_SECRET_KEY, ALGORITHM)
        return payload
    except JWTError:
        return None


# функция для входа пользователя
# ожидает на вход email и password, возвращает словарь с JWT-токенами
######################################################
##  access_token хранить в локальной переменной JS  ##
##  refresh_token хранить в куки HttpOnly           ##
######################################################
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)) -> dict:
    statement = select(UserAuthModel).where(UserAuthModel.email == form_data.username) # form_data.username содержит email в OAuth2PasswordRequestForm
    result = await db.execute(statement)
    user = result.scalars().first()
    if user is None:
        ...
        return None
    # TODO проверка пароля
    
    refresh_token = create_refresh_token(user.email)

    refresh_token_save = TokenModel(token=refresh_token, user_id=user.id)
    db.add(refresh_token_save)
    await db.commit()
    await db.refresh(refresh_token_save)

    # возвращает JWT токены
    return {
        "access_token": create_access_token(user.email),
        "refresh_token": refresh_token,
    }

async def current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)) -> Optional[UserAuthModel]:
    """
    Возвращает объект UserAuthModel со всей информацие о пользователе
    """
    # исклюяение для невалидных токенов
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # получаем access токен
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    # извлекаем email и получаем всю информацию по пользователю
    email: str = payload.get('sub')
    if email is None:
        raise credentials_exception
    statement = select(UserAuthModel).where(UserAuthModel.email == email)
    result = await db.execute(statement)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception
    return user
    
    
