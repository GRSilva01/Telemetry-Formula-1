from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Lap(Base):
    __tablename__ = "laps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_name = Column(String(100), nullable=False)
    lap_time_seconds = Column(Float, nullable=False)
    year_reference = Column(Integer, nullable=False, default=2024)
    date_recorded = Column(DateTime, default=datetime.utcnow)

    samples = relationship("TelemetrySample", back_populates="lap", cascade="all, delete-orphan")


class TelemetrySample(Base):
    __tablename__ = "telemetry_samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lap_id = Column(Integer, ForeignKey("laps.id"), nullable=False, index=True)

    distance = Column(Float, nullable=False)
    time_ms = Column(Integer, nullable=False)
    speed = Column(Float, nullable=False)
    throttle = Column(Float, nullable=False)
    brake = Column(Float, nullable=False)
    steer = Column(Float, nullable=False)

    # Coordenadas espaciais e Dinâmica Veicular
    world_pos_x = Column(Float, default=0.0)
    world_pos_z = Column(Float, default=0.0)
    g_force_lat = Column(Float, default=0.0)
    g_force_lon = Column(Float, default=0.0)

    lap = relationship("Lap", back_populates="samples")