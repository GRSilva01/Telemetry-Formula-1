from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from database import db


class Lap(db.Base if hasattr(db, 'Base') else object):
    __tablename__ = 'laps'

    id = Column(Integer, primary_key=True)
    track_name = Column(String(100), nullable=False)
    lap_time_seconds = Column(Float, nullable=False)
    date_recorded = Column(DateTime, default=func.now())
    year_reference = Column(Integer, nullable=False)
    is_valid = Column(Boolean, default=True)

    __table_args__ = (
        Index('ix_laps_track_name', 'track_name'),
        Index('ix_laps_year_reference', 'year_reference'),
    )


class TelemetrySample(db.Base if hasattr(db, 'Base') else object):
    __tablename__ = 'telemetry_samples'

    id = Column(Integer, primary_key=True)
    lap_id = Column(Integer, ForeignKey('laps.id', ondelete='CASCADE'), nullable=False)
    distance = Column(Float, index=True, nullable=False)
    time_ms = Column(Integer, nullable=False)
    speed = Column(Float, nullable=False)
    throttle = Column(Float, nullable=False)
    brake = Column(Float, nullable=False)
    steer = Column(Float, nullable=False)

    __table_args__ = (
        Index('ix_telemetry_samples_lap_id', 'lap_id'),
    )