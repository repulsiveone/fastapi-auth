from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import OperationalError, IntegrityError, SQLAlchemyError, NoResultFound

from app.models.auth import UserAuthModel, TokenModel
from app.db import get_session
from hashers import get_password
from app.logger import logger
from .tokens import create_access_token, create_refresh_token, decode_access_token

# ДЛЯ ТЕСТОВ!
# engine = create_async_engine("sqlite+aiosqlite:///test.db", echo=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

# функция для входа пользователя
# ожидает на вход email и password, возвращает словарь с JWT-токенами
######################################################
##  access_token хранить в локальной переменной JS  ##
##  refresh_token хранить в куки HttpOnly           ##
######################################################
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)) -> dict:
    try:
        statement = select(UserAuthModel).where(UserAuthModel.email == form_data.username) # form_data.username содержит email в OAuth2PasswordRequestForm
        result = await db.execute(statement)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password")
        # проверка правильности пароля
        if get_password(form_data.password, statement.password) is False:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password")
    
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
    
    except OperationalError as e:
        logger.error(f"Ошибка соединения с базой данных: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
    except IntegrityError as e:
        logger.error(f"Ошибка целостности данных: {e}")
        raise HTTPException(status_code=400, detail="Data integrity error")
    except SQLAlchemyError as e:
        logger.error(f"Ошибка SQLAlchemy: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    

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
    try:
        statement = select(UserAuthModel).where(UserAuthModel.email == email)
        result = await db.execute(statement)
        user = result.scalars().first()

        if user is None:
            raise credentials_exception
        return user
    except OperationalError as e:
        logger.error(f"Ошибка соединения с базой данных: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
    except NoResultFound as e:
        logger.error(f"Данные не найдены: {e}")
        raise credentials_exception
    except SQLAlchemyError as e:
        logger.error(f"Ошибка SQLAlchemy: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    
    
