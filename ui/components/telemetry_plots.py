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
            4, 1, figsize=(11, 8.5), sharex=True, gridspec_kw={'height_ratios': [2.2, 1.2, 1.0, 1.0]}
        )
        self.fig.patch.set_facecolor('#121212')
        self.fig.subplots_adjust(hspace=0.08, left=0.07, right=0.98, top=0.95, bottom=0.05)

        for a in self.ax:
            a.set_facecolor('#181818')

        # 0. Velocidade
        (self.line_pro_speed,) = self.ax[0].plot([], [], color="#005AFF", linewidth=1.8, label="VER (FIA Real)")
        (self.line_my_speed,) = self.ax[0].plot([], [], color="#00FFCC", linewidth=1.5, label="Você")
        self.ax[0].set_ylabel("Speed (km/h)", fontsize=9)
        self.ax[0].set_ylim(0, 360)
        self.ax[0].grid(True, alpha=0.15)
        self.ax[0].legend(loc="lower right", fontsize=8)

        # 1. Delta Cumulativo
        (self.line_cum_delta,) = self.ax[1].plot([], [], color="#FFFFFF", linewidth=1.4, label="Δt Cumulativo")
        self.ax[1].axhline(0, color="#555555", linestyle="--", linewidth=0.8)
        self.ax[1].set_ylabel("Delta (s)", fontsize=9)
        self.ax[1].set_ylim(-2.0, 2.0)
        self.ax[1].grid(True, alpha=0.15)
        self.ax[1].legend(loc="upper right", fontsize=8)

        # 2. Throttle
        (self.line_pro_thr,) = self.ax[2].plot([], [], color="#005AFF", alpha=0.5, linewidth=1.2)
        (self.line_my_thr,) = self.ax[2].plot([], [], color="#00FFCC", linewidth=1.3)
        self.ax[2].set_ylabel("Throttle %", fontsize=9)
        self.ax[2].set_ylim(-5, 105)
        self.ax[2].set_yticks([0, 50, 100])
        self.ax[2].grid(True, alpha=0.15)

        # 3. Brake & Steer
        (self.line_my_brk,) = self.ax[3].plot([], [], color="#FF3366", label="Freio (%)", linewidth=1.3)
        (self.line_my_str,) = self.ax[3].plot([], [], color="#FFCC00", alpha=0.7, label="Volante (%)", linewidth=1.0)
        self.ax[3].set_ylabel("Brake/Steer", fontsize=9)
        self.ax[3].set_ylim(-105, 105)
        self.ax[3].set_xlabel("Distância na Pista (m)", fontsize=9)
        self.ax[3].grid(True, alpha=0.15)
        self.ax[3].legend(loc="upper right", fontsize=8)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def set_reference_lap(self, pro_dist, pro_speed, pro_throttle, track_max, title=""):
        self.ax[0].set_xlim(0, max(track_max, 1000))
        self.line_pro_speed.set_data(pro_dist, pro_speed)
        self.line_pro_thr.set_data(pro_dist, pro_throttle)
        if title:
            self.ax[0].set_title(title, fontsize=10, color="#FFFFFF")
        self.canvas.draw_idle()

    def update_live_telemetry(self, dist, speed, deltas, throttle, brake, steer):
        if len(dist) == 0:
            self.reset_live_lines()
            return

        self.line_my_speed.set_data(dist, speed)
        self.line_cum_delta.set_data(dist, deltas)
        self.line_my_thr.set_data(dist, throttle)
        self.line_my_brk.set_data(dist, brake)
        self.line_my_str.set_data(dist, steer)

        if len(deltas) > 0:
            d_min, d_max = deltas.min(), deltas.max()
            margin = 0.5
            self.ax[1].set_ylim(min(d_min - margin, -1.0), max(d_max + margin, 1.0))

        self.canvas.draw_idle()

    def reset_live_lines(self):
        self.line_my_speed.set_data([], [])
        self.line_cum_delta.set_data([], [])
        self.line_my_thr.set_data([], [])
        self.line_my_brk.set_data([], [])
        self.line_my_str.set_data([], [])
        self.canvas.draw_idle()