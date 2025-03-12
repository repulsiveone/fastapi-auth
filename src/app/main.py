from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from contextlib import asynccontextmanager
from app.worker import cleanup_expired_refresh_tokens
import asyncio
from app.db import init_db, engine
from app.models.auth import UserAuthModel
from app.routers.auth import router as auth_router

# вызов функции для очистки невалидных токенов каждые 24 часа
async def run_periodically():
    while True:
        await cleanup_expired_refresh_tokens()
        await asyncio.sleep(60*60*24)

# инициализация базы данных
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(engine)
    task = asyncio.create_task(run_periodically())
    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Периодическая задача остановлена.")

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