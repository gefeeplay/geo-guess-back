from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from .database import init_db, get_session
from .models import UserCreate, UserRead, Duel
from .crud import (
    get_user_by_email, create_user,
    create_duel, list_duels, get_duel, join_duel, delete_duel
)
from .auth import (
    hash_password, verify_password, create_access_token, get_current_user
)

app = FastAPI(title="GeoGuess Duel API")

@app.on_event("startup")
def on_startup():
    init_db()

# ----- AUTH -----
@app.post("/auth/register", response_model=UserRead)
def register(user_in: UserCreate, session: Session = Depends(get_session)):
    existing = get_user_by_email(session, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(user_in.password)
    user = create_user(session, user_in, hashed)
    return UserRead.from_orm(user)

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    # OAuth2PasswordRequestForm ожидает поля: username, password (это удобно для fetch/form)
    user = get_user_by_email(session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserRead)
def me(current_user: UserRead = Depends(get_current_user)):
    return current_user

# ----- DUELS -----

# Создание дуэли
@app.post("/duels", response_model=Duel)
def create_new_duel(current_user: UserRead = Depends(get_current_user), session: Session = Depends(get_session)):
    duel = create_duel(session, creator_id=current_user.id)
    return duel

# Получение дуэлей
@app.get("/duels", response_model=list[Duel])
def get_duels(session: Session = Depends(get_session)):
    return list_duels(session)

# Присоединение к дуэли
@app.put("/duels/{duel_id}/join", response_model=Duel)
def join_existing_duel(duel_id: int, current_user: UserRead = Depends(get_current_user), session: Session = Depends(get_session)):
    duel = get_duel(session, duel_id)
    if not duel:
        raise HTTPException(status_code=404, detail="Duel not found")
    if duel.join_id is not None:
        raise HTTPException(status_code=400, detail="Duel already joined")
    if duel.creator_id == current_user.id:
        raise HTTPException(status_code=400, detail="Creator cannot join their own duel")
    duel = join_duel(session, duel, current_user.id)
    return duel

# Удаление дуэли
@app.delete("/duels/{duel_id}")
def delete_existing_duel(duel_id: int, current_user: UserRead = Depends(get_current_user), session: Session = Depends(get_session)):
    duel = get_duel(session, duel_id)
    if not duel:
        raise HTTPException(status_code=404, detail="Duel not found")
    # Правило: только создатель может удалить (можно изменить)
    if duel.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can delete duel")
    delete_duel(session, duel)
    return {"ok": True}
