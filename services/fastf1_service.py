# ================= SERVIÇO FASTF1 =================
# Camada de serviço responsável pela ingestão de dados oficiais da FIA via FastF1.
# Isola a lógica de busca/ cache de dados da UI e do motor de persistência.

import fastf1
from typing import Optional, Tuple
from datetime import datetime
import config


class FastF1Service:
    """Serviço para carregar dados de sessão F1 usando FastF1 com cache."""

    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or config.CACHE_DIR
        fastf1.Cache.enable_cache(self.cache_dir)
        self._cache = fastf1.Cache

    def load_session(self, year: int, track_name: str, session_type: str = "Q") -> object:
        """Carrega uma sessão F1 (treino, classificação, corrida).
        
        Args:
            year: Ano da temporada F1
            track_name: Nome da pista (ex: "Monaco", "Silverstone")
            session_type: Tipo de sessão ("Q" = Qualifying, "R" = Race, "P1", "P2", "P3")
        
        Returns:
            Session object do FastF1
        """
        try:
            session = fastf1.get_session(year, track_name, session_type)
            session.load(telemetry=True, weather=False, messages=False)
            return session
        except Exception as e:
            print(f"[FastF1 Service] Erro ao carregar sessão {year} {track_name}: {e}")
            return None

    def get_fastest_lap_driver(self, session) -> object:
        """Retorna a volta mais rápida do piloto principal (padrão VER)."""
        if session is None:
            return None
        try:
            lap = session.laps.pick_drivers("VER").pick_fastest()
            return lap
        except Exception as e:
            print(f"[FastF1 Service] Erro ao buscar volta mais rápida: {e}")
            return None

    def get_car_telemetry(self, lap) -> object:
        """Retorna dados de telemetria da volta."""
        if lap is None:
            return None
        try:
            tel = lap.get_car_data().add_distance()
            return tel
        except Exception as e:
            print(f"[FastF1 Service] Erro ao obter telemetria: {e}")
            return None

    def extract_reference_data(self, year: int, track_name: str, driver: str = "VER") -> Tuple:
        """Extrai dados de referência (distância, velocidade, throttle, tempo) da volta mais rápida.
        
        Returns tuple: (distances, speeds, throttles, time_secs, lap_time_str)
        """
        session = self.load_session(year, track_name)
        if session is None:
            return ([], [], [], [], "")

        lap = self.get_fastest_lap_driver(session)
        if lap is None:
            return ([], [], [], [], "")

        tel = self.get_car_telemetry(lap)
        if tel is None:
            return ([], [], [], [], "")

        # Extrair e unique-ify data (garantir pontos únicos e crescentes de distância)
        p_dist, unique_idx = __import__("numpy").unique(
            tel["Distance"].to_numpy(), return_index=True
        )

        p_speed = tel["Speed"].to_numpy()[unique_idx]
        p_throttle = tel["Throttle"].to_numpy()[unique_idx]
        p_time = tel["Time"].dt.total_seconds().to_numpy()[unique_idx]

        lap_time_str = str(lap["LapTime"]).split()[-1][:8]

        return (p_dist, p_speed, p_throttle, p_time, lap_time_str)

    def cache_exists(self, year: int, track_name: str) -> bool:
        """Verifica se há cache para a sessão especificada."""
        return self._cache.exists(f"{year}_{track_name}")


# Instância global para injeção de dependência
fastf1_service = FastF1Service()