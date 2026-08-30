# ================= PARSER PURO DE PACOTES =================
# Funções matemáticas/puras de desempacotamento binário.
# Recebem bytes e retornam Data Transfer Objects (DTOs) tipados.
# Nenhuma lógica de negócio ou interação com UI/Banco de Dados.

from typing import Dict, Any, List, Optional, Tuple
import struct
from typing import Optional, Tuple
from ingestion.protocol_constants import (
    HEADER_SIZE,
    PACKET_SESSION,
    PACKET_LAPDATA,
    PACKET_CARSTATUS,
    TRACK_MAP,
)


# ================= DTOs (Data Transfer Objects) =================

class SessionDataDTO:
    """Dados da sessão (pista, tempo, etc)."""
    def __init__(self):
        self.track_id: int = 0
        self.track_name: str = "Desconhecido"
        self.track_length: float = 0.0
        self.session_type: int = 0
        self.game_major_version: int = 0
        self.game_minor_version: int = 0
        self.game_patch_version: int = 0
        self.session_time_remaining: int = 0
        self.session_time_total: int = 0
        self.speed_max: float = 0.0


class CarTelemetryDTO:
    """Telemetria do carro (speed, throttle, brake, steer)."""
    def __init__(self):
        self.speed: int = 0
        self.throttle: float = 0.0
        self.steer: float = 0.0
        self.brake: float = 0.0
        self.gear: int = 0
        self.engine_rpm: int = 0
        drs: int = 0
        local_time: float = 0.0


class LapDataDTO:
    """Dados da volta (distância, tempos)."""
    def __init__(self):
        self.current_lap_number: int = 0
        self.lap_time_ms: int = 0
        self.previous_lap_time_ms: int = 0
        self.best_lap_time_ms: int = 0
        self.speed_team_mate_1: float = 0.0
        self.speed_team_mate_2: float = 0.0
        self.is_personal_best: int = 0
        self.ai_controlled: int = 0


# ================= FUNÇÕES DE PARSING =================

def parse_session_data(raw_data: bytes) -> Optional[SessionDataDTO]:
    """Parseia o pacote 1 (SessionData). Retorna None se dados inválidos."""
    if len(raw_data) < HEADER_SIZE:
        return None

    header = struct.unpack_from("<HBBBB B Q f I I B B", raw_data, 0)
    # header indices: header[0]=format, [1]=sessionId, [2]=sessionMajorVersion, etc.
    # Ajustado para o formato real do F1 2020+

    packet_id = header[1]  # offset 1 após o formato
    # Note: O formato exacto pode variar ligeiramente entre versões do jogo

    dto = SessionDataDTO()
    # trackId está no byte offset 7 do payload (após o header struct)
    # Vamos extrair os campos principais
    dto.track_id = header[7] if len(header) > 7 else 0
    dto.track_name = TRACK_MAP.get(dto.track_id, "Desconhecido")
    dto.track_length = header[4] if len(header) > 4 else 0  # trackLength como H (2 bytes)

    return dto


def parse_car_telemetry(raw_data: bytes, player_index: int = 0) -> Optional[CarTelemetryDTO]:
    """Parseia o pacote 6 (Car Telemetry)."""
    if len(raw_data) < HEADER_SIZE:
        return None

    header = struct.unpack_from("<HBBBB B Q f I I B B", raw_data, 0)
    packet_id = header[1]

    if packet_id != PACKET_CARSTATUS:
        return None

    # Cada item de telemetria do carro tem 60 bytes
    # O jogador (player_index) começa em offset: HEADER_SIZE + (player_index * 60)
    offset = HEADER_SIZE + (player_index * CAR_TELEMETRY_ITEM_SIZE)

    # O carro telemetry tem 15 bytes por jogador dentro do bloco de 60:
    # <Hfffb = 2 bytes (speed) + 4 bytes (throttle, brake, steer, ???) + 1 byte (gear)
    # Mas o layout real do jogo é: speed(H), throttle(f), steer(f), brake(f), gear(b) = 2+4+4+4+1 = 15
    # Os outros 45 bytes são padding ou dados de outros jogadores

    car_offset = offset + 0  # Começa no início do bloco do jogador

    # Speed: unsigned short (2 bytes) na posição 0 do bloco do carro
    speed = struct.unpack_from("<H", raw_data, car_offset)[0]

    # throttle, steer, brake: float (4 bytes cada) nas posições 2, 4, 6
    throttle = struct.unpack_from("<f", raw_data, car_offset + 2)[0]
    steer = struct.unpack_from("<f", raw_data, car_offset + 6)[0]
    brake = struct.unpack_from("<f", raw_data, car_offset + 10)[0]

    # gear: signed byte (1 byte) na posição 14
    gear = struct.unpack_from("<b", raw_data, car_offset + 14)[0]

    dto = CarTelemetryDTO()
    dto.speed = speed
    dto.throttle = throttle
    dto.steer = steer
    dto.brake = brake
    dto.gear = gear

    return dto


def parse_lap_data(raw_data: bytes, player_index: int = 0) -> Optional[LapDataDTO]:
    """Parseia o pacote 2 (Lap Data)."""
    if len(raw_data) < HEADER_SIZE:
        return None

    header = struct.unpack_from("<HBBBB B Q f I I B B", raw_data, 0)
    packet_id = header[1]

    if packet_id != PACKET_LAPDATA:
        return None

    # Cada item de dados da volta tem 62 bytes
    offset = HEADER_SIZE + (player_index * LAP_DATA_ITEM_SIZE)

    # Layout do pacote 2 (62 bytes por jogador):
    # offset 0: m_currentLapNumber (uint32)
    # offset 4: m_lapTimeMs (uint32)
    # offset 8: m_previousLapTimeMs (uint32)
    # offset 12: m_bestLapTimeMs (uint32)
    # offset 16: m_speedTeamMate1 (float)
    # offset 20: m_speedTeamMate2 (float)
    # offset 24: m_isPersonalBest (uint8)
    # offset 25: m_aiControlled (uint8)
    # offset 26: ??? (padding)
    # ... total 62 bytes

    current_lap = struct.unpack_from("<I", raw_data, offset)[0]
    lap_time_ms = struct.unpack_from("<I", raw_data, offset + 4)[0]
    previous_lap_ms = struct.unpack_from("<I", raw_data, offset + 8)[0]
    best_lap_ms = struct.unpack_from("<I", raw_data, offset + 12)[0]
    speed_mate1 = struct.unpack_from("<f", raw_data, offset + 16)[0]
    speed_mate2 = struct.unpack_from("<f", raw_data, offset + 20)[0]
    is_personal_best = struct.unpack_from("<b", raw_data, offset + 24)[0]
    ai_controlled = struct.unpack_from("<b", raw_data, offset + 25)[0]

    dto = LapDataDTO()
    dto.current_lap_number = current_lap
    dto.lap_time_ms = lap_time_ms
    dto.previous_lap_time_ms = previous_lap_ms
    dto.best_lap_time_ms = best_lap_ms
    dto.speed_team_mate_1 = speed_mate1
    dto.speed_team_mate_2 = speed_mate2
    dto.is_personal_best = is_personal_best
    dto.ai_controlled = ai_controlled

    return dto