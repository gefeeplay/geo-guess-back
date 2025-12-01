from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from app.logger import logger
from app.database import get_session
from app.models import (User, Statistics, StatisticsRead, GameResult, DuelResult, 
GameStatisticsResponse, DuelStatisticsResponse)

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

# ------- POST /statistics/game -------
@router.post("/game", response_model=GameStatisticsResponse)
async def update_game_result(
    game_result: GameResult,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Обновить статистику после игры"""
    
    # Находим статистику пользователя
    statement = select(Statistics).where(Statistics.user_id == current_user.id)
    stats = session.exec(statement).first()
    
    if not stats:
        raise HTTPException(
            status_code=404, 
            detail=f"Статистика для пользователя {current_user.email} не найдена"
        )
    
    # Увеличиваем счетчик игр
    stats.games += 1
    
    # Если выиграл, увеличиваем счетчик побед
    if game_result.won:
        stats.games_won += 1
    
    session.add(stats)
    session.commit()
    session.refresh(stats)
    
    logger.info(f"Обновлена статистика для пользователя {current_user.email}")
    return {
        "message": "Статистика игры обновлена",
        "user_email": current_user.email,
        "games": stats.games,   
        "games_won": stats.games_won   
    }

# ------- POST /statistics/duel -------
@router.post("/duel", response_model=DuelStatisticsResponse)
async def update_duel_result(
    duel_result: DuelResult,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Обновить статистику после дуэли"""
    
    # Находим статистику пользователя
    statement = select(Statistics).where(Statistics.user_id == current_user.id)
    stats = session.exec(statement).first()
    
    if not stats:
        raise HTTPException(
            status_code=404, 
            detail=f"Статистика для пользователя {current_user.email} не найдена"
        )
    
    # Увеличиваем счетчик дуэлей
    stats.duels += 1
    
    # Если выиграл, увеличиваем счетчик побед
    if duel_result.won:
        stats.duels_won += 1
    
    session.add(stats)
    session.commit()
    session.refresh(stats)
    
    return {
        "message": "Статистика дуэли обновлена",
        "user_email": current_user.email,
        "duels": stats.duels,
        "duels_won": stats.duels_won
    }
