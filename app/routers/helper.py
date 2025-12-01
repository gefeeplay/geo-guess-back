from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from app.database import get_session
from app.models import User
from app.utils import decode_token

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