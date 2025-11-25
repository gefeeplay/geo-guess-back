from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from fastapi.security import OAuth2PasswordBearer
from ..database import get_session
from ..models import Duel
from ..utils import decode_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid token")
    return data["user_id"]

# =============== GET /duels =================

@router.get("/")
def get_duels(session: Session = Depends(get_session)):
    return session.exec(select(Duel)).all()

# =============== POST /duels ================

@router.post("/")
def create_duel(
    user_id: int = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    duel = Duel(creator_id=user_id)
    session.add(duel)
    session.commit()
    session.refresh(duel)
    return duel

# =============== PUT /duels/{id}/join ===============

@router.put("/{duel_id}/join")
def join_duel(
    duel_id: int,
    user_id: int = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    duel = session.get(Duel, duel_id)
    if not duel:
        raise HTTPException(status_code=404, detail="Duel not found")

    if duel.join_id is not None:
        raise HTTPException(status_code=400, detail="Duel already full")

    duel.join_id = user_id
    session.add(duel)
    session.commit()
    session.refresh(duel)
    return duel

# =============== DELETE /duels/{id} ===============

@router.delete("/{duel_id}")
def delete_duel(
    duel_id: int,
    session: Session = Depends(get_session)
):
    duel = session.get(Duel, duel_id)
    if not duel:
        raise HTTPException(status_code=404, detail="Duel not found")

    session.delete(duel)
    session.commit()
    return {"message": "Duel deleted"}
