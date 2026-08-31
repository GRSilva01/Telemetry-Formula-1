import pandas as pd
from database.connection import get_session
from database.models import Lap, TelemetrySample

class LapRepository:
    @staticmethod
    def save_lap(track_name: str, lap_time_seconds: float, df_telemetry: pd.DataFrame, year_reference: int = 2024) -> int:
        session = get_session()
        try:
            lap = Lap(
                track_name=track_name,
                lap_time_seconds=lap_time_seconds,
                year_reference=year_reference
            )
            session.add(lap)
            session.flush()

            samples = [
                TelemetrySample(
                    lap_id=lap.id,
                    distance=row["Distance"],
                    time_ms=int(row["TimeMs"]),
                    speed=row["Speed"],
                    throttle=row["Throttle"],
                    brake=row["Brake"],
                    steer=row["Steer"],
                    world_pos_x=row.get("WorldPosX", 0.0),
                    world_pos_z=row.get("WorldPosZ", 0.0),
                    g_force_lat=row.get("GForceLat", 0.0),
                    g_force_lon=row.get("GForceLon", 0.0)
                )
                for _, row in df_telemetry.iterrows()
            ]

            session.bulk_save_objects(samples)
            session.commit()
            return lap.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def get_all_laps():
        session = get_session()
        try:
            return session.query(Lap).order_by(Lap.id.desc()).all()
        finally:
            session.close()

    @staticmethod
    def get_lap_telemetry_df(lap_id: int) -> pd.DataFrame:
        session = get_session()
        try:
            samples = session.query(TelemetrySample).filter_by(lap_id=lap_id).order_by(TelemetrySample.distance.asc()).all()
            if not samples:
                return pd.DataFrame()

            return pd.DataFrame([{
                "Distance": s.distance,
                "TimeMs": s.time_ms,
                "Speed": s.speed,
                "Throttle": s.throttle,
                "Brake": s.brake,
                "Steer": s.steer,
                "WorldPosX": s.world_pos_x,
                "WorldPosZ": s.world_pos_z,
                "GForceLat": s.g_force_lat,
                "GForceLon": s.g_force_lon
            } for s in samples])
        finally:
            session.close()