from fastapi import Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import ValidationError


from app.db import get_session
from app.models.auth import UserAuthModel, CreateUserModel, TokenModel, ChangePasswordRequest
from app.services.auth import login, current_user
from app.services.tokens import refresh_access_token, get_refresh_token
from app.services.hashers import get_password, make_password
from app.logger import logger
from app.services.roles import require_role

router = APIRouter()


@router.get('/me')
async def get_myself_info(current_user = Depends(current_user)) -> dict:
    """
    Возврашает информацию о пользователе в виде словаря (пароль не передается)
    """
    curr_user: Optional[UserAuthModel] = current_user
    user_info = {
        'id': curr_user.id,
        'username': curr_user.username,
        'email': curr_user.email,
    }
    return user_info


@router.post('/signup')
async def signup(user: CreateUserModel, session: AsyncSession=Depends(get_session)):
    try:
        result_user = await UserAuthModel.create_user(username=user.username, email=user.email, password=user.password, session=session)
        return result_user
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка базы данных: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        await session.rollback()
        logger.error(f"{e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# возвращает слоаврь с JWT-токенами
@router.post('/login')
async def signin(
    response: Response,
    form_data: OAuth2PasswordRequestForm=Depends(),
    session: AsyncSession=Depends(get_session)) -> dict:

    user = await login(form_data=form_data, db=session)

    # устанавливаем refresk_token в cookies
    response.set_cookie(
        key="refresh_token",
        value=user["refresh_token"],
        httponly=True, # Запрещаем доступ к cookie через JavaScript
        max_age=30 * 24 * 60 * 60,
        samesite='lax', # Защита от CSRF
        secure=True, # Использовать только через HTTPS
    )
    # access_token должен храниться в переменной JavaScript
    return {'access_token': user['access_token']}


"""
    Для работы на практике это должно быть реализовано на стороне клиента:
    1. Клиент отправляет запрос на защищенный эндпоинт c access-токеном.
    2. Если access-токен истек, сервер возвращает ошибку 401 Unauthorized.
    3. Клиент автоматически отправляет запрос на /refresh-token, чтобы получить новый access-токен.
    4. После получения нового access-токена клиент повторяет исходный запрос.
    5. Если refresh-токен также истек, клиент перенаправляет пользователя на страницу входа.
"""
@router.post('/refresh_token')
async def refresh_token(
    refresh_token: str = Depends(get_refresh_token),
    session: AsyncSession = Depends(get_session)
):
    new_access_token = await refresh_access_token(refresh_token, session)
    # возвращает access_token в котором access_token и token_type
    return {'access_token': new_access_token}

@router.post('/logout')
async def logout(
    response: Response,
    refresh_token: str = Depends(get_refresh_token),
    session: AsyncSession = Depends(get_session)
):
    """
    Выход из системы (отзыв конкретного refresh токена)
    """
    # ищем refresh_token в базе данных
    try:
        statement = select(TokenModel).where(TokenModel.token == refresh_token)
        db_token = await session.execute(statement)
        result = db_token.scalar_one_or_none()

        if not result:
            raise HTTPException(
                status_code=404, detail="Refresh token not found"
            )
        
        # помечаем токен как недействительный
        result.invalidated = True
        await session.commit()
        await session.refresh(result)
        response.delete_cookie(key="refresh_token")

        headers = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        content = {"message": "Logged out successfully"}
        return JSONResponse(content=content, headers=headers)
    
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка базы данных при изменении username: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post('/logout_all')
async def logout_all(
    session: AsyncSession = Depends(get_session),
    current_user = Depends(current_user)
):
    """
    Выход из системы на всех устройствах
    """
    # поулчаем id текущего пользователя
    user_id = current_user.id
    # находим все токены пользователя
    try:
        statement = select(TokenModel).where(TokenModel.user_id == user_id)
        refresh_token = await session.execute(statement)
        result = refresh_token.scalars().all() # возвращает список
        # помечаем токены как недействительные
        for token in result:
            token.invalidated = True

        headers = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        content = {"message": "Logged out from all devices successfully"}
        return JSONResponse(content=content, headers=headers)
    
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка базы данных при изменении username: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post('/change_password')
async def change_password(
    password_data: ChangePasswordRequest,
    current_user = Depends(current_user),
    session: AsyncSession = Depends(get_session)
):
    # сверяем пароли
    if not get_password(password_data.current_password, current_user.password):
        raise HTTPException(status_code=400, detail='Incorrect current password')
    # меняем новый пароль для пользователя
    current_user.password = make_password(password_data.new_password)
    await session.commit()

    return {'message', 'Password changed successfully'}


# Для тестов
@router.post('/admin')
async def admin(_ = Depends(require_role("admin"))):
    return {'message': 'success'}


# TODO Восстановление пароля (/forgot-password и /reset-password)
