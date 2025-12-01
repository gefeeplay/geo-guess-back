from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from app.logger import logger
from app.database import get_session
from app.models import User, Statistics, StatisticsRead
from app.routers.helper import get_current_user

router = APIRouter()
security = HTTPBearer()

# ------- GET /statistics -------
@router.get("/", response_model=StatisticsRead)
def get_statistics(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    stats = session.exec(
        select(Statistics).where(Statistics.user_id == current_user.id)
    ).first()

    if not stats:
        # Если нет статистики — создаём пустую
        stats = Statistics(user_id=current_user.id)
        session.add(stats)
        session.commit()
        session.refresh(stats)

    logger.info(f"Получена статистика для пользователя {current_user.email}")
    return stats