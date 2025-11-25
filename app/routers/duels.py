from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from ..database import get_session
from ..models import Duel
from ..utils import decode_token

router = APIRouter()
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Extract and validate JWT token from Authorization header
    Returns user_id from token payload
    """
    token = credentials.credentials
    data = decode_token(token)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return user_id

# =============== GET /duels =================

@router.get("/")
def get_duels(session: Session = Depends(get_session)):
    """Get all duels (public endpoint)"""
    return session.exec(select(Duel)).all()

# =============== POST /duels ================

@router.post("/")
def create_duel(
    user_id: int = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new duel (requires authentication)"""
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
    """Join an existing duel (requires authentication)"""
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
    """Delete a duel (public endpoint - consider adding auth if needed)"""
    duel = session.get(Duel, duel_id)
    if not duel:
        raise HTTPException(status_code=404, detail="Duel not found")

    session.delete(duel)
    session.commit()
    return {"message": "Duel deleted"}