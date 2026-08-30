import pandas as pd
from database.connection import get_session
from database.models import Lap, TelemetrySample

class LapRepository:
    @staticmethod
    def save_lap(track_name, lap_time_sec, telemetry_df, year_ref=2024):
        session = get_session()
        try:
            lap = Lap(
                track_name=track_name,
                lap_time_seconds=lap_time_sec,
                year_reference=year_ref,
                is_valid=True
            )
            session.add(lap)
            session.flush()  # Gera lap.id

            samples = [
                TelemetrySample(
                    lap_id=lap.id,
                    distance=row['Distance'],
                    time_ms=int(row['TimeMs']),
                    speed=row['Speed'],
                    throttle=row['Throttle'],
                    brake=row['Brake'],
                    steer=row['Steer']
                )
                for _, row in telemetry_df.iterrows()
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
            return session.query(Lap).order_by(Lap.date_recorded.desc()).all()
        finally:
            session.close()

    @staticmethod
    def get_lap_telemetry_df(lap_id):
        session = get_session()
        try:
            samples = session.query(TelemetrySample).filter_by(lap_id=lap_id).order_by(TelemetrySample.distance.asc()).all()
            data = [{
                'Distance': s.distance,
                'TimeMs': s.time_ms,
                'Speed': s.speed,
                'Throttle': s.throttle,
                'Brake': s.brake,
                'Steer': s.steer
            } for s in samples]
            return pd.DataFrame(data)
        finally:
            session.close()