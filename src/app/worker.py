import os
from rq_scheduler import Scheduler
from dotenv import load_dotenv
from datetime import datetime, timezone
from celery import Celery, shared_task
from celery.schedules import crontab
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from app.db import get_session, engine
from app.models.auth import TokenModel
from rq import scheduler
import sys
import asyncio

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

load_dotenv()

async def cleanup_expired_refresh_tokens():
    logger.info("Задача cleanup_expired_refresh_tokens запущена.")
    """Удаляет из базы данных просроченные и недействительные токены."""
    try:
        async with AsyncSession(engine) as db:
            try:
                # Выполняем запрос для поиска истекших токенов
                result = await db.execute(
                    select(TokenModel).where(
                        TokenModel.invalidated == True
                    )
                )
                expired_tokens = result.scalars().all() 

                # Удаляем каждый истекший токен
                for token in expired_tokens:
                    await db.delete(token) 

                # Фиксируем транзакцию
                await db.commit()
            except Exception as e:
                # Откатываем транзакцию в случае ошибки
                await db.rollback()
                print(f"Error in cleanup_expired_refresh_tokens: {e}")
    except Exception as e:
        print(f"Error with session: {e}")
