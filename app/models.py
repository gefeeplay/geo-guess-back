from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel, EmailStr

# Модели базы данных
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(index=True, unique=True)
    hashed_password: str
    is_verified: bool = Field(default=False)
    verification_token: Optional[str] = None
    verification_expire: Optional[datetime] = None
    statistics: Optional["Statistics"] = Relationship(back_populates="user")

class Statistics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # ForeignKey на user.id — правильный способ связи
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)

    games: int = Field(default=0)
    games_won: int = Field(default=0)

    duels: int = Field(default=0)
    duels_won: int = Field(default=0)

    # связь (опционально, пригодится)
    user: Optional["User"] = Relationship(back_populates="statistics")

# Дуэль (таблица)
class Duel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    creator_id: int = Field(foreign_key="user.id")
    join_id: Optional[int] = Field(default=None, foreign_key="user.id")
    winner_id: Optional[int] = Field(default=None, foreign_key="user.id")


# ----- Pydantic схемы -----

# То, что приходит на /register
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(UserCreate):
    pass    


# То, что возвращается наружу (например /me)
class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool

    class Config:
        from_attributes = True   # чтобы можно было возвращать SQLModel-объекты

class StatisticsRead(BaseModel):
    games: int
    games_won: int
    duels: int
    duels_won: int

    class Config:
        orm_mode = True

# Запрос
class GameResult(BaseModel):
    won: bool  # True - выиграл, False - проиграл

class DuelResult(BaseModel):
    won: bool  # True - выиграл, False - проиграл

# Ответ
class GameStatisticsResponse(BaseModel):
    message: str
    user_email: EmailStr
    games: int
    games_won: int

class DuelStatisticsResponse(BaseModel):
    message: str
    user_email: EmailStr
    duels: int
    duels_won: int

