# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlmodel import Session, select
from datetime import datetime, timedelta

from app.database import get_session
from app.models import User, UserCreate, UserRead
from app.utils import hash_password, verify_password, create_access_token, decode_token, create_verification_token, send_verification_email


router = APIRouter()

# Используем HTTPBearer для JWT токенов
security = HTTPBearer()

# --------- helpers ----------
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), session: Session = Depends(get_session)) -> User:
    """
    Dependency: returns SQLModel User instance for a valid token.
    Raises 401 if token invalid or user not found.
    """
    token = credentials.credentials
    
    data = decode_token(token)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# --------- endpoints ---------
@router.post("/register")
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    try:
        existing = session.exec(
            select(User).where(User.email == user_data.email)
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # создаем токен подтверждения
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

        # отправляем письмо (в фоне или с обработкой ошибок)
        try:
            send_verification_email(new_user.email, token)
        except Exception as email_error:
            # Логируем ошибку, но не прерываем регистрацию
            print(f"Email sending failed: {email_error}")
            # Можно также сохранить эту ошибку в базу данных

        return {"message": "User created, verification email sent"}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()  # Важно откатить изменения при ошибке
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login")
def login(data: UserCreate, session: Session = Depends(get_session)):
    """Login endpoint - returns JWT token"""
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    """Get current user info - requires JWT token"""
    return current_user

@router.get("/verify")
def verify_email(token: str, session: Session = Depends(get_session)):
    try:
        user = session.exec(select(User).where(User.verification_token == token)).first()

        if not user:
            raise HTTPException(status_code=400, detail="Invalid token")

        if user.verification_expire < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Token expired")

        user.is_verified = True
        user.verification_token = None
        user.verification_expire = None
        session.add(user)
        session.commit()

        return {"message": "Email verified successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
