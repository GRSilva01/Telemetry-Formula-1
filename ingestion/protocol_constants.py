# ================= PROTOCOLO UDP F1 2020+ =================
# Constantes e offsets baseados no protocolo oficial da FIA (Packet Data).

# Tamanho do header em bytes (formato little-endian: HBBBB B Q f I I B B)
HEADER_FORMAT = "<HBBBB B Q f I I B B"
HEADER_SIZE = 21  # Calculado via struct.calcsize

# IDs de pacotes (Packet ID)
PACKET_SESSION = 1          # Dados da sessão (pista, condições)
PACKET_MOTDATA = 5          # Dados do motor (não usado neste projeto)
PACKET_ACCEL = 2            # Aceleração (não usado)
PACKET_CARSETUP = 3         # Setup do carro (não usado)
PACKET_CARTELEMETRY = 4     # Telemetria do carro (não usado)
PACKET_MARSHALLING = 5      # Marshalling flags (não usado)
PACKET_LAPDATA = 2          # Dados da volta (distância, tempos)
PACKET_CARSTATUS = 6        # Status do carro (speed, throttle, brake, steer)
PACKET_FINALRESULT = 7      # Resultado final (não usado)
PACKET_LOSTCARS = 8         # Carros perdidos (não usado)
PACKET_CARVIBRATIONS = 9    # Vibrações do carro (não usado)
PACKET_TIME_TRIAL = 10      # Dados de tempo trial (não usado)
PACKET_SESSION_END = 11     # Fim da sessão (não usado)

# Tamanho do dado do carro no pacote 6 (Car Telemetry)
# Formato: <Hfffb = 2 + 4*4 + 1 = 19 bytes, mas o offset usa 60 bytes por jogador
CAR_TELEMETRY_ITEM_SIZE = 60

# Tamanho do dado da volta no pacote 2 (Lap Data)
LAP_DATA_ITEM_SIZE = 62

# Offsets dentro do header do pacote 1 (SessionData)
# Posição 7: trackId (1 byte signed)
SESSION_TRACK_ID_OFFSET = 7
# Posição 4: trackLength (2 bytes unsigned)
SESSION_TRACK_LENGTH_OFFSET = 4

# Mapas de circuitos
TRACK_MAP = {
    0: "Melbourne",
    3: "Bahrain",
    4: "Catalunya",
    5: "Monaco",
    6: "Montreal",
    7: "Silverstone",
    9: "Hungaroring",
    10: "Spa",
    11: "Monza",
    12: "Singapore",
    13: "Suzuka",
    14: "Abu Dhabi",
    15: "Austin",
    16: "Sao Paulo",
    17: "Austria",
    19: "Mexico",
    20: "Baku",
    26: "Zandvoort",
    27: "Imola",
    29: "Jeddah",
    30: "Miami",
    31: "Las Vegas",
    32: "Qatar"
}

# Padrões de nomeação de arquivos
LAP_FILENAME_PATTERN = "{track_name}_{lap_time_ms}_{distance}m"


# ================= TIPOS PADRÃO =================

TelemetryDTO = dict[str, float | int]
LapDTO = dict[str, int | float | str]