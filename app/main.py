from fastapi import FastAPI
from .database import init_db
from .routers import auth, duels

app = FastAPI()

# Инициализация базы и создание таблиц
init_db()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(duels.router, prefix="/duels", tags=["Duels"])
