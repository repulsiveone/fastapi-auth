from fastapi import Depends, FastAPI, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlmodel import Session
from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm


from app.db import get_session, init_db
from app.models.auth import UserAuthModel, CreateUserModel
from app.services.oauth import login, refresh_access_token, get_refresh_token

router = APIRouter()

@router.get("/users", response_model=list[UserAuthModel])
async def get_user(session: AsyncSession=Depends(get_session)):
    result = await session.exec(select(UserAuthModel))
    users = result.scalars().all()
    return [UserAuthModel(username=user.username, email=user.email, password=user.password, id=user.id) for user in users]

@router.post('/signup')
async def signup(user: CreateUserModel, session: AsyncSession=Depends(get_session)):
    user = await UserAuthModel.create_user(username=user.username, email=user.email, password=user.password, session=session)
    return user

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
    return {'access_token': new_access_token}

# TODO Выход (/logout)
# TODO Получение информации о текущем пользователе (/me)
# TODO Смена пароля (/change-password)
# TODO Восстановление пароля (/forgot-password и /reset-password)
