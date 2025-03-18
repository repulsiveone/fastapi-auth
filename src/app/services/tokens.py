from fastapi import Cookie
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Union, Any
from sqlalchemy.ext.asyncio import AsyncSession
import os
from sqlalchemy.exc import OperationalError, SQLAlchemyError, NoResultFound
from dotenv import load_dotenv
from sqlalchemy import select
from fastapi import HTTPException, status

from app.logger import logger
from app.models.auth import TokenModel


# для работы с .env
load_dotenv()

# ДлЯ ТЕСВТОВ!
# ACCESS_TOKEN_EXPIRE_MINUTES = 1

ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 минут
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 дней
ALGORITHM = "HS256"
JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']   # обязательно сохранять в секрете
JWT_REFRESH_SECRET_KEY = os.environ['JWT_REFRESH_SECRET_KEY']   # обязательно сохранять в секрете

# функция для создания access JWT токена
def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt

# функция для создания refresh JWT токена
def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
    return encoded_jwt

# функция для обновления access токена
async def refresh_access_token(refresh_token: str, db: AsyncSession):
    ...
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # проверяем наличие токена в базе данных
        statement = select(TokenModel).where(TokenModel.token==refresh_token)
        token_check = await db.execute(statement)
        result = token_check.scalar_one_or_none()
        if result is not None:
            # пробуем раскодировать токен
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
            # создаем новый access токен
            new_access_token = create_access_token(email)
            return {'access_token': new_access_token, 'token_type': 'bearer'}
        else:
            raise HTTPException(status_code=401, detail='Refresh token expired or not found')
    except OperationalError as e:
        logger.error(f"Ошибка соединения с базой данных: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
    except NoResultFound as e:
        logger.error(f"Данные не найдены: {e}")
        raise credentials_exception
    except SQLAlchemyError as e:
        logger.error(f"Ошибка SQLAlchemy: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException as e:
        raise


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