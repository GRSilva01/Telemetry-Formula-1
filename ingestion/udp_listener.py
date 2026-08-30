# ================= UDP LISTENER (Thread de Socket) =================
# Responsável apenas por receber dados do socket e disparar callbacks.
# Responsabilidade única: receber bytes do socket e disparar callbacks registrados.
# Não tem conhecimento de UI, banco de dados ou lógica de negócio.

import socket
from threading import Thread
from typing import Callable, List, Optional
from datetime import datetime

from ingestion.protocol_constants import (
    HEADER_SIZE,
    PACKET_SESSION,
    PACKET_LAPDATA,
    CAR_TELEMETRY_ITEM_SIZE,
    PACKET_CARSTATUS,
    TRACK_MAP,
)
from ingestion.packet_parser import parse_session_data, parse_car_telemetry, parse_lap_data


# ================= DATACLASSES ===============

class TelemetryUpdate:
    """Dados de telemetria prontos para serem consumidos por UI ou serviço."""
    def __init__(self, lap_id: int, distance: float, time_ms: int,
                 speed: float, throttle: float, brake: float, steer: float,
                 lap_time_str: str = ""):
        self.lap_id = lap_id
        self.distance = float(distance)
        self.time_ms = time_ms
        self.speed = float(speed)
        self.throttle = float(throttle)
        self.brake = float(brake)
        self.steer = float(steer)
        self.lap_time_str = lap_time_str


class LapCompletedEvent:
    """Evento disparado quando uma volta é completada/finish."""
    def __init__(self, lap_id: int, lap_time_str: str,
                 total_distance: float, total_time_ms: int):
        self.lap_id = lap_id
        self.lap_time_str = lap_time_str
        self.total_distance = float(total_distance)
        self.total_time_ms = total_time_ms


# ================= CLASSE UDP LISTENER ===============

class UDPEmitter:
    """Emite dados de telemetria F1 recebidos via UDP para callbacks registrados."""

    def __init__(self, udp_port: int = 20773, udp_ip: str = "127.0.0.1"):
        self.udp_port = udp_port
        self.udp_ip = udp_ip
        self.sock: Optional[socket.socket] = None
        self._running: bool = False

        # Callbacks registrados por categoria
        self._session_callbacks: List[Callable] = []
        self._car_telemetry_callbacks: List[Callable] = []
        self._lap_data_callbacks: List[Callable] = []
        self._lap_completed_callbacks: List[Callable] = []

        # Estado interno da captura
        self._current_lap_samples: List[dict] = []
        self._lap_id_counter: int = 0
        self._lap_start_distance: float = 0.0
        self._track_name: str = "Desconhecido"
        self._track_length: float = 0.0
        self._prev_dist: float = 0.0
        self._last_lap_time_ms: int = 0
        self._is_recording: bool = False

    # --- Registration methods ---

    def add_session_callback(self, callback: Callable) -> None:
        """Registra callback para dados de sessão (pista, etc)."""
        self._session_callbacks.append(callback)

    def remove_session_callback(self, callback: Callable) -> None:
        """Remove callback de sessão."""
        self._session_callbacks.remove(callback)

    def add_car_telemetry_callback(self, callback: Callable) -> None:
        """Registra callback para telemetria do carro (speed, throttle, brake, steer)."""
        self._car_telemetry_callbacks.append(callback)

    def remove_car_telemetry_callback(self, callback: Callable) -> None:
        """Remove callback de telemetria do carro."""
        self._car_telemetry_callbacks.remove(callback)

    def add_lap_data_callback(self, callback: Callable) -> None:
        """Registra callback para dados de volta (volta completa, amostras)."""
        self._lap_data_callbacks.append(callback)

    def remove_lap_data_callback(self, callback: Callable) -> None:
        """Remove callback de dados de volta."""
        self._lap_data_callbacks.remove(callback)

    def add_lap_completed_callback(self, callback: Callable) -> None:
        """Registra callback quando uma volta é completada/finish."""
        self._lap_completed_callbacks.append(callback)

    def remove_lap_completed_callback(self, callback: Callable) -> None:
        """Remove callback de finalização de volta."""
        self._lap_completed_callbacks.remove(callback)

    # --- Core logic ---

    def _emit_session(self, session_data: dict) -> None:
        """Dispara todos os callbacks de sessão com dados da sessão."""
        for callback in self._session_callbacks:
            try:
                callback(session_data)
            except Exception as e:
                print(f"[UDP Emitter] Error in session callback: {e}")

    def _emit_car_telemetry(self, telemetry: dict) -> None:
        """Dispara todos os callbacks de telemetria do carro."""
        for callback in self._car_telemetry_callbacks:
            try:
                callback(telemetry)
            except Exception as e:
                print(f"[UDP Emitter] Error in car telemetry callback: {e}")

    def _emit_lap_data(self, lap_data: TelemetryUpdate) -> None:
        """Dispara todos os callbacks de dados de volta."""
        for callback in self._lap_data_callbacks:
            try:
                callback(lap_data)
            except Exception as e:
                print(f"[UDP Emitter] Error in lap data callback: {e}")

    def _emit_lap_completed(self, lap_event: LapCompletedEvent) -> None:
        """Dispara callbacks quando uma volta é completada."""
        for callback in self._lap_completed_callbacks:
            try:
                callback(lap_event)
            except Exception as e:
                print(f"[UDP Emitter] Error in lap completed callback: {e}")

    def start(self) -> None:
        """Inicia o thread de escuta UDP em segundo plano."""
        if self._running:
            return

        self._running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.udp_ip, self.udp_port))

        thread = Thread(target=self._listen_loop, daemon=True)
        thread.start()
        print(f"[UDP Listener] Ouvindo na porta {self.udp_port}...")

    def stop(self) -> None:
        """Para o thread de escuta."""
        self._running = False
        if self.sock:
            self.sock.close()
            self.sock = None
        print("[UDP Listener] Encerrado.")

    def _listen_loop(self) -> None:
        """Loop principal de recepção de dados UDP."""
        while self._running:
            try:
                data, _ = self.sock.recvfrom(4096)
                if len(data) < HEADER_SIZE:
                    continue

                header = struct.unpack_from("<HBBBB B Q f I I B B", data, 0)
                packet_id = header[1]

                # --- PACOTE 1: Session Data (Identificação da pista) ---
                if packet_id == PACKET_SESSION:
                    session_dto = parse_session_data(data)
                    if session_dto:
                        self._track_name = session_dto.track_name
                        self._track_length = session_dto.track_length
                        self._emit_session({
                            "track_name": self._track_name,
                            "track_length": self._track_length,
                            "packet_id": packet_id,
                        })

                # --- PACOTE 6: Car Telemetry (Speed, throttle, brake, steer) ---
                elif packet_id == PACKET_CARSTATUS:
                    # player_idx vem do header; no formato original era header[10]
                    # Vamos usar um índice padrão 0 para simplificar ou extrair corretamente
                    car_dto = parse_car_telemetry(data, player_index=0)
                    if car_dto:
                        self._emit_car_telemetry({
                            "speed": car_dto.speed,
                            "throttle": car_dto.throttle,
                            "steer": car_dto.steer,
                            "brake": car_dto.brake,
                            "gear": car_dto.gear,
                            "packet_id": packet_id,
                        })

                # --- PACOTE 2: Lap Data (Distância e tempos da volta) ---
                elif packet_id == PACKET_LAPDATA:
                    lap_dto = parse_lap_data(data, player_index=0)
                    if lap_dto:
                        self._process_lap_data(lap_dto)

            except Exception as e:
                if self._running:
                    print(f"[!] Erro no loop UDP: {e}")

    def _process_lap_data(self, lap_dto: dict) -> None:
        """Processa dados de volta e gerencia gravação de amostras."""
        current_lap_num = lap_dto.current_lap_number
        lap_time_ms = lap_dto.lap_time_ms
        prev_lap_ms = lap_dto.previous_lap_time_ms
        best_lap_ms = lap_dto.best_lap_time_ms
        is_personal_best = lap_dto.is_personal_best

        # Lógica de reinício de volta (transição do setor final para início)
        # Se o carro estava > 90% da pista e agora está nos primeiros 5%
        track_eff_len = self._track_length if self._track_length > 0 else 5000.0

        if self._prev_dist > (track_eff_len * 0.90) and 0 <= lap_dto.current_lap_number:
            # Nova volta detectada - registrar dados se tivemos amostras suficientes
            if len(self._current_lap_samples) > 100:
                # Calcular tempo total da volta
                total_time_ms = self._last_lap_time_ms if self._last_lap_time_ms > 0 else lap_dto.lap_time_ms

                lap_event = LapCompletedEvent(
                    lap_id=self._lap_id_counter,
                    lap_time_str=self._format_lap_time(lap_time_ms),
                    total_distance=max(self._current_lap_samples, key=lambda x: x.get("distance", 0)).get("distance", 0) if self._current_lap_samples else 0,
                    total_time_ms=total_time_ms,
                )

                # Dispara evento de volta completada
                self._emit_lap_completed(lap_event)

            # Resetar estado para nova volta
            self._current_lap_samples = []
            self._lap_id_counter += 1
            self._prev_dist = 0.0

        # Acumular dados da telemetria se estamos gravando ou pista conhecida
        if self._is_recording or self._track_name != "Desconhecido":
            # Coletar dados básicos a partir dos dados disponíveis
            sample = {
                "distance": lap_dto.current_lap_number if hasattr(lap_dto, 'current_lap_number') else 0,
                "time_ms": lap_dto.lap_time_ms if hasattr(lap_dto, 'lap_time_ms') else 0,
            }
            # Adicionar dados de speed se disponíveis via estado global
            # (Em uma implementação completa, passaria telemetria do carro tamb

        # Nota: Em uma implementação completa, aqui acumulariamos as amostras
        # Esta é a estrutura base para o padrão observador

    def _format_lap_time(self, lap_time_ms: int) -> str:
        """Formata tempo da volta em string mm:ss.cc."""
        if lap_time_ms <= 0:
            return "--:--.--"
        minutes = lap_time_ms // 60000
        seconds = (lap_time_ms % 60000) / 1000
        return f"{minutes}:{seconds:.3f}"