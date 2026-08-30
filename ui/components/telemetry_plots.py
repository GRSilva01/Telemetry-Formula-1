import tkinter as tk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TelemetryPlots(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#121212")
        self._setup_figure()

    def _setup_figure(self):
        plt.style.use("dark_background")
        self.fig, self.ax = plt.subplots(
            3, 1, figsize=(11, 8), sharex=True, gridspec_kw={'height_ratios': [2.8, 1.2, 1.2]}
        )
        self.fig.patch.set_facecolor('#121212')
        self.fig.subplots_adjust(hspace=0.08, left=0.06, right=0.98, top=0.94, bottom=0.06)

        for a in self.ax:
            a.set_facecolor('#181818')

        # Linhas de plotagem
        (self.line_pro_speed,) = self.ax[0].plot([], [], color="#005AFF", linewidth=1.5, label="VER (F1 Real)")
        (self.line_my_speed,) = self.ax[0].plot([], [], color="#00FFCC", linewidth=1.5, label="Você")
        (self.line_pro_thr,) = self.ax[1].plot([], [], color="#005AFF", alpha=0.5, linewidth=1.2)
        (self.line_my_thr,) = self.ax[1].plot([], [], color="#00FFCC", linewidth=1.2)
        (self.line_my_brk,) = self.ax[2].plot([], [], color="#FF3366", label="Freio (%)", linewidth=1.2)
        (self.line_my_str,) = self.ax[2].plot([], [], color="#FFCC00", alpha=0.7, label="Volante (%)", linewidth=1.0)

        # Configurações de Eixos
        self.ax[0].set_ylabel("Speed (km/h)", fontsize=10)
        self.ax[0].set_ylim(0, 360)
        self.ax[0].grid(True, alpha=0.15)
        self.ax[0].legend(loc="lower right", fontsize=9)

        self.ax[1].set_ylabel("Throttle %", fontsize=10)
        self.ax[1].set_yticks([0, 50, 100])
        self.ax[1].grid(True, alpha=0.15)

        self.ax[2].set_ylabel("Brake / Steer", fontsize=10)
        self.ax[2].set_xlabel("Distância na Pista (m)", fontsize=10)
        self.ax[2].grid(True, alpha=0.15)
        self.ax[2].legend(loc="upper right", fontsize=9)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Método de compatibilidade caso a UI tente chamar set_facecolor diretamente no componente
    def set_facecolor(self, color):
        self.fig.patch.set_facecolor(color)
        for a in self.ax:
            a.set_facecolor(color)
        self.canvas.draw_idle()

    def set_reference_lap(self, pro_dist, pro_speed, pro_throttle, track_max, title=""):
        self.ax[0].set_xlim(0, track_max)
        self.line_pro_speed.set_data(pro_dist, pro_speed)
        self.line_pro_thr.set_data(pro_dist, pro_throttle)
        if title:
            self.ax[0].set_title(title, fontsize=11)
        self.canvas.draw_idle()

    def update_live_telemetry(self, dist, speed, throttle, brake, steer):
        self.line_my_speed.set_data(dist, speed)
        self.line_my_thr.set_data(dist, throttle)
        self.line_my_brk.set_data(dist, brake)
        self.line_my_str.set_data(dist, steer)
        self.canvas.draw_idle()

    def reset_live_lines(self):
        self.line_my_speed.set_data([], [])
        self.line_my_thr.set_data([], [])
        self.line_my_brk.set_data([], [])
        self.line_my_str.set_data([], [])
        self.canvas.draw_idle()