import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from config import DB_NAME

DB_PATH = os.path.abspath(DB_NAME)
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Cria todas as tabelas no banco de dados SQLite caso ainda não existam."""
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()