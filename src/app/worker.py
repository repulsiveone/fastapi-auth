from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import DatabaseError, OperationalError, NoResultFound, SQLAlchemyError

from app.db import engine
from app.models.auth import TokenModel
from app.logger import logger

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

                if not expired_tokens:
                    logger.info("Нет просроченных токенов для удаления.")
                    return
                # Удаляем каждый истекший токен
                for token in expired_tokens:
                    await db.delete(token) 

                # Фиксируем транзакцию
                await db.commit()
        
            except (DatabaseError, OperationalError) as e:
                # Откатываем транзакцию в случае ошибки
                await db.rollback()
                logger.error(f"Ошибка базы данных: {e}")
            except Exception as e:
                # Откатываем транзакцию в случае ошибки
                await db.rollback()
                logger.error(f"Error in cleanup_expired_refresh_tokens: {e}")
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при создании сессии: {e}")
    except Exception as e:
        logger.critical(f"Error with session: {e}")
