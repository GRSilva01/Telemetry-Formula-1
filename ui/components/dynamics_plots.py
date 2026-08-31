import tkinter as tk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors

class DynamicsPlots(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#121212")
        self._setup_figure()

    def _setup_figure(self):
        plt.style.use("dark_background")
        self.fig, (self.ax_map, self.ax_gg) = plt.subplots(
            1, 2, figsize=(11, 8), gridspec_kw={'width_ratios': [1.3, 1]}
        )
        self.fig.patch.set_facecolor('#121212')
        self.fig.subplots_adjust(left=0.06, right=0.95, top=0.92, bottom=0.08, wspace=0.25)

        # 1. Configuração do Track Map 2D
        self.ax_map.set_facecolor('#181818')
        self.ax_map.set_title("Track Map: Delta Heatmap vs VER", fontsize=11, color="#FFFFFF", pad=10)
        self.ax_map.axis("off")
        self.track_collection = None
        self.dot_live_pos, = self.ax_map.plot([], [], 'o', color="#00FFCC", markersize=7, label="Posição Atual")

        # Barra de Cores para o Delta
        self.cmap = plt.get_cmap("RdYlGn_r") # Verde = mais rápido, Vermelho = mais lento
        self.norm = mcolors.Normalize(vmin=-0.5, vmax=0.5)
        self.cbar = self.fig.colorbar(
            plt.cm.ScalarMappable(norm=self.norm, cmap=self.cmap),
            ax=self.ax_map,
            orientation='horizontal',
            fraction=0.046,
            pad=0.04
        )
        self.cbar.set_label("Delta Relativo (s) [Verde: Ganho | Vermelho: Perda]", fontsize=9, color="#AAAAAA")
        self.cbar.ax.tick_params(labelsize=8, colors="#AAAAAA")

        # 2. Configuração do G-G Diagram (Friction Circle)
        self.ax_gg.set_facecolor('#181818')
        self.ax_gg.set_title("G-G Diagram (Friction Circle)", fontsize=11, color="#FFFFFF", pad=10)
        self.ax_gg.set_xlabel("Aceleração Lateral (G)", fontsize=9, color="#AAAAAA")
        self.ax_gg.set_ylabel("Aceleração Longitudinal (G)", fontsize=9, color="#AAAAAA")
        self.ax_gg.set_xlim(-5.5, 5.5)
        self.ax_gg.set_ylim(-5.5, 3.5)
        self.ax_gg.grid(True, linestyle="--", alpha=0.2)

        # Círculos guias de 1G, 2G, 3G, 4G, 5G
        for r in [1.0, 2.0, 3.0, 4.0, 5.0]:
            circle = plt.Circle((0, 0), r, color='#333333', fill=False, linestyle=':', alpha=0.6)
            self.ax_gg.add_patch(circle)

        self.scatter_my_gg = self.ax_gg.scatter([], [], c="#00FFCC", s=10, alpha=0.4, label="Sua Volta")
        self.dot_live_gg, = self.ax_gg.plot([], [], 'o', color="#FFCC00", markersize=8, label="Ponto Atual")
        self.ax_gg.legend(loc="upper right", fontsize=8)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_dynamics(self, x_coords, z_coords, deltas, g_lat, g_lon):
        if len(x_coords) < 5:
            return

        # 1. Desenha o Traçado 2D com Delta Heatmap
        x = np.array(x_coords)
        z = np.array(z_coords)

        # Remove coleção anterior do traçado para evitar sobreposição pesada
        if self.track_collection:
            try:
                self.track_collection.remove()
            except ValueError:
                pass

        points = np.array([x, z]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        d_vals = np.array(deltas[:-1]) if len(deltas) >= len(x) else np.zeros(len(segments))
        
        self.track_collection = LineCollection(segments, cmap=self.cmap, norm=self.norm)
        self.track_collection.set_array(d_vals)
        self.track_collection.set_linewidth(3.5)
        self.ax_map.add_collection(self.track_collection)

        # Ajusta os limites da pista com margem
        margin = 80
        self.ax_map.set_xlim(x.min() - margin, x.max() + margin)
        self.ax_map.set_ylim(z.min() - margin, z.max() + margin)
        self.dot_live_pos.set_data([x[-1]], [z[-1]])

        # 2. Desenha o G-G Diagram
        lat = np.array(g_lat)
        lon = np.array(g_lon)
        self.scatter_my_gg.set_offsets(np.c_[lat, lon])
        self.dot_live_gg.set_data([lat[-1]], [lon[-1]])

        self.canvas.draw_idle()

    def reset_dynamics(self):
        if self.track_collection:
            try:
                self.track_collection.remove()
            except ValueError:
                pass
            self.track_collection = None
        self.dot_live_pos.set_data([], [])
        self.scatter_my_gg.set_offsets(np.empty((0, 2)))
        self.dot_live_gg.set_data([], [])
        self.canvas.draw_idle()