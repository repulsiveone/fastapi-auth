from .auth import current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status, Depends
from app.models.auth import UserAuthModel
from app.db import get_session

def require_role(role: str):
    async def role_checker(current_user = Depends(current_user)):
        if current_user.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User have not any role"
			)
        if current_user.role.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required role",
            )
        return current_user
    return role_checker
