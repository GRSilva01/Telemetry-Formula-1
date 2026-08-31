import numpy as np
from typing import List, Dict, Any

def calculate_instant_delta(pro_dist: np.ndarray, pro_time: np.ndarray, cur_dist: float, cur_time: float) -> float:
    """Calcula a diferença escalar instantânea (segundos) contra a referência pro."""
    if len(pro_dist) < 2 or cur_dist <= pro_dist[0]:
        return 0.0
    if cur_dist >= pro_dist[-1]:
        pro_t = pro_time[-1]
    else:
        pro_t = float(np.interp(cur_dist, pro_dist, pro_time))
    return float(cur_time - pro_t)

def calculate_cumulative_deltas(my_dist: np.ndarray, my_time: np.ndarray, pro_dist: np.ndarray, pro_time: np.ndarray) -> np.ndarray:
    """Retorna o vetor completo de delta cumulativo ao longo da volta."""
    if len(my_dist) < 2 or len(pro_dist) < 2:
        return np.zeros_like(my_dist)
    pro_interpolated = np.interp(my_dist, pro_dist, pro_time)
    return my_time - pro_interpolated

def generate_mini_sectors(track_length: float, num_sectors: int = 20) -> List[Dict[str, float]]:
    """Gera faixas equidistantes de mini-setores ao longo do traçado."""
    step = track_length / num_sectors
    sectors = []
    for i in range(num_sectors):
        sectors.append({
            "sector_idx": i + 1,
            "start_dist": i * step,
            "end_dist": (i + 1) * step,
            "delta": 0.0,
            "status": "EQUAL"
        })
    return sectors

def calculate_mini_sectors_status(mini_sectors: List[Dict[str, float]], my_dist: np.ndarray, my_deltas: np.ndarray) -> List[Dict[str, Any]]:
    """Atualiza o delta de cada micro-setor comparando a variação local de tempo."""
    if len(my_dist) < 5 or len(my_deltas) < 5:
        return mini_sectors

    results = []
    for s in mini_sectors:
        mask = (my_dist >= s["start_dist"]) & (my_dist <= s["end_dist"])
        if np.any(mask):
            sub_deltas = my_deltas[mask]
            # Variação de delta dentro do setor (ganho ou perda local)
            local_diff = sub_deltas[-1] - sub_deltas[0]
            status = "GREEN" if local_diff < -0.015 else ("RED" if local_diff > 0.015 else "YELLOW")
            results.append({
                "sector_idx": s["sector_idx"],
                "start_dist": s["start_dist"],
                "end_dist": s["end_dist"],
                "delta": local_diff,
                "status": status
            })
        else:
            results.append(s)
    return results

def calculate_trail_braking_score(brake_array: np.ndarray, steer_array: np.ndarray) -> float:
    """
    Calcula um score (0 a 100%) da suavidade na transição entre frenagem e esterçamento.
    Mede a sobreposição controlada de freio decrescente com aumento de volante.
    """
    if len(brake_array) < 10:
        return 0.0

    # Condição de entrada de curva: Freio ativo (> 5%) com volante virando (> 10%)
    mask = (brake_array > 5.0) & (np.abs(steer_array) > 10.0)
    if not np.any(mask):
        return 0.0

    overlap_points = np.sum(mask)
    total_braking_points = np.sum(brake_array > 5.0)

    score = (overlap_points / max(total_braking_points, 1)) * 100.0
    return min(float(score * 1.5), 100.0)