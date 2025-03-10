import os
from datetime import datetime, timezone
from celery import Celery, shared_task
from celery.schedules import crontab
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends

from app.db import get_session, engine
from app.models.auth import TokenModel


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("BROKER_URL")
celery.conf.result_backend = os.environ.get("BROKER_URL")

@celery.task(name="cleanup_expired_refresh_tokens")
async def cleanup_expired_refresh_tokens():
    """Удаляет из базы данных просроченные и недействительные токены."""
    async with AsyncSession(engine) as db:
        
        result = await db.execute(
            select(TokenModel).where(
                (TokenModel.expires_at < datetime.now(timezone.utc))
                | (TokenModel.invalidated == True)
            )
        )
        expired_tokens = result.scalars().all() 

        for token in expired_tokens:
            await db.delete(token) 

        await db.commit()

celery.conf.beat_shedule = {
    'cleanup_tokens': {
        'task': 'cleanup_expired_refresh_tokens',
        'schedule': crontab(minute=0, hour='*/24'),
    }
}