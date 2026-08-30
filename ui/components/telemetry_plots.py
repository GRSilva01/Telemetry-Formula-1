# ================= TELEMETRY PLOTS COMPONENT =================
# Componente de gráficos Matplotlib isolado em tk.Frame.
# Recebe dados via métodos update_data() - desacoplado da lógica de negócio.

import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional, List, Dict, Any
import numpy as np


class TelemetryPlots(tk.Frame):
    """Canvas de gráficos Matplotlib integrado à interface Tkinter.
    
    Responsável apenas pela renderização gráfica. Não contém lógica de
    cálculo de delta ou interpolação - esses dados são fornecidos via
    métodos públicos.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._fig = None
        self._canvas = None
        self._axes = None
        self._lines = {}
        self._setup_figure()

    def _setup_figure(self) -> None:
        """Configura a figura Matplotlib."""
        self._fig = Figure(figsize=(11, 8), facecolor='#121212')
        self._fig.patch.set_facecolor('#121212')
        plt.subplots_adjust(hspace=0.08, left=0.06, right=0.98, top=0.94, bottom=0.06)

        # Cria 3 subplots: Speed, Throttle/Brake/Steer, e Delta/Opcional
        self._axes = self._fig.subplots(3, 1, sharex=True)

        # Garante que axes seja uma lista mesmo com 1 subplot
        if not isinstance(self._axes, list):
            self._axes = [self._axes]

        for ax in self._axes:
            ax.set_facecolor('#181818')

        # Configuração dos eixos
        self._configure_axes()

        # Cria o canvas
        self._canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _configure_axes(self) -> None:
        """Configura o layout dos 3 eixos."""
        # Eixo 0: Speed
        ax0 = self._axes[0]
        ax0.set_ylabel("Speed (km/h)", fontsize=10)
        ax0.set_ylim(0, 360)
        ax0.grid(True, alpha=0.15)
        ax0.legend(loc="lower right", fontsize=9)

        # Eixo 1: Throttle
        ax1 = self._axes[1]
        ax1.set_ylabel("Throttle %", fontsize=10)
        ax1.set_yticks([0, 50, 100])
        ax1.grid(True, alpha=0.15)

        # Eixo 2: Brake/Steer
        ax2 = self._axes[2]
        ax2.set_ylabel("Brake / Steer", fontsize=10)
        ax2.set_xlabel("Distância na Pista (m)", fontsize=10)
        ax2.grid(True, alpha=0.15)
        ax2.legend(loc="upper right", fontsize=9)

        # Linhas placeholder - serão atualizadas dinamicamente
        self._lines['pro_speed'] = ax0.plot([], [], color="#005AFF",
                                              linewidth=1.5, label="REF")[0]
        self._lines['my_speed'] = ax0.plot([], [], color="#00FFCC",
                                             linewidth=1.5, label="YOU")[0]
        self._lines['pro_thr'] = ax1.plot([], [], color="#005AFF", alpha=0.6,
                                            linewidth=1.2)[0]
        self._lines['my_thr'] = ax1.plot([], [], color="#00FFCC",
                                          linewidth=1.2)[0]
        self._lines['my_brk'] = ax2.plot([], [], color="#FF3366",
                                          linewidth=1.2, label="Freio (%)")[0]
        self._lines['my_str'] = ax2.plot([], [], color="#FFCC00",
                                          alpha=0.7, linewidth=1.0,
                                          label="Volante (%)")[0]

        # Adiciona legends aos eixos que têm legenda
        ax0.legend(loc="lower right", fontsize=9)

    def update_data(self, 
                    my_dist: Optional[List[float]] = None,
                    my_speed: Optional[List[float]] = None,
                    my_throttle: Optional[List[float]] = None,
                    my_brake: Optional[List[float]] = None,
                    my_steer: Optional[List[float]] = None,
                    pro_dist: Optional[List[float]] = None,
                    pro_speed: Optional[List[float]] = None,
                    pro_throttle: Optional[List[float]] = None,
                    title: Optional[str] = None) -> None:
        """Atualiza os gráficos com novos dados.
        
        Args:
            my_dist: Distâncias do piloto (live/historical)
            my_speed: Velocidades do piloto
            my_throttle: Positions do throttle do piloto
            my_brake: Positions do brake do piloto
            my_steer: Positions do steer do piloto
            pro_dist: Distâncias da referência (VER)
            pro_speed: Velocidades da referência
            pro_throttle: Positions do throttle da referência
            title: Título opcional para o gráfico
        """
        # Atualizar dados do piloto
        if my_dist is not None and my_speed is not None:
            m_dist = np.array(my_dist, dtype=float)
            m_spd = np.array(my_speed, dtype=float)
            self._lines['my_speed'].set_data(m_dist, m_spd)

        if my_throttle is not None:
            m_thr = np.array(my_throttle, dtype=float)
            self._lines['my_thr'].set_data(my_dist if my_dist else [], m_thr)

        if my_brake is not None:
            m_brk = np.array(my_brake, dtype=float)
            self._lines['my_brk'].set_data(my_dist if my_dist else [], m_brk)

        if my_steer is not None:
            m_str = np.array(my_steer, dtype=float) * 100
            self._lines['my_str'].set_data(my_dist if my_dist else [], m_str)

        # Atualizar dados da referência
        if pro_dist is not None and pro_speed is not None:
            p_dist = np.array(pro_dist, dtype=float)
            p_spd = np.array(pro_speed, dtype=float)
            self._lines['pro_speed'].set_data(p_dist, p_spd)

        # Ajustar limites dos eixos se houver dados
        if my_dist is not None and len(my_dist) > 0:
            max_dist = max(max(my_dist), 1.0) if my_dist else 1.0
            self._axes[0].set_xlim(0, max_dist * 1.1)
            self._axes[1].set_xlim(0, max_dist * 1.1)
            self._axes[2].set_xlim(0, max_dist * 1.1)

        # Atualizar título se fornecido
        if title is not None:
            self._fig.suptitle(title, fontsize=12, color='white')

        # Redesenha o canvas
        try:
            self._canvas.draw()
        except Exception as e:
            print(f"[TelemetryPlots] Erro ao desenhar canvas: {e}")

    def clear(self) -> None:
        """Limpa todos os dados dos gráficos."""
        for line in self._lines.values():
            line.set_data([], [])
        self._fig.suptitle("", fontsize=12)
        try:
            self._canvas.draw()
        except Exception:
            pass

    def set_facecolor(self, color: str) -> None:
        """Define a cor de fundo da figura."""
        self._fig.patch.set_facecolor(color)
        for ax in self._axes:
            ax.set_facecolor(color)
        try:
            self._canvas.draw()
        except Exception:
            pass