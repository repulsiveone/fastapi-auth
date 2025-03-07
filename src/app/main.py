from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db import init_db, engine
from app.models.auth import UserAuthModel
from app.routers.auth import router as auth_router

# инициализация базы данных
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(engine)
    yield

app = FastAPI(lifespan=lifespan)

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