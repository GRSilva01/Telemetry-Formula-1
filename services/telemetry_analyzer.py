import numpy as np

def calculate_delta(pro_dist, pro_time, my_dist, my_time, num_points=2500):
    """
    Calcula o delta de tempo ponto a ponto em uma malha contínua de distância.
    Usa np.interp (puro NumPy) sem depender de DLLs do SciPy.
    """
    if len(pro_dist) < 2 or len(my_dist) < 2:
        return np.array([]), np.array([])

    # Garante estrita monotonicidade e remoção de duplicatas
    p_dist_uniq, p_idx = np.unique(pro_dist, return_index=True)
    p_time_uniq = pro_time[p_idx]

    m_dist_uniq, m_idx = np.unique(my_dist, return_index=True)
    m_time_uniq = my_time[m_idx]

    max_dist = min(p_dist_uniq.max(), m_dist_uniq.max())
    if max_dist <= 0:
        return np.array([]), np.array([])

    grid = np.linspace(0, max_dist, num=num_points)

    # Interpolação 1D direta via NumPy
    pro_interp = np.interp(grid, p_dist_uniq, p_time_uniq)
    my_interp = np.interp(grid, m_dist_uniq, m_time_uniq)

    delta = my_interp - pro_interp
    return grid, delta

def calculate_instant_delta(pro_dist, pro_time, current_dist, current_my_time):
    """
    Calcula o delta escalar instantâneo para o HUD/Relógio Digital.
    """
    if len(pro_dist) < 2 or current_dist <= 0:
        return 0.0

    p_dist_uniq, p_idx = np.unique(pro_dist, return_index=True)
    p_time_uniq = pro_time[p_idx]

    # Encontra o tempo do piloto profissional naquela distância exata
    pro_time_at_dist = np.interp(current_dist, p_dist_uniq, p_time_uniq)
    return float(current_my_time - pro_time_at_dist)

def smooth_signal(signal, window_size=5):
    """
    Suaviza sinais ruidosos (volante/inputs) usando média móvel via convolução.
    """
    if len(signal) < window_size:
        return signal
    window = np.ones(window_size) / window_size
    return np.convolve(signal, window, mode='same')