from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlmodel import Session
from fastapi import APIRouter, HTTPException

from app.db import get_session, init_db
from app.models.auth import UserAuthModel, CreateUserModel

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