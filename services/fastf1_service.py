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
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(self.cache_dir)

    def extract_reference_data(self, year, track_name, preferred_session="Q", driver="VER"):
        gp_name = FASTF1_TRACK_NAME_MAP.get(track_name, track_name)
        
        session_hierarchy = ["Q", "R", "FP3", "FP2", "FP1"]
        if preferred_session in session_hierarchy:
            session_hierarchy.remove(preferred_session)
            session_hierarchy.insert(0, preferred_session)

        years_to_try = [int(year), 2024, 2023, 2022] if int(year) not in [2024, 2023, 2022] else [int(year), 2024, 2023, 2022]
        years_to_try = list(dict.fromkeys(years_to_try))

        for y in years_to_try:
            for s_type in session_hierarchy:
                try:
                    session = fastf1.get_session(y, gp_name, s_type)
                    session.load(telemetry=True, weather=False, messages=False)

                    if session.laps.empty:
                        continue

                    laps = session.laps
                    driver_laps = laps[(laps["Driver"] == driver) | (laps["DriverNumber"] == "1") | (laps["DriverNumber"] == 1)]

                    if driver_laps.empty:
                        continue

                    valid_laps = driver_laps.copy()
                    valid_laps["LapTimeSec"] = valid_laps["LapTime"].dt.total_seconds()
                    valid_laps = valid_laps[valid_laps["LapTimeSec"] > 30.0]

                    if valid_laps.empty:
                        continue

                    best_lap = valid_laps.sort_values(by="LapTimeSec").iloc[0]
                    lap_time_str = str(best_lap["LapTime"]).split()[-1][:8]

                    tel = best_lap.get_telemetry()
                    if tel is None or tel.empty:
                        continue

                    if "Distance" not in tel.columns or tel["Distance"].max() == 0:
                        tel = tel.add_distance()

                    if "Distance" not in tel.columns or "Speed" not in tel.columns:
                        continue

                    p_dist = tel["Distance"].to_numpy()
                    p_speed = tel["Speed"].to_numpy()
                    p_throttle = tel["Throttle"].to_numpy() if "Throttle" in tel.columns else np.zeros_like(p_dist)
                    p_time = tel["Time"].dt.total_seconds().to_numpy()

                    p_dist, unique_idx = np.unique(p_dist, return_index=True)
                    p_speed = p_speed[unique_idx]
                    p_throttle = p_throttle[unique_idx]
                    p_time = p_time[unique_idx]

                    if "X" in tel.columns and "Y" in tel.columns:
                        p_x = tel["X"].to_numpy()[unique_idx]
                        p_y = tel["Y"].to_numpy()[unique_idx]
                    else:
                        p_x, p_y = np.array([]), np.array([])

                    return {
                        "success": True,
                        "year_used": y,
                        "session_used": s_type,
                        "driver_used": driver,
                        "distance": p_dist,
                        "speed": p_speed,
                        "throttle": p_throttle,
                        "time_sec": p_time,
                        "pos_x": p_x,
                        "pos_y": p_y,
                        "lap_time_str": lap_time_str,
                        "error": None
                    }

                except Exception:
                    continue

        return {
            "success": False,
            "error": f"Nenhuma telemetria encontrada para {driver} em {gp_name}."
        }

fastf1_service = FastF1Service()