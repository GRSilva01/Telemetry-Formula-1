from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Index, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import config

Base = declarative_base()


class Lap(Base):
    __tablename__ = "laps"

    id = Column(Integer, primary_key=True)
    track_name = Column(String(100), nullable=False)
    lap_time_seconds = Column(Float, nullable=False)
    date_recorded = Column(DateTime, default=datetime.utcnow)
    year_reference = Column(Integer, nullable=False)
    is_valid = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_laps_track_name", "track_name"),
        Index("ix_laps_year_reference", "year_reference"),
    )


class TelemetrySample(Base):
    __tablename__ = "telemetry_samples"

    id = Column(Integer, primary_key=True)
    lap_id = Column(Integer, ForeignKey("laps.id", ondelete="CASCADE"), nullable=False)
    distance = Column(Float, index=True, nullable=False)
    time_ms = Column(Integer, nullable=False)
    speed = Column(Float, nullable=False)
    throttle = Column(Float, nullable=False)
    brake = Column(Float, nullable=False)
    steer = Column(Float, nullable=False)

    __table_args__ = (
        Index("ix_telemetry_samples_lap_id", "lap_id"),
    )


engine = create_engine(
    f"sqlite:///{config.DB_PATH}",
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)


def init_db():
    """Cria as tabelas se não existirem."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Retorna uma nova sessão de banco de dados."""
    return SessionLocal()