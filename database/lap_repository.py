from .models import Lap, TelemetrySample, get_session


class LapRepository:
    """Repositório para operações CRUD na tabela laps e telemetry_samples."""

    @staticmethod
    def save_lap(track_name: str, lap_time_seconds: float, year_reference: int) -> Lap:
        """Salva metadados de uma volta no banco de dados."""
        session = get_session()
        try:
            lap = Lap(
                track_name=track_name,
                lap_time_seconds=lap_time_seconds,
                year_reference=year_reference,
                is_valid=True,
            )
            session.add(lap)
            session.commit()
            return lap
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def get_laps_by_year(year: int) -> list[Lap]:
        """Lista todas as voltas de um ano específico."""
        session = get_session()
        try:
            return (
                session.query(Lap)
                .filter(Lap.year_reference == year)
                .order_by(Lap.date_recorded.desc())
                .all()
            )
        finally:
            session.close()

    @staticmethod
    def get_lap_by_id(lap_id: int) -> Lap | None:
        """Busca um lap por ID."""
        session = get_session()
        try:
            return session.query(Lap).get(lap_id)
        finally:
            session.close()

    @staticmethod
    def save_telemetry_samples(lap_id: int, samples: list[dict]) -> None:
        """Salva amostras de telemetria para uma volta específica."""
        session = get_session()
        try:
            for sample_data in samples:
                sample = TelemetrySample(
                    lap_id=lap_id,
                    distance=sample_data.get("distance", 0.0),
                    time_ms=sample_data.get("time_ms", 0),
                    speed=sample_data.get("speed", 0.0),
                    throttle=sample_data.get("throttle", 0.0),
                    brake=sample_data.get("brake", 0.0),
                    steer=sample_data.get("steer", 0.0),
                )
                session.add(sample)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def get_telemetry_by_lap_id(lap_id: int) -> list[TelemetrySample]:
        """Busca todas as amostras de telemetria de uma volta."""
        session = get_session()
        try:
            return (
                session.query(TelemetrySample)
                .filter(TelemetrySample.lap_id == lap_id)
                .order_by(TelemetrySample.distance.asc())
                .all()
            )
        finally:
            session.close()