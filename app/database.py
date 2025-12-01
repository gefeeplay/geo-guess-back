import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL_TEST") if os.getenv("TESTING") == "1" else os.getenv("DATABASE_URL")

print("DATABASE_URL =", repr(DATABASE_URL))

engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    from .models import User, Duel
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session