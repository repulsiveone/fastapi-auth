from fastapi import FastAPI

from .db import init_db
from .models.auth import UserAuthModel
from .routers.auth import router as auth_router

app = FastAPI()

app.include_router(auth_router)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {'Hello': 'World!'}