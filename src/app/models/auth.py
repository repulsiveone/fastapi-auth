import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, Field
from fastapi import Depends, HTTPException
from pydantic import field_validator, BaseModel, StringConstraints, constr
from typing_extensions import Annotated
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.services.hashers import make_password
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PASSWORD_REGEX = r"^(?=.*[a-z,A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"

class RoleModel(SQLModel, table=True):
    """
    Набор разрешений, который определяет какие действия может выполнить пользователь.
    По умолчанию:
    admin - Может иметь разрешения на создание, редактирование и удаление ресурсов.
    moderator - Включает разрешения на создание, редактирование и публикацию контента, но не на удаление пользователей или изменение настроек системы. 
    user - Имеет разрешение на просмотр ресурсов.
    """
    id: int = Field(default=None, primary_key=True)
    role: str = Field(default="user")

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

    def set_password(self, password: str):
        self.password = make_password(password)
    # функция для создания пользователя
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
    
    @classmethod
    async def email_exists(cls, email:str, session: AsyncSession) -> bool:
        """
        Проверка существует ли пользователь с указанным email в базе данных
        """
        statement = select(cls).where(cls.email==email)
        email_check = await session.execute(statement)
        result = email_check.scalar_one_or_none()
        return result is not None
    
    @staticmethod
    async def change_username_by_id(user_id: int, new_username: str, session: AsyncSession):
        """
        Изменяет username пользователя по id
        """
        user = update(UserAuthModel).where(UserAuthModel.id==user_id).values(username=new_username)
        await session.execute(user)
        await session.commit()

    @staticmethod
    async def change_email_by_id(user_id: int, new_email: str, session: AsyncSession):
        """
        Изменяет email пользователя по id
        """
        try:
            if await UserAuthModel.email_exists(email=new_email, session=session):
                return False
            else:
                user = update(UserAuthModel).where(UserAuthModel.id==user_id).values(email=new_email)
                await session.execute(user)
                await session.commit()
                return True
            
        except IntegrityError:  # Перехват ошибки нарушения уникальности (если email уже существует)
            await session.rollback()
            return False 
        except Exception as e:
            await session.rollback()
            raise # Перебросить исключение для роутера


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