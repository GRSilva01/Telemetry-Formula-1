import tkinter as tk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TelemetryPlots(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#070A12")
        self._setup_figure()

    def _setup_figure(self):
        plt.style.use("dark_background")
        self.fig, self.ax = plt.subplots(
            4, 1, figsize=(11, 8.5), sharex=True, gridspec_kw={'height_ratios': [2.2, 1.1, 1.0, 1.0]}
        )
        self.fig.patch.set_facecolor('#070A12')
        self.fig.subplots_adjust(hspace=0.07, left=0.06, right=0.98, top=0.95, bottom=0.05)

        for a in self.ax:
            a.set_facecolor('#0B101D')
            a.grid(True, color='#182338', linestyle='--', linewidth=0.6, alpha=0.7)
            a.tick_params(colors='#8A99AD', labelsize=8)
            for spine in a.spines.values():
                spine.set_color('#1B283E')

        self.ax[0].set_xlim(0, 5800)
        # 0. Velocidade
        (self.line_pro_speed,) = self.ax[0].plot([], [], color="#00E5FF", linewidth=1.6, label="Referência FIA", alpha=0.9)
        (self.line_my_speed,) = self.ax[0].plot([], [], color="#FFD000", linewidth=1.8, label="Você")
        self.ax[0].set_ylabel("Speed (km/h)", fontsize=8, color="#8A99AD", fontweight='bold')
        self.ax[0].set_ylim(0, 360)
        self.ax[0].legend(loc="lower right", fontsize=8, facecolor='#0B101D', edgecolor='#1B283E')

        # 1. Delta
        (self.line_cum_delta,) = self.ax[1].plot([], [], color="#FFFFFF", linewidth=1.4, label="Δt Acumulado")
        self.ax[1].axhline(0, color="#FFD000", linestyle=":", linewidth=0.8, alpha=0.6)
        self.ax[1].set_ylabel("Delta (s)", fontsize=8, color="#8A99AD", fontweight='bold')
        self.ax[1].set_ylim(-2.0, 2.0)
        self.ax[1].legend(loc="upper right", fontsize=8, facecolor='#0B101D', edgecolor='#1B283E')

        # 2. Throttle
        (self.line_pro_thr,) = self.ax[2].plot([], [], color="#00E5FF", alpha=0.45, linewidth=1.2)
        (self.line_my_thr,) = self.ax[2].plot([], [], color="#FFD000", linewidth=1.4)
        self.ax[2].set_ylabel("Throttle %", fontsize=8, color="#8A99AD", fontweight='bold')
        self.ax[2].set_ylim(-5, 105)
        self.ax[2].set_yticks([0, 50, 100])

        # 3. Brake & Steer
        (self.line_my_brk,) = self.ax[3].plot([], [], color="#EA0029", label="Brake (%)", linewidth=1.4)
        (self.line_my_str,) = self.ax[3].plot([], [], color="#94A3B8", alpha=0.85, label="Steer (%)", linewidth=1.1)
        self.ax[3].set_ylabel("Brake/Steer", fontsize=8, color="#8A99AD", fontweight='bold')
        self.ax[3].set_ylim(-105, 105)
        self.ax[3].set_xlabel("Distância na Pista (m)", fontsize=8, color="#8A99AD", fontweight='bold')
        self.ax[3].legend(loc="upper right", fontsize=8, facecolor='#0B101D', edgecolor='#1B283E')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def set_reference_lap(self, pro_dist, pro_speed, pro_throttle, track_max, title=""):
        self.ax[0].set_xlim(0, max(track_max, 1000))
        self.line_pro_speed.set_data(pro_dist, pro_speed)
        self.line_pro_thr.set_data(pro_dist, pro_throttle)
        if title:
            self.ax[0].set_title(title, fontsize=9, color="#E2E8F0", fontweight='bold', pad=8)
        self.canvas.draw_idle()

    def clear_reference_lap(self, title=""):
        self.line_pro_speed.set_data([], [])
        self.line_pro_thr.set_data([], [])
        if title:
            self.ax[0].set_title(title, fontsize=9, color="#E2E8F0", fontweight='bold', pad=8)
        self.canvas.draw_idle()

    def update_telemetry_data(self, dist, speed, throttle, brake, steer, deltas=None, track_len=5800.0):
        if len(dist) == 0:
            self.reset_live_lines()
            return

        max_x = max(track_len, dist[-1] + 100.0) if len(dist) > 0 else 5800.0
        self.ax[0].set_xlim(0, max_x)

        self.line_my_speed.set_data(dist, speed)
        self.line_my_thr.set_data(dist, throttle)
        self.line_my_brk.set_data(dist, brake)
        self.line_my_str.set_data(dist, steer)

        if deltas is not None and len(deltas) > 0:
            self.line_cum_delta.set_data(dist, deltas)
            d_min, d_max = deltas.min(), deltas.max()
            margin = 0.5
            self.ax[1].set_ylim(min(d_min - margin, -1.0), max(d_max + margin, 1.0))
        else:
            self.line_cum_delta.set_data([], [])

        self.canvas.draw_idle()
        
    def reset_live_lines(self):
        self.line_my_speed.set_data([], [])
        self.line_cum_delta.set_data([], [])
        self.line_my_thr.set_data([], [])
        self.line_my_brk.set_data([], [])
        self.line_my_str.set_data([], [])
        self.canvas.draw_idle()