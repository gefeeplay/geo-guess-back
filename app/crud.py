from sqlmodel import Session, select
from .models import User, UserCreate, Duel

def get_user_by_email(session: Session, email: str):
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def create_user(session: Session, user_create: UserCreate, hashed_password: str):
    user = User(email=user_create.email, hashed_password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Дуэли
def create_duel(session: Session, creator_id: int) -> Duel:
    duel = Duel(creator_id=creator_id)
    session.add(duel)
    session.commit()
    session.refresh(duel)
    return duel

def list_duels(session: Session):
    statement = select(Duel)
    return session.exec(statement).all()

def get_duel(session: Session, duel_id: int):
    return session.get(Duel, duel_id)

def join_duel(session: Session, duel: Duel, user_id: int):
    duel.join_id = user_id
    session.add(duel)
    session.commit()
    session.refresh(duel)
    return duel

def delete_duel(session: Session, duel: Duel):
    session.delete(duel)
    session.commit()
