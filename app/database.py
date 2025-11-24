from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "postgresql://postgres:wzwzwz41521@localhost:5432/geoguess"

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    from .models import User, Duel
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session