import os
import fastf1
import numpy as np

# Mapeamento do nome interno do jogo para o nome oficial do GP aceito pelo FastF1
FASTF1_TRACK_NAME_MAP = {
    "Melbourne": "Australian Grand Prix",
    "Bahrain": "Bahrain Grand Prix",
    "Catalunya": "Spanish Grand Prix",
    "Monaco": "Monaco Grand Prix",
    "Montreal": "Canadian Grand Prix",
    "Silverstone": "British Grand Prix",
    "Hungaroring": "Hungarian Grand Prix",
    "Spa": "Belgian Grand Prix",
    "Monza": "Italian Grand Prix",
    "Singapore": "Singapore Grand Prix",
    "Suzuka": "Japanese Grand Prix",
    "Abu Dhabi": "Abu Dhabi Grand Prix",
    "Austin": "United States Grand Prix",
    "Sao Paulo": "São Paulo Grand Prix",
    "Austria": "Austrian Grand Prix",
    "Mexico": "Mexico City Grand Prix",
    "Baku": "Azerbaijan Grand Prix",
    "Zandvoort": "Dutch Grand Prix",
    "Imola": "Emilia Romagna Grand Prix",
    "Jeddah": "Saudi Arabian Grand Prix",
    "Miami": "Miami Grand Prix",
    "Las Vegas": "Las Vegas Grand Prix",
    "Qatar": "Qatar Grand Prix"
}

class FastF1Service:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(self.cache_dir)

    def extract_reference_data(self, year, track_name, session_type="Q", driver="VER"):
        """
        Carrega a volta mais rápida da referência oficial da F1 com fallback automático de ano.
        """
        gp_name = FASTF1_TRACK_NAME_MAP.get(track_name, track_name)
        years_to_try = [int(year), 2024, 2023] if int(year) not in [2024, 2023] else [int(year), 2024, 2023]

        for y in years_to_try:
            try:
                print(f"[FastF1] Tentando carregar {driver} em {gp_name} ({y} - {session_type})...")
                session = fastf1.get_session(y, gp_name, session_type)
                session.load(telemetry=True, weather=False, messages=False)

                laps = session.laps.pick_drivers(driver)
                if laps.empty:
                    continue

                lap = laps.pick_fastest()
                if lap is None or lap.empty or str(lap["LapTime"]) == "NaT":
                    continue

                tel = lap.get_car_data().add_distance()
                if tel.empty or "Distance" not in tel:
                    continue

                p_dist, unique_idx = np.unique(tel["Distance"].to_numpy(), return_index=True)
                p_speed = tel["Speed"].to_numpy()[unique_idx]
                p_throttle = tel["Throttle"].to_numpy()[unique_idx]
                p_time = tel["Time"].dt.total_seconds().to_numpy()[unique_idx]
                lap_time_str = str(lap["LapTime"]).split()[-1][:8]

                return {
                    "success": True,
                    "year_used": y,
                    "distance": p_dist,
                    "speed": p_speed,
                    "throttle": p_throttle,
                    "time_sec": p_time,
                    "lap_time_str": lap_time_str,
                    "error": None
                }

            except Exception as e:
                print(f"[FastF1] Falha para {gp_name} ({y}): {e}")
                continue

        return {
            "success": False,
            "error": f"Não foi possível obter dados oficiais para {gp_name}."
        }

    def load_driver_lap(self, year, track_name, session_type="Q", driver="VER"):
        return self.extract_reference_data(year, track_name, session_type, driver)

fastf1_service = FastF1Service()