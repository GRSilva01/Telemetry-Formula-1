from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database.connection import Base

class Lap(Base):
    __tablename__ = "laps"

    id = Column(Integer, primary_key=True, index=True)
    track_name = Column(String(50), nullable=False, index=True)
    lap_time_seconds = Column(Float, nullable=False)
    date_recorded = Column(DateTime, default=datetime.utcnow)
    year_reference = Column(Integer, default=2024)
    is_valid = Column(Boolean, default=True)

    samples = relationship("TelemetrySample", back_populates="lap", cascade="all, delete-orphan")

class TelemetrySample(Base):
    __tablename__ = "telemetry_samples"

    id = Column(Integer, primary_key=True, index=True)
    lap_id = Column(Integer, ForeignKey("laps.id", ondelete="CASCADE"), nullable=False, index=True)
    distance = Column(Float, nullable=False, index=True)
    time_ms = Column(Integer, nullable=False)
    speed = Column(Float, nullable=False)
    throttle = Column(Float, nullable=False)
    brake = Column(Float, nullable=False)
    steer = Column(Float, nullable=False)

    lap = relationship("Lap", back_populates="samples")