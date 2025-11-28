from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import auth, duels

app = FastAPI()

# ---- CORS ----
origins = [
    "http://localhost:5173",
    "https://gefeeplay.github.io/geo-guess-grid/",
    "*",  # можно временно, но не оставляй в production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы: GET, POST, OPTIONS, DELETE...
    allow_headers=["*"],  # Разрешить любые заголовки
)

# Инициализация базы и создание таблиц
init_db()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(duels.router, prefix="/duels", tags=["Duels"])
