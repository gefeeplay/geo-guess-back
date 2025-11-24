from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import EmailStr

# Модель пользователя в БД
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(index=True, unique=True)
    hashed_password: str

# Схемы для входящих/исходящих данных (Pydantic)
class UserCreate(SQLModel):
    email: EmailStr
    password: str

class UserRead(SQLModel):
    id: int
    email: EmailStr

# Дуэль
class Duel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    creator_id: int
    join_id: Optional[int] = None
    winner_id: Optional[int] = None
