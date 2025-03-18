from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from sqlalchemy.exc import IntegrityError, OperationalError, DatabaseError

from app.worker import cleanup_expired_refresh_tokens
from app.db import init_db, engine
from app.models.auth import UserAuthModel, RoleModel
from app.routers.auth import router as auth_router
from app.db import get_session
from app.logger import logger

# вызов функции для очистки невалидных токенов каждые 24 часа
async def run_periodically():
    while True:
        await cleanup_expired_refresh_tokens()
        await asyncio.sleep(60*60*24)

async def create_default_roles(session: AsyncSession):
    """
    создает основные роли в базе данных при запуске программы
    """
    DEFAULT_ROLES = [
        {"name": "admin"},
        {"name": "moderator"},
        {"name": "user"}
    ]
    for role in DEFAULT_ROLES:
        role = RoleModel(name=role["name"])
        session.add(role)

    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        logger.warning(f"Ошибка целостности данных: {e}. Возможно, роли уже существуют.")
    except (DatabaseError, OperationalError) as e:
        await session.rollback()
        logger.error(f"Ошибка базы данных{e}")
    except Exception as e:
        await session.rollback()
        logger.critical(f"Неожиданна ошибка{e}")
        raise

# инициализация базы данных
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(engine)
    task = asyncio.create_task(run_periodically())
    await create_default_roles(session=get_session)
    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Периодическая задача остановлена")

app = FastAPI(lifespan=lifespan)

async def run_periodically():
    while True:
        await cleanup_expired_refresh_tokens()
        await asyncio.sleep(60)  # Запускать каждую минуту

# настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.get("/")
def read_root():
    return {'Hello': 'World!'}