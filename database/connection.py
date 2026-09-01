import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

DB_PATH = "f1_telemetry.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)

def get_session():
    """Retorna uma nova sessão SQLAlchemy."""
    return SessionLocal()

def init_db():
    """Cria tabelas e executa migrações automáticas de schema."""
    Base.metadata.create_all(engine)

    # Migração automática para garantir a coluna 'gear'
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(telemetry_points);")
        columns = [row[1] for row in cursor.fetchall()]
        if "gear" not in columns:
            cursor.execute("ALTER TABLE telemetry_points ADD COLUMN gear INTEGER DEFAULT 0;")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Erro na migração do SQLite: {e}")