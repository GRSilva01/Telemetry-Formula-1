import threading
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from database.lap_repository import LapRepository
from services.telemetry_analyzer import calculate_instant_delta

class LiveTelemetryService:
    def __init__(self, on_lap_completed_callback=None):
        self.lock = threading.Lock()
        self.on_lap_completed_callback = on_lap_completed_callback

        self.current_track = "Aguardando telemetria..."
        self.track_length = 5800.0
        self.prev_dist = 0.0

        # Estado da Localização / Boxes
        self.is_in_pits = False
        self.pit_status_str = "ON TRACK"

        # PB Cache
        self.pb_dist = np.array([])
        self.pb_time_sec = np.array([])
        self.pb_speed = np.array([])
        self.pb_throttle = np.array([])

        # Powertrain Live
        self.prev_gear = 0
        self.shift_events: List[str] = []
        self.last_shift_status = "--"

        # Instantâneos
        self.latest_car = {
            "speed": 0.0, "throttle": 0.0, "brake": 0.0, "steer": 0.0, "gear": 0,
            "engine_rpm": 0, "rev_lights_percent": 0, "tyres_surf_temp": [0, 0, 0, 0]
        }
        self.latest_motion = {"x": 0.0, "z": 0.0, "g_lat": 0.0, "g_lon": 0.0}

        # Buffers Live
        self.live_dist: List[float] = []
        self.live_speed: List[float] = []
        self.live_throttle: List[float] = []
        self.live_brake: List[float] = []
        self.live_steer: List[float] = []
        self.live_gear: List[int] = []
        self.live_time_sec: List[float] = []
        self.live_deltas: List[float] = []
        self.live_pos_x: List[float] = []
        self.live_pos_z: List[float] = []
        self.live_g_lat: List[float] = []
        self.live_g_lon: List[float] = []

        self.needs_ui_reset = False

    def load_pb_data(self, pb_dist, pb_time_sec, pb_speed, pb_throttle):
        with self.lock:
            self.pb_dist = pb_dist
            self.pb_time_sec = pb_time_sec
            self.pb_speed = pb_speed
            self.pb_throttle = pb_throttle

    def handle_session(self, data: Dict[str, Any]):
        track_name = data.get("track_name")
        track_len = data.get("track_length", 5800.0)
        if track_name and track_name != "Desconhecido" and track_name != self.current_track:
            with self.lock:
                self.current_track = track_name
                self.track_length = track_len

    def handle_car_telemetry(self, data: Dict[str, Any]):
        with self.lock:
            cur_gear = data.get("gear", 0)
            rev_pct = data.get("rev_lights_percent", 0)

            if cur_gear > self.prev_gear and 1 <= self.prev_gear <= 7 and cur_gear <= 8:
                if 94 <= rev_pct <= 99:
                    self.last_shift_status = "OPTIMAL"
                elif rev_pct < 90:
                    self.last_shift_status = "EARLY"
                else:
                    self.last_shift_status = "LATE"
                self.shift_events.append(self.last_shift_status)

            self.prev_gear = cur_gear
            self.latest_car.update({
                "speed": data.get("speed", 0.0),
                "throttle": data.get("throttle", 0.0),
                "brake": data.get("brake", 0.0),
                "steer": data.get("steer", 0.0),
                "gear": cur_gear,
                "engine_rpm": data.get("engine_rpm", 0),
                "rev_lights_percent": rev_pct,
                "tyres_surf_temp": data.get("tyres_surf_temp", [0, 0, 0, 0])
            })

    def handle_motion(self, data: Dict[str, Any]):
        with self.lock:
            self.latest_motion.update({
                "x": data.get("world_pos_x", 0.0),
                "z": data.get("world_pos_z", 0.0),
                "g_lat": data.get("g_force_lat", 0.0),
                "g_lon": data.get("g_force_lon", 0.0)
            })

    def handle_lap(self, data: Dict[str, Any]):
        dist = data.get("lap_distance", 0.0)
        cur_time_ms = data.get("current_lap_time_ms", 0)
        last_time_ms = data.get("last_lap_time_ms", 0)
        pit_status = data.get("pit_status", 0)
        driver_status = data.get("driver_status", 4)

        with self.lock:
            # Identifica se está nos boxes ou na garagem
            # pit_status: 1 (entrando), 2 (no pit)
            # driver_status: 0 (na garagem)
            in_pits_by_flag = (pit_status in (1, 2)) or (driver_status == 0)
            
            if in_pits_by_flag:
                self.is_in_pits = True
                if driver_status == 0:
                    self.pit_status_str = "IN GARAGE"
                elif pit_status == 1:
                    self.pit_status_str = "PITTING (IN)"
                else:
                    self.pit_status_str = "PIT LANE"
            else:
                self.is_in_pits = False
                self.pit_status_str = "ON TRACK"

            eff_len = self.track_length if self.track_length > 0 else 5800.0

            # 1. Reset por retorno ao Box / Garagem ou Linha de Chegada
            if (self.prev_dist > 300.0 and dist < (self.prev_dist - 200.0)) or self.is_in_pits:
                # Salva apenas voltas reais completadas na pista
                if not self.is_in_pits and self.prev_dist > (eff_len * 0.80) and len(self.live_dist) > 100:
                    lap_s = (last_time_ms / 1000.0) if last_time_ms > 0 else (self.live_time_sec[-1] if self.live_time_sec else 0.0)
                    if lap_s > 20.0:
                        df_to_save = pd.DataFrame({
                            "Distance": list(self.live_dist),
                            "TimeMs": [int(t * 1000) for t in self.live_time_sec],
                            "Speed": list(self.live_speed),
                            "Throttle": list(self.live_throttle),
                            "Brake": list(self.live_brake),
                            "Steer": list(self.live_steer),
                            "Gear": list(self.live_gear),
                            "WorldPosX": list(self.live_pos_x),
                            "WorldPosZ": list(self.live_pos_z),
                            "GForceLat": list(self.live_g_lat),
                            "GForceLon": list(self.live_g_lon)
                        })
                        threading.Thread(
                            target=self._save_lap_async,
                            args=(self.current_track, lap_s, df_to_save),
                            daemon=True
                        ).start()

                # Limpa os buffers ao vivo para não poluir
                self.live_dist.clear()
                self.live_speed.clear()
                self.live_throttle.clear()
                self.live_brake.clear()
                self.live_steer.clear()
                self.live_gear.clear()
                self.live_time_sec.clear()
                self.live_deltas.clear()
                self.live_pos_x.clear()
                self.live_pos_z.clear()
                self.live_g_lat.clear()
                self.live_g_lon.clear()
                self.shift_events.clear()
                self.needs_ui_reset = True
                self.prev_dist = max(dist, 0.0)
                return

            # 2. Ingestão quando estiver acelerando na pista
            if dist >= 0.0 and not self.is_in_pits:
                cur_t_sec = cur_time_ms / 1000.0
                if len(self.live_dist) == 0 or dist > self.live_dist[-1]:
                    self.live_dist.append(dist)
                    self.live_speed.append(self.latest_car["speed"])
                    self.live_throttle.append(self.latest_car["throttle"])
                    self.live_brake.append(self.latest_car["brake"])
                    self.live_steer.append(self.latest_car["steer"] * 100.0)
                    self.live_gear.append(int(self.latest_car["gear"]))
                    self.live_time_sec.append(cur_t_sec)
                    self.live_pos_x.append(self.latest_motion["x"])
                    self.live_pos_z.append(self.latest_motion["z"])
                    self.live_g_lat.append(self.latest_motion["g_lat"])
                    self.live_g_lon.append(self.latest_motion["g_lon"])

                    if len(self.pb_dist) > 0 and dist > 15 and cur_t_sec > 0:
                        inst_delta = calculate_instant_delta(self.pb_dist, self.pb_time_sec, dist, cur_t_sec)
                        self.live_deltas.append(inst_delta)
                    else:
                        self.live_deltas.append(0.0)

                self.prev_dist = dist

    def _save_lap_async(self, track_name, lap_time_sec, df):
        try:
            LapRepository.save_lap(track_name, lap_time_sec, df)
            if self.on_lap_completed_callback:
                self.on_lap_completed_callback(track_name)
        except Exception as e:
            print(f"[!] Erro ao salvar volta: {e}")