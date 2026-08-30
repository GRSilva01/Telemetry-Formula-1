# ================= DELTA HUD WIDGET =================
# Widget isolado que exibe o delta de tempo entre o piloto e a referência.
# Herda de tk.Frame para composição fácil em qualquer interface.
# Recebe dados via método update_data() - princípios SOLID.

import tkinter as tk
from tkinter import ttk


class DeltaHUD(tk.Frame):
    """Widget que mostra o delta em tempo real entre o piloto e a referência."""

    def __init__(self, parent, ref_driver: str = "VER", **kwargs):
        super().__init__(parent, **kwargs)
        self.ref_driver = ref_driver
        self._delta_var = tk.StringVar(value=f"+0.000s {ref_driver}")
        self._delta_fg = "#FF3366"  # Vermelho por padrão (pior tempo)
        self._delta_bg = "#0d2818"

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura a interface do widget."""
        # Frame principal do HUD
        hud_frame = tk.Frame(self, bg="#1E1E1E", pady=10)
        hud_frame.pack(fill=tk.X)

        # Título
        tk.Label(hud_frame, text=f"LIVE DELTA vs {self.ref_driver}", 
                 fg="#888888", bg="#1E1E1E", font=("Arial", 9)).pack(anchor="w")

        # Display do delta
        self.lbl_delta = tk.Label(hud_frame, textvariable=self._delta_var,
                                  fg=self._delta_fg, bg=self._delta_bg,
                                  font=("Consolas", 24, "bold"), pady=8)
        self.lbl_delta.pack(fill=tk.X, pady=2)

        # Indicação de melhoria/piora
        self.lbl_trend = tk.Label(hud_frame, text="", fg="#00FF66",
                                  bg=self._delta_bg, font=("Arial", 9))
        self.lbl_trend.pack(anchor="w")

    def update_data(self, delta: float, is_improving: bool = False) -> None:
        """Atualiza o display do delta.
        
        Args:
            delta: Valor do delta em segundos (negativo = mais rápido)
            is_improving: True se o piloto está melhorando o tempo
        """
        if is_improving:
            self._delta_fg = "#00FF66"  # Verde - melhorando
            self._delta_bg = "#0d2818"
            trend_text = "Melhorando!"
        else:
            self._delta_fg = "#FF3366"  # Vermelho - piorando
            self._delta_bg = "#330d18"
            trend_text = "Piorando!"

        # Formatação: +1.234s ou -0.567s
        if delta < 0:
            formatted = f"{delta:+.3f}s"
        else:
            formatted = f"+{delta:+.3f}s"

        self._delta_var.set(formatted)
        self.lbl_delta.config(fg=self._delta_fg, bg=self._delta_bg)
        if hasattr(self, 'lbl_trend'):
            self.lbl_trend.config(text=trend_text, fg=self._delta_fg)

    def set_background(self, bg_color: str) -> None:
        """Define a cor de fundo do widget."""
        self.config(bg=bg_color)
        self.lbl_delta.config(bg=bg_color)
        if hasattr(self, 'lbl_trend'):
            self.lbl_trend.config(bg=bg_color)


# Instância global para fácil acesso
delta_hud_instance = None