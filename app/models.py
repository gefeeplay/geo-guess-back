from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel, EmailStr

# Модель пользователя в БД
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(index=True, unique=True)
    hashed_password: str


# ----- Pydantic схемы -----

# То, что приходит на /register
class UserCreate(BaseModel):
    email: EmailStr
    password: str


# То, что возвращается наружу (например /me)
class UserRead(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True   # чтобы можно было возвращать SQLModel-объекты


# Дуэль (таблица)
class Duel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    creator_id: int = Field(foreign_key="user.id")
    join_id: Optional[int] = Field(default=None, foreign_key="user.id")
    winner_id: Optional[int] = Field(default=None, foreign_key="user.id")
