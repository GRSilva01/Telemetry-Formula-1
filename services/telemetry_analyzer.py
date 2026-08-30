# ================= ANALISADOR DE TELEMETRIA =================
# Módulo de funções puras para análise de dados de telemetria:
# - Cálculo de delta entre dois pilotos
# - Interpolação de dados
# - Métricas de performance

import numpy as np
from scipy.interpolate import interp1d
from typing import Tuple, Optional


def calculate_delta(
    my_time: float,
    pro_time_sec: np.ndarray,
    pro_dist: np.ndarray,
    current_dist: float,
) -> Optional[float]:
    """Calcula o delta de tempo entre o piloto e a referência (VER).
    
    Usa interpolação para encontrar o tempo da referência na mesma distância.
    
    Args:
        my_time: Tempo do piloto na mesma distância (em segundos)
        pro_time_sec: Tempo da referência por ponto de distância
        pro_dist: Distância dos pontos da referência
        current_dist: Distância atual do piloto
    
    Returns:
        Delta em segundos (negativo = mais rápido que referência), ou None se houver erro
    """
    try:
        # Interpolação do tempo da referência na distância atual
        # bounds_error=False evita erro se distância estiver fora do range
        # fill_value="extrapolate" extrapola se necessário
        pro_time_at_dist = interp1d(
            pro_dist, pro_time_sec,
            bounds_error=False, fill_value="extrapolate"
        )(current_dist)

        delta = my_time - pro_time_at_dist
        return float(delta) if np.isfinite(delta) else None
    except Exception as e:
        print(f"[Telemetry Analyzer] Erro ao calcular delta: {e}")
        return None


def calculate_instant_delta(
    my_dist: np.ndarray,
    my_time_sec: np.ndarray,
    pro_dist: np.ndarray,
    pro_time_sec: np.ndarray,
    index: int = -1,
) -> Optional[float]:
    """Calcula delta instantâneo no índice especificado.
    
    Args:
        my_dist: Distâncias do piloto
        my_time_sec: Tempos do piloto (segundos)
        pro_dist: Distâncias da referência
        pro_time_sec: Tempos da referência (segundos)
        index: Índice no array (padrão: último ponto)
    
    Returns:
        Delta em segundos no índice especificado
    """
    try:
        if index < 0:
            index = len(my_dist) - 1

        if index >= len(my_dist) or index < 0:
            return None

        current_dist = float(my_dist[index])
        my_time = float(my_time_sec[index])

        # Busca interpolação da referência na distância do piloto
        if current_dist >= pro_dist[0] and current_dist <= pro_dist[-1]:
            pro_time_at_dist = interp1d(
                pro_dist, pro_time_sec,
                bounds_error=False, fill_value="extrapolate"
            )(current_dist)
        else:
            # Extrapolação se estiver fora dos limites
            pro_time_at_dist = interp1d(
                pro_dist, pro_time_sec,
                bounds_error=False, fill_value="extrapolate"
            )(current_dist)

        delta = my_time - pro_time_at_dist
        return float(delta) if np.isfinite(delta) else None
    except Exception as e:
        print(f"[Telemetry Analyzer] Erro no delta instantâneo: {e}")
        return None


def smooth_signal(
    data: np.ndarray,
    window_size: int = 5,
) -> np.ndarray:
    """Aplica suavização móvel a um sinal de telemetria.
    
    Args:
        data: Array de dados
        window_size: Tamanho da janela de média móvel (ímpar recomendado)
    
    Returns:
        Dados suavizados
    """
    if len(data) <= window_size:
        return data

    # Média móvel simples
    window = np.ones(window_size) / window_size
    return np.convolve(data, window, mode='valid')


def find_nearest_point(
    target_dist: float,
    dist_array: np.ndarray,
) -> int:
    """Encontra o índice do ponto mais próximo da distância alvo.
    
    Args:
        target_dist: Distância alvo
        dist_array: Array de distâncias ordenadas
    
    Returns:
        Índice do ponto mais próximo
    """
    return int(np.abs(dist_array - target_dist).argmin())