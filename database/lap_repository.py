import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, LapModel, TelemetryPointModel

DB_PATH = "f1_telemetry.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


class LapRepository:
    @staticmethod
    def save_lap(track_name: str, lap_time_seconds: float, df: pd.DataFrame, year_reference: int = 2024):
        session = SessionLocal()
        try:
            lap = LapModel(
                track_name=track_name,
                lap_time_seconds=float(lap_time_seconds),
                date_recorded=datetime.now(),
                year_reference=year_reference
            )
            session.add(lap)
            session.flush()

            points = []
            for _, row in df.iterrows():
                points.append(TelemetryPointModel(
                    lap_id=lap.id,
                    distance=float(row["Distance"]),
                    time_ms=int(row["TimeMs"]),
                    speed=float(row["Speed"]),
                    throttle=float(row["Throttle"]),
                    gear=int(row.get("Gear", 0)),
                    brake=float(row["Brake"]),
                    steer=float(row["Steer"]),
                    world_pos_x=float(row.get("WorldPosX", 0.0)),
                    world_pos_z=float(row.get("WorldPosZ", 0.0)),
                    g_force_lat=float(row.get("GForceLat", 0.0)),
                    g_force_lon=float(row.get("GForceLon", 0.0))
                ))

            session.bulk_save_objects(points)
            session.commit()
            return lap.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def get_all_laps():
        session = SessionLocal()
        try:
            return session.query(LapModel).order_by(LapModel.id.desc()).all()
        finally:
            session.close()

    @staticmethod
    def get_best_lap(track_name: str):
        session = SessionLocal()
        try:
            return session.query(LapModel).filter(
                LapModel.track_name == track_name
            ).order_by(LapModel.lap_time_seconds.asc()).first()
        finally:
            session.close()

    @staticmethod
    def get_lap_telemetry_df(lap_id: int) -> pd.DataFrame:
        session = SessionLocal()
        try:
            pts = session.query(TelemetryPointModel).filter(
                TelemetryPointModel.lap_id == lap_id
            ).order_by(TelemetryPointModel.distance.asc()).all()

            if not pts:
                return pd.DataFrame()

            data = {
                "Distance": [p.distance for p in pts],
                "TimeMs": [p.time_ms for p in pts],
                "Speed": [p.speed for p in pts],
                "Throttle": [p.throttle for p in pts],
                "Brake": [p.brake for p in pts],
                "Steer": [p.steer for p in pts],
                "Gear": [p.gear for p in pts],
                "WorldPosX": [p.world_pos_x for p in pts],
                "WorldPosZ": [p.world_pos_z for p in pts],
                "GForceLat": [p.g_force_lat for p in pts],
                "GForceLon": [p.g_force_lon for p in pts]
            }
            return pd.DataFrame(data)
        finally:
            session.close()