import re
from sqlmodel import SQLModel, Field, validator, Session
from fastapi import Depends

from services.hashers import make_password
from app.db import get_session

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PASSWORD_REGEX = r"^(?=.*[a-z,A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"

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
    def create_user(cls, username:str, email:str, password:str, session: Session=Depends(get_session)):
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
        session.commit()
        session.refresh(user)
        return user
    # функция для создания супер-пользователя: создается пользователь -> устанавливается флаг True для is_superuser
    @classmethod
    def create_superuser(cls, username:str, email:str, password:str, session: Session=Depends(get_session)):
        user = cls.create_user(username=username, email=email, password=password, session=session)
        user.is_superuser = True
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @validator("email")
    def validate_email(cls, email):
        if not re.match(EMAIL_REGEX, email):
            raise ValueError("Must be a valid email address")
        return email
    
    @validator("password")
    def validate_password(cls, password):
        if not re.match(PASSWORD_REGEX, password):
            raise ValueError("Password are incorrect")
        return password

class UserAuthModel(UserModel, table=True):
    id: int = Field(default=None, primary_key=True)

class CreateUserModel(UserModel):
    pass
