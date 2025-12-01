# app/routers/duels.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from app.database import get_session
from app.models import Duel
from app.utils import decode_token
from app.logger import logger

router = APIRouter()
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    logger.info(f"Получен токен для дуэлей: {token}")

    data = decode_token(token)
    if not data:
        logger.warning("Неверный или просроченный токен при работе с дуэлями")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = data.get("user_id")
    if not user_id:
        logger.warning("Некорректный payload токена для дуэлей")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    logger.info(f"Авторизован пользователь (duels): {user_id}")
    return user_id


# ------- GET /duels -------
@router.get("/")
def get_duels(session: Session = Depends(get_session)):
    logger.info("Запрос списка дуэлей")
    return session.exec(select(Duel)).all()


# ------- POST /duels -------
@router.post("/")
def create_duel(user_id: int = Depends(get_current_user),
                session: Session = Depends(get_session)):
    logger.info(f"Создание новой дуэли пользователем {user_id}")

    duel = Duel(creator_id=user_id)
    session.add(duel)
    session.commit()
    session.refresh(duel)

    logger.info(f"Дуэль создана: id={duel.id}, creator={user_id}")
    return duel


# ------- PUT /duels/{id}/join -------
@router.put("/{duel_id}/join")
def join_duel(duel_id: int,
              user_id: int = Depends(get_current_user),
              session: Session = Depends(get_session)):
    logger.info(f"Пользователь {user_id} пытается присоединиться к дуэли {duel_id}")

    duel = session.get(Duel, duel_id)
    if not duel:
        logger.warning(f"Дуэль не найдена: {duel_id}")
        raise HTTPException(status_code=404, detail="Duel not found")

    if duel.join_id is not None:
        logger.warning(f"Дуэль {duel_id} уже заполнена")
        raise HTTPException(status_code=400, detail="Duel already full")

    duel.join_id = user_id
    session.add(duel)
    session.commit()
    session.refresh(duel)

    logger.info(f"Пользователь {user_id} присоединился к дуэли {duel_id}")
    return duel


# ------- DELETE /duels/{id} -------
@router.delete("/{duel_id}")
def delete_duel(duel_id: int, session: Session = Depends(get_session)):
    logger.info(f"Удаление дуэли {duel_id}")

    duel = session.get(Duel, duel_id)
    if not duel:
        logger.warning(f"Попытка удаления несуществующей дуэли {duel_id}")
        raise HTTPException(status_code=404, detail="Duel not found")

    session.delete(duel)
    session.commit()

    logger.info(f"Дуэль {duel_id} удалена")
    return {"message": "Duel deleted"}
