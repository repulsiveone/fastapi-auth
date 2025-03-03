from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlmodel import Session
from fastapi import APIRouter, HTTPException

from app.db import get_session, init_db
from app.models.auth import UserAuthModel, CreateUserModel

router = APIRouter()

@router.get("/users", response_model=list[UserAuthModel])
def get_user(session: Session=Depends(get_session)):
    result = session.execute(select(UserAuthModel))
    users = result.scalars().all()
    return [UserAuthModel(username=user.username, email=user.email, password=user.password, id=user.id) for user in users]

@router.post('/signup')
def signup(user: CreateUserModel, session: Session=Depends(get_session)):
    user = UserAuthModel(username=user.username, email=user.email, password=user.password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user