from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlmodel import Session, select
from datetime import datetime

from app.database import get_session
from app.models import User, UserCreate, UserRead
from app.utils import (
    hash_password, verify_password, create_access_token,
    decode_token, create_verification_token, send_verification_email
)
from app.logger import logger

router = APIRouter()
security = HTTPBearer()


# ---------- Helpers ----------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    token = credentials.credentials
    logger.info(f"Получен токен для проверки: {token}")

    data = decode_token(token)
    if not data:
        logger.warning("Неверный или просроченный токен")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = data.get("user_id")
    if not user_id:
        logger.warning("Некорректный payload токена")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = session.get(User, user_id)
    if not user:
        logger.warning(f"Пользователь с id {user_id} не найден")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    logger.info(f"Авторизован пользователь: {user.email}")
    return user


# ---------- Endpoints ----------
@router.post("/register")
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    logger.info(f"Попытка регистрации пользователя: {user_data.email}")

    try:
        existing = session.exec(
            select(User).where(User.email == user_data.email)
        ).first()

        if existing:
            logger.warning(f"Регистрация отклонена — email уже используется: {user_data.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        token, expires = create_verification_token()

        new_user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            is_verified=False,
            verification_token=token,
            verification_expire=expires,
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        logger.info(f"Пользователь создан: {new_user.email}, отправка письма подтверждения")

        try:
            send_verification_email(new_user.email, token)
        except Exception as email_error:
            logger.error(f"Ошибка отправки письма: {email_error}")

        return {"message": "User created, verification email sent"}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка регистрации: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login")
def login(data: UserCreate, session: Session = Depends(get_session)):
    logger.info(f"Попытка входа: {data.email}")

    user = session.exec(
        select(User).where(User.email == data.email)
    ).first()

    if not user:
        logger.warning(f"Вход отклонён — пользователь не найден: {data.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(data.password, user.hashed_password):
        logger.warning(f"Вход отклонён — неверный пароль: {data.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"user_id": user.id})

    logger.info(f"Пользователь вошёл: {user.email}")
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    logger.info(f"Запрос информации о пользователе: {current_user.email}")
    return current_user


@router.get("/verify")
def verify_email(token: str, session: Session = Depends(get_session)):
    logger.info(f"Запрос подтверждения email по токену: {token}")

    try:
        user = session.exec(
            select(User).where(User.verification_token == token)
        ).first()

        if not user:
            logger.warning("Попытка подтверждения с неверным токеном")
            raise HTTPException(status_code=400, detail="Invalid token")

        if user.verification_expire < datetime.utcnow():
            logger.warning("Токен подтверждения просрочен")
            raise HTTPException(status_code=400, detail="Token expired")

        user.is_verified = True
        user.verification_token = None
        user.verification_expire = None

        session.add(user)
        session.commit()

        logger.info(f"Email успешно подтверждён: {user.email}")
        return {"message": "Email verified successfully"}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка подтверждения email: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")