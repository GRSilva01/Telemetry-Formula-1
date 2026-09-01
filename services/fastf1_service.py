import os
import logging
import fastf1
import numpy as np
import pandas as pd

# Silencia logs verbosos que congelam o console
logging.getLogger('fastf1').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

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
    def __init__(self, cache_dir: str = "cache_fastf1"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(self.cache_dir)

    def extract_reference_data(self, year: int, track_name: str, session_type: str = "Q", driver_code: str = "VER") -> dict:
        try:
            sess = fastf1.get_session(year, track_name, session_type)
            sess.load(telemetry=True, weather=False, messages=False)

            # Filtra estritamente pelo piloto solicitado
            driver_laps = sess.laps.pick_drivers(driver_code.upper())
            if driver_laps.empty:
                driver_laps = sess.laps.pick_driver(driver_code.upper())

            fastest_lap = driver_laps.pick_fastest()
            if fastest_lap is None or fastest_lap.empty:
                return {"success": False, "error": f"Nenhuma volta válida para {driver_code}"}

            tel = fastest_lap.get_telemetry()
            if tel.empty:
                return {"success": False, "error": "Telemetria vazia"}

            dist = tel["Distance"].to_numpy()
            speed = tel["Speed"].to_numpy()
            throttle = tel["Throttle"].to_numpy()
            gear = tel["nGear"].to_numpy() if "nGear" in tel else np.zeros_like(dist)
            time_sec = tel["Time"].dt.total_seconds().to_numpy()

            lap_time_val = fastest_lap["LapTime"]
            total_sec = lap_time_val.total_seconds() if hasattr(lap_time_val, "total_seconds") else float(time_sec[-1])
            m = int(total_sec // 60)
            s = total_sec % 60
            lap_str = f"{m:02d}:{s:06.3f}"

            return {
                "success": True,
                "distance": dist,
                "speed": speed,
                "throttle": throttle,
                "gear": gear,
                "time_sec": time_sec,
                "lap_time_str": lap_str,
                "lap_time_sec": total_sec,
                "driver": driver_code.upper()
            }
        except Exception as e:
            print(f"[!] Erro FastF1: {e}")
            return {"success": False, "error": str(e)}

fastf1_service = FastF1Service()
