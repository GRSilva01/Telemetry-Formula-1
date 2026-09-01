import socket
import struct
import threading
from typing import Callable, List, Dict, Any

TRACKS_MAP = {
    0: "Melbourne", 1: "Paul Ricard", 2: "Shanghai", 3: "Sakhir", 4: "Catalunya",
    5: "Monaco", 6: "Montreal", 7: "Silverstone", 8: "Hockenheim", 9: "Hungaroring",
    10: "Spa", 11: "Monza", 12: "Singapore", 13: "Suzuka", 14: "Abu Dhabi",
    15: "Texas", 16: "Brazil", 17: "Austria", 18: "Sochi", 19: "Mexico",
    20: "Baku", 21: "Sakhir Short", 22: "Silverstone Short", 23: "Texas Short",
    24: "Suzuka Short", 25: "Hanoi", 26: "Zandvoort", 27: "Imola",
    28: "Portimao", 29: "Jeddah", 30: "Miami", 31: "Las Vegas", 32: "Losail"
}

class UDPEmitter:
    def __init__(self, udp_ip: str = "127.0.0.1", udp_port: int = 20777):
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        self.running = False
        self._thread = None
        self._socket = None

        # Callbacks registrados
        self._session_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._car_telemetry_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._lap_data_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._motion_callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def add_session_callback(self, cb: Callable[[Dict[str, Any]], None]):
        self._session_callbacks.append(cb)

    def add_car_telemetry_callback(self, cb: Callable[[Dict[str, Any]], None]):
        self._car_telemetry_callbacks.append(cb)

    def add_lap_data_callback(self, cb: Callable[[Dict[str, Any]], None]):
        self._lap_data_callbacks.append(cb)

    def add_motion_callback(self, cb: Callable[[Dict[str, Any]], None]):
        self._motion_callbacks.append(cb)

    def start(self):
        if not self.running:
            self.running = True
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.bind((self.udp_ip, self.udp_port))
            self._socket.settimeout(0.5)
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self.running = False
        if self._socket:
            self._socket.close()

    def _listen_loop(self):
        HEADER_SIZE = 29
        while self.running:
            try:
                data, _ = self._socket.recvfrom(2048)
                if len(data) < HEADER_SIZE:
                    continue

                packet_id = struct.unpack_from("<B", data, 6)[0]
                player_idx = struct.unpack_from("<B", data, 27)[0]

                # 0. MOTION DATA
                if packet_id == 0:
                    CAR_MOTION_SIZE = 60
                    offset = HEADER_SIZE + (player_idx * CAR_MOTION_SIZE)
                    if len(data) >= offset + CAR_MOTION_SIZE:
                        m_bytes = data[offset : offset + CAR_MOTION_SIZE]
                        x = struct.unpack_from("<f", m_bytes, 0)[0]
                        z = struct.unpack_from("<f", m_bytes, 8)[0]
                        g_lat = struct.unpack_from("<f", m_bytes, 36)[0]
                        g_lon = struct.unpack_from("<f", m_bytes, 40)[0]
                        motion_dict = {"world_pos_x": float(x), "world_pos_z": float(z), "g_force_lat": float(g_lat), "g_force_lon": float(g_lon)}
                        for cb in self._motion_callbacks:
                            cb(motion_dict)

                # --- 1. SESSION DATA (Packet ID 1) ---
                elif packet_id == 1:
                    # Offset 0 do payload: weather (uint8)
                    # Offset 1 do payload: trackTemperature (int8)
                    # Offset 2 do payload: airTemperature (int8)
                    # Offset 3 do payload: totalLaps (uint8)
                    # Offset 4 do payload: trackLength (uint16)
                    # Offset 6 do payload: sessionType (uint8)
                    # Offset 7 do payload: trackId (int8)
                    if len(data) >= HEADER_SIZE + 8:
                        track_len = struct.unpack_from("<H", data, HEADER_SIZE + 4)[0]
                        track_id = struct.unpack_from("<b", data, HEADER_SIZE + 7)[0]
                        track_name = TRACKS_MAP.get(track_id, "Desconhecido")

                        sess_dict = {
                            "track_name": track_name,
                            "track_length": float(track_len) if track_len > 0 else 5800.0
                        }
                        for cb in self._session_callbacks:
                            try:
                                cb(sess_dict)
                            except Exception:
                                pass
                            
                # --- 2. LAP DATA (Packet ID 2) ---
                elif packet_id == 2:
                    # No F1 23/24, cada LapData struct tem entre 57 e 62 bytes.
                    # Para ser robusto a ambas as versões:
                    CAR_LAP_SIZE = 62 if (len(data) - HEADER_SIZE) >= (22 * 62) else 57
                    offset = HEADER_SIZE + (player_idx * CAR_LAP_SIZE)
                    
                    if len(data) >= offset + 35:
                        lap_bytes = data[offset : offset + CAR_LAP_SIZE]
                        last_lap_ms = struct.unpack_from("<I", lap_bytes, 0)[0]
                        cur_lap_ms = struct.unpack_from("<I", lap_bytes, 4)[0]
                        lap_dist = struct.unpack_from("<f", lap_bytes, 20)[0]
                        
                        # No F1 23/24:
                        # pitStatus fica no byte offset 27 ou 28
                        # driverStatus fica no byte offset 30 ou 31
                        pit_status = struct.unpack_from("<B", lap_bytes, 27)[0]
                        if pit_status not in (0, 1, 2):
                            pit_status = struct.unpack_from("<B", lap_bytes, 28)[0]
                            
                        driver_status = struct.unpack_from("<B", lap_bytes, 30)[0]
                        if driver_status > 4:
                            driver_status = struct.unpack_from("<B", lap_bytes, 31)[0]

                        lap_dict = {
                            "last_lap_time_ms": int(last_lap_ms),
                            "current_lap_time_ms": int(cur_lap_ms),
                            "lap_distance": float(lap_dist),
                            "pit_status": int(pit_status) if pit_status in (0, 1, 2) else 0,
                            "driver_status": int(driver_status) if driver_status <= 4 else 4
                        }
                        for cb in self._lap_data_callbacks:
                            cb(lap_dict)

                # 6. CAR TELEMETRY
                elif packet_id == 6:
                    CAR_TEL_SIZE = 60
                    offset = HEADER_SIZE + (player_idx * CAR_TEL_SIZE)
                    if len(data) >= offset + CAR_TEL_SIZE:
                        tel_bytes = data[offset : offset + CAR_TEL_SIZE]
                        speed = struct.unpack_from("<H", tel_bytes, 0)[0]
                        throttle = struct.unpack_from("<f", tel_bytes, 2)[0]
                        steer = struct.unpack_from("<f", tel_bytes, 6)[0]
                        brake = struct.unpack_from("<f", tel_bytes, 10)[0]
                        gear = struct.unpack_from("<b", tel_bytes, 15)[0]
                        engine_rpm = struct.unpack_from("<H", tel_bytes, 16)[0]
                        rev_lights_pct = struct.unpack_from("<B", tel_bytes, 19)[0]
                        tyres_surf_temp = list(struct.unpack_from("<4B", tel_bytes, 28))

                        tel_dict = {
                            "speed": float(speed),
                            "throttle": float(throttle),
                            "steer": float(steer),
                            "brake": float(brake),
                            "gear": int(gear),
                            "engine_rpm": int(engine_rpm),
                            "rev_lights_percent": int(rev_lights_pct),
                            "tyres_surf_temp": tyres_surf_temp
                        }
                        for cb in self._car_telemetry_callbacks:
                            cb(tel_dict)

            except socket.timeout:
                continue
            except Exception as e:
                print(f"[!] Erro no loop UDP: {e}")