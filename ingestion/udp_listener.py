import socket
import struct
import threading
from typing import Dict, Any, List, Callable
from ingestion.protocol_constants import HEADER_FORMAT, HEADER_SIZE, TRACK_MAP

class UDPEmitter:
    def __init__(self, ip="127.0.0.1", port=20773, udp_ip=None, udp_port=None, **kwargs):
        self.ip = udp_ip or ip
        self.port = udp_port or port
        
        self._session_callbacks: List[Callable] = []
        self._telemetry_callbacks: List[Callable] = []
        self._lap_data_callbacks: List[Callable] = []
        self._motion_callbacks: List[Callable] = []
        self._tyres_callbacks: List[Callable] = []
        
        self.running = False
        self._thread = None
        self._sock = None

    def add_session_callback(self, callback: Callable):
        if callback not in self._session_callbacks:
            self._session_callbacks.append(callback)

    def add_car_telemetry_callback(self, callback: Callable):
        if callback not in self._telemetry_callbacks:
            self._telemetry_callbacks.append(callback)

    def add_lap_data_callback(self, callback: Callable):
        if callback not in self._lap_data_callbacks:
            self._lap_data_callbacks.append(callback)

    def add_motion_callback(self, callback: Callable):
        if callback not in self._motion_callbacks:
            self._motion_callbacks.append(callback)

    def add_tyres_callback(self, callback: Callable):
        if callback not in self._tyres_callbacks:
            self._tyres_callbacks.append(callback)

    def start(self):
        if self.running:
            return
        self.running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((self.ip, self.port))
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass

    def _listen_loop(self):
        while self.running:
            try:
                data, _ = self._sock.recvfrom(2048)
                if len(data) < HEADER_SIZE:
                    continue

                header = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])
                packet_id = header[5]
                player_idx = header[10]

                # --- 0. MOTION DATA (Packet ID 0) ---
                if packet_id == 0:
                    CAR_MOTION_SIZE = 60
                    offset = HEADER_SIZE + (player_idx * CAR_MOTION_SIZE)
                    if len(data) >= offset + 36:
                        motion_vals = struct.unpack_from("<fffffffff", data, offset)
                        motion_dict = {
                            "world_pos_x": float(motion_vals[0]),
                            "world_pos_y": float(motion_vals[1]),
                            "world_pos_z": float(motion_vals[2]),
                            "g_force_lat": float(motion_vals[6]),
                            "g_force_lon": float(motion_vals[7]),
                            "g_force_vert": float(motion_vals[8])
                        }
                        for cb in self._motion_callbacks:
                            try:
                                cb(motion_dict)
                            except Exception as e:
                                print(f"[!] Erro no callback de motion: {e}")

                # --- 1. SESSION DATA (Packet ID 1) ---
                elif packet_id == 1 and len(data) >= HEADER_SIZE + 8:
                    track_id = struct.unpack_from("<b", data, HEADER_SIZE + 7)[0]
                    track_length = struct.unpack_from("<H", data, HEADER_SIZE + 4)[0]
                    track_name = TRACK_MAP.get(track_id, "Desconhecido")
                    session_dict = {
                        "track_id": track_id,
                        "track_name": track_name,
                        "track_length": float(track_length)
                    }
                    for cb in self._session_callbacks:
                        try:
                            cb(session_dict)
                        except Exception as e:
                            print(f"[!] Erro no callback de sessão: {e}")

                # --- 2. LAP DATA (Packet ID 2) ---
                elif packet_id == 2:
                    CAR_LAP_SIZE = 62
                    offset = HEADER_SIZE + (player_idx * CAR_LAP_SIZE)
                    if len(data) >= offset + CAR_LAP_SIZE:
                        lap_bytes = data[offset : offset + CAR_LAP_SIZE]
                        last_lap_ms = struct.unpack_from("<I", lap_bytes, 0)[0]
                        cur_lap_ms = struct.unpack_from("<I", lap_bytes, 4)[0]
                        lap_dist = struct.unpack_from("<f", lap_bytes, 20)[0]
                        cur_lap_num = struct.unpack_from("<B", lap_bytes, 32)[0]
                        # driver_status no offset 45: 0=in garage, 1=flying lap, 2=in lap, 3=out lap, 4=on track
                        driver_status = struct.unpack_from("<B", lap_bytes, 45)[0]

                        lap_dict = {
                            "last_lap_time_ms": int(last_lap_ms),
                            "current_lap_time_ms": int(cur_lap_ms),
                            "lap_distance": float(lap_dist),
                            "current_lap_num": int(cur_lap_num),
                            "driver_status": int(driver_status)
                        }
                        for cb in self._lap_data_callbacks:
                            try:
                                cb(lap_dict)
                            except Exception as e:
                                pass

                            
                # --- 6. CAR TELEMETRY (Packet ID 6) ---
                elif packet_id == 6:
                    CAR_TELEMETRY_SIZE = 60
                    offset = HEADER_SIZE + (player_idx * CAR_TELEMETRY_SIZE)
                    if len(data) >= offset + CAR_TELEMETRY_SIZE:
                        # Offsets exatos da struct F1:
                        # speed(0:2), throttle(2:6), steer(6:10), brake(10:14), clutch(14), gear(15)
                        speed, throttle, steer, brake, gear = struct.unpack_from("<Hfffb", data, offset)
                        
                        # brakesTemp(22:30), tyresSurfTemp(30:34)
                        brakes_temp = struct.unpack_from("<HHHH", data, offset + 22)
                        tyres_surf = struct.unpack_from("<BBBB", data, offset + 30)

                        telemetry_dict = {
                            "speed": float(speed),
                            "throttle": float(throttle * 100.0),
                            "steer": float(steer),
                            "brake": float(brake * 100.0),
                            "gear": int(gear),
                            "brakes_temp": list(brakes_temp), # [RL, RR, FL, FR]
                            "tyres_surf_temp": list(tyres_surf) # [RL, RR, FL, FR]
                        }

                        for cb in self._telemetry_callbacks:
                            try:
                                cb(telemetry_dict)
                            except Exception as e:
                                pass

            except Exception as e:
                if self.running:
                    print(f"[!] Erro no loop UDP: {e}")

UDPListener = UDPEmitter