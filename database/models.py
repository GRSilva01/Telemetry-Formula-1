from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class LapModel(Base):
    __tablename__ = "laps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_name = Column(String(100), nullable=False)
    lap_time_seconds = Column(Float, nullable=False)
    date_recorded = Column(DateTime, default=datetime.utcnow, nullable=False)
    year_reference = Column(Integer, default=2024, nullable=False)

    points = relationship(
        "TelemetryPointModel",
        back_populates="lap",
        cascade="all, delete-orphan",
        order_by="TelemetryPointModel.distance.asc()"
    )


class TelemetryPointModel(Base):
    __tablename__ = "telemetry_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lap_id = Column(Integer, ForeignKey("laps.id", ondelete="CASCADE"), nullable=False, index=True)
    distance = Column(Float, nullable=False)
    time_ms = Column(Integer, nullable=False)
    speed = Column(Float, nullable=False)
    throttle = Column(Float, nullable=False)
    brake = Column(Float, nullable=False)
    steer = Column(Float, nullable=False)
    gear = Column(Integer, default=0)
    world_pos_x = Column(Float, default=0.0)
    world_pos_z = Column(Float, default=0.0)
    g_force_lat = Column(Float, default=0.0)
    g_force_lon = Column(Float, default=0.0)

    lap = relationship("LapModel", back_populates="points")


# Aliases para compatibilidade legada
Lap = LapModel
TelemetrySample = TelemetryPointModel
TelemetryPoint = TelemetryPointModel
