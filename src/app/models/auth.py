import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, Field
from fastapi import Depends
from pydantic import field_validator, BaseModel, StringConstraints, constr
from typing_extensions import Annotated

from app.services.hashers import make_password
# TODO сделать permissions model
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PASSWORD_REGEX = r"^(?=.*[a-z,A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"


class TokenModel(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    token: str = Field(default=None, index=True)
    user_id: int = Field(index=True)
    invalidated: bool = Field(default=False)


class UserModel(SQLModel):
    username: str = Field(default=None, max_length=100)
    email: str = Field(default=None, max_length=100, unique=True)
    password: str = Field(min_length=8, max_length=100)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    # TODO добавить функцию update_user
    def set_password(self, password: str):
        self.password = make_password(password)
    # функция для создания пользователя
    # TODO добавить проверку есть ли почта в базе данных
    @classmethod
    async def create_user(cls, username:str, email:str, password:str, session: AsyncSession):
        user_data = {
            "username": username,
            "email": email,
            "password": password
        }
        # создание объекта с валидацией
        user = cls.model_validate(user_data)
        # хэширование пароля
        user.set_password(password)
        #добавление пользователя в базу данных
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    # функция для создания супер-пользователя: создается пользователь -> устанавливается флаг True для is_superuser
    @classmethod
    async def create_superuser(cls, username:str, email:str, password:str, session: AsyncSession):
        user = await cls.create_user(username=username, email=email, password=password, session=session)
        user.is_superuser = True
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @field_validator("email")
    def validate_email(cls, email):
        if not re.match(EMAIL_REGEX, email):
            raise ValueError("Must be a valid email address")
        return email
    
    @field_validator("password")
    def validate_password(cls, password):
        if not re.match(PASSWORD_REGEX, password):
            raise ValueError("Password are incorrect")
        return password

class UserAuthModel(UserModel, table=True):
    id: int = Field(default=None, primary_key=True)

class CreateUserModel(UserModel):
    pass


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    def validate_password(cls, new_password):
        if not re.match(PASSWORD_REGEX, new_password):
            raise ValueError("Password are incorrect")
        return new_password