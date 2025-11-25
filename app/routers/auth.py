from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.models import User, UserCreate, UserRead
from app.utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token
)
from app.database import get_session


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ========================= REGISTER =========================

@router.post("/register", response_model=UserRead)
def register(data: UserCreate, session: Session = Depends(get_session)):
    email = data.email
    password = data.password

    if not email or not password:
        raise HTTPException(400, "Email and password required")

    # Проверяем существование пользователя
    if session.exec(select(User).where(User.email == email)).first():
        raise HTTPException(400, "User already exists")

    # Хешируем пароль
    hashed = hash_password(password)

    user = User(email=email, hashed_password=hashed)
    session.add(user)
    session.commit()
    session.refresh(user)

    return {"id": user.id, "email": user.email}

# ========================= LOGIN =========================

@router.post("/login")
def login(data: dict, session: Session = Depends(get_session)):
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise HTTPException(400, "Email and password required")

    user = session.exec(select(User).where(User.email == email)).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}

# ========================= ME =========================

@router.get("/me")
def me(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    data = decode_token(token)

    if not data:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = session.get(User, data["user_id"])

    return user
