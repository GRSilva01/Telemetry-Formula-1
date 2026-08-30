# ================= CONFIGURAÇÕES GLOBAIS =================
# Arquivo centralizado para versionamento e constantes da aplicação.

# Rede
UDP_IP = "127.0.0.1"
UDP_PORT = 20773

# FastF1
F1_DEFAULT_YEAR = 2024
F1_DEFAULT_SESSION = "Q"
F1_DEFAULT_DRIVER = "VER"

# Pistas (mapeamento de IDs para nomes)
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

# Diretórios
PROJECT_ROOT = "/mnt/d/Trabalho Faculdade/ProjetoF1"
CACHE_DIR = f"{PROJECT_ROOT}/cache"
LAPS_DIR = f"{PROJECT_ROOT}/laps"

# Database
DB_PATH = f"{PROJECT_ROOT}/database/f1_telemetry.db"

# UI
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900