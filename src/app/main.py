from fastapi import FastAPI

from app.db import init_db
from app.models.auth import UserAuthModel

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {'Hello': 'World!'}