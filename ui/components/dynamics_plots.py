import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors

class DynamicsPlots(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#070A12")
        self.map_mode = "SPEED_DELTA"
        self._last_data = None
        self._setup_ui()

    def _setup_ui(self):
        # 1. Barra Superior de Seleção do Modo
        top_bar = tk.Frame(self, bg="#0E1424", padx=10, pady=6, highlightthickness=1, highlightbackground="#1B283E")
        top_bar.pack(fill=tk.X, padx=6, pady=(6, 2))

        tk.Label(top_bar, text="MODO DO MAPA:", fg="#FFD000", bg="#0E1424", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        self.combo_mode = ttk.Combobox(
            top_bar,
            values=[
                "Delta de Velocidade (Onde você ganha/perde km/h)",
                "Mapa de Marchas Engatadas (1ª a 8ª)",
                "Diferencial de Marchas (Sua vs Referência)"
            ],
            state="readonly",
            width=48,
            font=("Segoe UI", 9)
        )
        self.combo_mode.set("Delta de Velocidade (Onde você ganha/perde km/h)")
        self.combo_mode.pack(side=tk.LEFT, padx=(0, 15))
        self.combo_mode.bind("<<ComboboxSelected>>", self._on_mode_changed)

        # 2. Split Principal: Lado Esquerdo (Gráficos + Legenda) e Lado Direito (Diagnóstico)
        main_split = tk.Frame(self, bg="#070A12")
        main_split.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        left_container = tk.Frame(main_split, bg="#070A12")
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Diagnóstico Lateral (Direita)
        self.diag_frame = tk.LabelFrame(main_split, text=" DIAGNÓSTICO DE CÂMBIO & VELOCIDADE ", fg="#FFD000", bg="#0E1424", font=("Segoe UI", 8, "bold"), padx=8, pady=8, width=380)
        self.diag_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(6, 0))
        self.diag_frame.pack_propagate(False)

        self.diag_text = tk.Text(self.diag_frame, bg="#070A12", fg="#E2E8F0", font=("Consolas", 8), borderwidth=0, wrap=tk.WORD)
        self.diag_text.pack(fill=tk.BOTH, expand=True)
        self.diag_text.insert(tk.END, "Carregue uma volta salva na barra lateral para gerar o diagnóstico.")
        self.diag_text.config(state=tk.DISABLED)

        # Gráficos Matplotlib (Mapa + G-G)
        plot_frame = tk.Frame(left_container, bg="#070A12")
        plot_frame.pack(fill=tk.BOTH, expand=True)

        # 3. PAINEL DE LEGENDA FIXO (Abaixo do mapa, fácil de enxergar)
        self.legend_frame = tk.LabelFrame(
            left_container, text=" LEGENDA VISUAL DO TRAÇADO ", fg="#FFD000", bg="#0E1424",
            font=("Segoe UI", 8, "bold"), padx=10, pady=6, highlightthickness=1, highlightbackground="#1B283E"
        )
        self.legend_frame.pack(fill=tk.X, pady=(2, 4))
        
        self.legend_content = tk.Frame(self.legend_frame, bg="#0E1424")
        self.legend_content.pack(fill=tk.X)
        self._build_legend_speed_delta()

        # Configuração Matplotlib
        plt.style.use("dark_background")
        self.fig, (self.ax_map, self.ax_gg) = plt.subplots(
            1, 2, figsize=(9.5, 6.8), gridspec_kw={'width_ratios': [1.4, 1]}
        )
        self.fig.patch.set_facecolor('#070A12')
        self.fig.subplots_adjust(left=0.03, right=0.97, top=0.92, bottom=0.05, wspace=0.18)

        self.ax_map.set_facecolor('#0B101D')
        self.ax_map.set_title("CIRCUIT TRACK MAP", fontsize=9, color="#E2E8F0", fontweight='bold', pad=8)
        self.ax_map.axis("off")
        self.track_collection = None
        self.dot_live_pos, = self.ax_map.plot([], [], 'o', color="#FFD000", markersize=7)

        # Colormaps
        self.cmap_delta = mcolors.LinearSegmentedColormap.from_list("v_delta", ["#EA0029", "#334155", "#00E676"])
        self.cmap_gears = matplotlib.colormaps["turbo"].resampled(8)
        self.cmap_geardiff = mcolors.LinearSegmentedColormap.from_list("gear_diff", ["#FFD000", "#00E5FF", "#EA0029"])

        # G-G Diagram
        self.ax_gg.set_facecolor('#0B101D')
        self.ax_gg.set_title("G-G DIAGRAM (FRICTION CIRCLE)", fontsize=9, color="#E2E8F0", fontweight='bold', pad=8)
        self.ax_gg.set_xlabel("Aceleração Lateral (G)", fontsize=8, color="#8A99AD", fontweight='bold')
        self.ax_gg.set_ylabel("Aceleração Longitudinal (G)", fontsize=8, color="#8A99AD", fontweight='bold')
        self.ax_gg.set_xlim(-5.0, 5.0)
        self.ax_gg.set_ylim(-5.0, 3.0)
        self.ax_gg.grid(True, color='#182338', linestyle='--', linewidth=0.6, alpha=0.7)
        self.ax_gg.tick_params(colors='#8A99AD', labelsize=8)
        for spine in self.ax_gg.spines.values():
            spine.set_color('#1B283E')

        for r in [1.0, 2.0, 3.0, 4.0]:
            circle = plt.Circle((0, 0), r, color='#1B283E', fill=False, linestyle=':', alpha=0.8)
            self.ax_gg.add_patch(circle)

        self.scatter_my_gg = self.ax_gg.scatter([], [], c="#FFD000", s=8, alpha=0.35)
        self.dot_live_gg, = self.ax_gg.plot([], [], 'o', color="#EA0029", markersize=7)

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _clear_legend(self):
        for widget in self.legend_content.winfo_children():
            widget.destroy()

    def _build_legend_speed_delta(self):
        self._clear_legend()
        # Vermelho -> Cinza/Neutro -> Verde
        items = [
            ("#EA0029", "Mais Lento (-25 a -5 km/h)", "Você perdendo velocidade em relação à referência"),
            ("#64748B", "Velocidade Equivalente (±0 km/h)", "Ritmo idêntico ou mesma volta"),
            ("#00E676", "Mais Rápido (+5 a +25 km/h)", "Você carregando mais velocidade no ápice/reta")
        ]
        for color, title, desc in items:
            row = tk.Frame(self.legend_content, bg="#0E1424")
            row.pack(side=tk.LEFT, expand=True, padx=8)
            box = tk.Canvas(row, width=16, height=12, bg=color, highlightthickness=1, highlightbackground="#FFFFFF")
            box.pack(side=tk.LEFT, padx=(0, 6))
            txt_f = tk.Frame(row, bg="#0E1424")
            txt_f.pack(side=tk.LEFT)
            tk.Label(txt_f, text=title, fg="#FFFFFF", bg="#0E1424", font=("Segoe UI", 8, "bold")).pack(anchor="w")
            tk.Label(txt_f, text=desc, fg="#8A99AD", bg="#0E1424", font=("Segoe UI", 7)).pack(anchor="w")

    def _build_legend_gears(self):
        self._clear_legend()
        gear_colors = [
            ("1ª", "#30123B"), ("2ª", "#466BE3"), ("3ª", "#28BBEC"), ("4ª", "#A2FC3C"),
            ("5ª", "#FBBA38"), ("6ª", "#F53817"), ("7ª", "#A80303"), ("8ª", "#7A0404")
        ]
        for gear_label, color in gear_colors:
            item = tk.Frame(self.legend_content, bg="#0E1424")
            item.pack(side=tk.LEFT, expand=True, padx=4)
            box = tk.Canvas(item, width=18, height=12, bg=color, highlightthickness=1, highlightbackground="#334155")
            box.pack(side=tk.LEFT, padx=(0, 4))
            tk.Label(item, text=gear_label, fg="#FFFFFF", bg="#0E1424", font=("Consolas", 9, "bold")).pack(side=tk.LEFT)

    def _build_legend_gear_diff(self):
        self._clear_legend()
        items = [
            ("#FFD000", "Marcha Mais Curta", "Você usou marcha menor (ex: 3ª vs 4ª da Ref)"),
            ("#00E5FF", "Mesma Marcha (Ideal)", "Você e a referência engataram a mesma marcha"),
            ("#EA0029", "Marcha Mais Longa", "Você usou marcha maior (ex: 5ª vs 4ª da Ref)")
        ]
        for color, title, desc in items:
            row = tk.Frame(self.legend_content, bg="#0E1424")
            row.pack(side=tk.LEFT, expand=True, padx=8)
            box = tk.Canvas(row, width=16, height=12, bg=color, highlightthickness=1, highlightbackground="#FFFFFF")
            box.pack(side=tk.LEFT, padx=(0, 6))
            txt_f = tk.Frame(row, bg="#0E1424")
            txt_f.pack(side=tk.LEFT)
            tk.Label(txt_f, text=title, fg="#FFFFFF", bg="#0E1424", font=("Segoe UI", 8, "bold")).pack(anchor="w")
            tk.Label(txt_f, text=desc, fg="#8A99AD", bg="#0E1424", font=("Segoe UI", 7)).pack(anchor="w")

    def _on_mode_changed(self, event):
        val = self.combo_mode.get()
        if "Delta de Velocidade" in val:
            self.map_mode = "SPEED_DELTA"
            self._build_legend_speed_delta()
        elif "Mapa de Marchas" in val:
            self.map_mode = "GEAR_USER"
            self._build_legend_gears()
        else:
            self.map_mode = "GEAR_DIFF"
            self._build_legend_gear_diff()

        if self._last_data:
            self.render_map_and_diagnostics(*self._last_data)

    def render_map_and_diagnostics(self, x_coords, z_coords, my_speed, my_gear, my_dist, pro_dist=None, pro_speed=None, pro_gear=None, g_lat=None, g_lon=None):
        self._last_data = (x_coords, z_coords, my_speed, my_gear, my_dist, pro_dist, pro_speed, pro_gear, g_lat, g_lon)
        if len(x_coords) < 10:
            return

        x = np.array(x_coords)
        z = np.array(z_coords)
        s = np.array(my_speed)
        g = np.array(my_gear)
        d = np.array(my_dist)

        if self.track_collection:
            try:
                self.track_collection.remove()
            except Exception:
                pass

        points = np.array([x, z]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        has_pro = pro_dist is not None and len(pro_dist) > 0 and pro_speed is not None and len(pro_speed) > 0

        if self.map_mode == "SPEED_DELTA" and has_pro:
            interp_pro_speed = np.interp(d, pro_dist, pro_speed)
            v_delta = s - interp_pro_speed
            norm = mcolors.Normalize(vmin=-25.0, vmax=25.0)
            self.track_collection = LineCollection(segments, cmap=self.cmap_delta, norm=norm)
            self.track_collection.set_array(v_delta[:-1])
        elif self.map_mode == "GEAR_USER":
            norm = mcolors.Normalize(vmin=1, vmax=8)
            self.track_collection = LineCollection(segments, cmap=self.cmap_gears, norm=norm)
            self.track_collection.set_array(g[:-1])
        elif self.map_mode == "GEAR_DIFF" and has_pro and pro_gear is not None and len(pro_gear) > 0:
            interp_pro_gear = np.interp(d, pro_dist, pro_gear)
            gear_diff = g - interp_pro_gear
            norm = mcolors.Normalize(vmin=-2, vmax=2)
            self.track_collection = LineCollection(segments, cmap=self.cmap_geardiff, norm=norm)
            self.track_collection.set_array(gear_diff[:-1])
        else:
            # Fallback para velocidade absoluta
            norm = mcolors.Normalize(vmin=max(0, s.min()), vmax=max(100, s.max()))
            self.track_collection = LineCollection(segments, cmap=matplotlib.colormaps["plasma"], norm=norm)
            self.track_collection.set_array(s[:-1])

        self.track_collection.set_linewidth(4.2)
        self.ax_map.add_collection(self.track_collection)

        margin = 80
        self.ax_map.set_xlim(x.min() - margin, x.max() + margin)
        self.ax_map.set_ylim(z.min() - margin, z.max() + margin)
        self.dot_live_pos.set_data([x[-1]], [z[-1]])

        if g_lat is not None and g_lon is not None and len(g_lat) > 0:
            lat = np.array(g_lat)
            lon = np.array(g_lon)
            self.scatter_my_gg.set_offsets(np.c_[lat, lon])
            self.dot_live_gg.set_data([lat[-1]], [lon[-1]])

        self.canvas.draw_idle()
        self._generate_feedback_report(d, s, g, pro_dist, pro_speed, pro_gear)

    def _generate_feedback_report(self, d, s, g, pro_dist, pro_speed, pro_gear):
        self.diag_text.config(state=tk.NORMAL)
        self.diag_text.delete("1.0", tk.END)

        has_pro = pro_dist is not None and len(pro_dist) > 0 and pro_speed is not None and len(pro_speed) > 0

        if not has_pro:
            self.diag_text.insert(tk.END, "════════════════════════════════════\n")
            self.diag_text.insert(tk.END, "  TELEMETRIA DA VOLTA SALVA\n")
            self.diag_text.insert(tk.END, "════════════════════════════════════\n\n")
            self.diag_text.insert(tk.END, f"• Velocidade Máxima: {s.max():.1f} km/h\n")
            self.diag_text.insert(tk.END, f"• Velocidade Média: {s.mean():.1f} km/h\n")
            if g.max() > 0:
                self.diag_text.insert(tk.END, f"• Marchas: {int(g[g>0].min())}ª a {int(g.max())}ª\n\n")
            self.diag_text.insert(tk.END, "ℹ️ Vá para a Aba 2 e clique em 'Comparar com FIA' para carregar a telemetria do piloto profissional e ver a análise curva a curva.")
            self.diag_text.config(state=tk.DISABLED)
            return

        interp_pro_speed = np.interp(d, pro_dist, pro_speed)
        v_diff = s - interp_pro_speed

        slower_pct = float((v_diff < -5.0).mean() * 100)
        faster_pct = float((v_diff > 5.0).mean() * 100)

        report = []
        report.append("════════════════════════════════════\n")
        report.append("  RELATÓRIO DE CÂMBIO & VELOCIDADE\n")
        report.append("════════════════════════════════════\n\n")
        report.append(f"• Déficit (>5 km/h lento): {slower_pct:.1f}%\n")
        report.append(f"• Vantagem (>5 km/h rápido): {faster_pct:.1f}%\n\n")
        report.append("─── APEX SPEED & GEAR BREAKDOWN ───\n\n")

        # Mínimos locais de velocidade para achar ápices
        window = 35
        corners = []
        for i in range(window, len(s) - window, window):
            local_min_idx = i - window + np.argmin(s[i-window : i+window])
            if s[local_min_idx] < 240 and local_min_idx not in corners:
                if not any(abs(local_min_idx - c) < 20 for c in corners):
                    corners.append(local_min_idx)

        for c_idx in corners[:9]:
            dist_m = d[c_idx]
            my_v = s[c_idx]
            pro_v = interp_pro_speed[c_idx]
            delta_v = my_v - pro_v
            my_g = int(g[c_idx])

            status_icon = "🟢" if delta_v >= -3.0 else "🔴"
            report.append(f"Trecho ~{int(dist_m)}m | {status_icon}\n")
            report.append(f"  V_min: {my_v:.1f} km/h (Ref: {pro_v:.1f} km/h | Δ {delta_v:+.1f})\n")
            
            if my_g > 0:
                report.append(f"  Sua Marcha: {my_g}ª marcha\n")

            if pro_gear is not None and len(pro_gear) > 0:
                pro_g_val = int(round(np.interp(dist_m, pro_dist, pro_gear)))
                if pro_g_val > 0 and my_g > 0:
                    if my_g < pro_g_val:
                        report.append(f"  ⚠️ CÂMBIO: Ref usou {pro_g_val}ª. Suba uma marcha p/ tracionar melhor.\n")
                    elif my_g > pro_g_val:
                        report.append(f"  ⚠️ CÂMBIO: Ref usou {pro_g_val}ª. Reduza mais uma p/ ter giro.\n")
                    else:
                        report.append(f"  ✓ CÂMBIO: Marcha ideal ({my_g}ª).\n")
            report.append("\n")

        self.diag_text.insert(tk.END, "".join(report))
        self.diag_text.config(state=tk.DISABLED)

    def reset_dynamics(self):
        if self.track_collection:
            try:
                self.track_collection.remove()
            except Exception:
                pass
            self.track_collection = None
        self.dot_live_pos.set_data([], [])
        self.scatter_my_gg.set_offsets(np.empty((0, 2)))
        self.dot_live_gg.set_data([], [])
        self._last_data = None
        self.canvas.draw_idle()