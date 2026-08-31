import os
import threading
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox

from config import UDP_IP, UDP_PORT, F1_SESSION, F1_DRIVER
from database.lap_repository import LapRepository
from ingestion.udp_listener import UDPEmitter
from services.fastf1_service import fastf1_service
from services.telemetry_analyzer import (
    calculate_instant_delta,
    calculate_cumulative_deltas,
    generate_mini_sectors,
    calculate_mini_sectors_status,
    calculate_trail_braking_score
)
from ui.components.telemetry_plots import TelemetryPlots
from ui.components.dynamics_plots import DynamicsPlots
from ui.components.tyres_sectors_panel import TyresSectorsPanel


class F1TelemetryApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("F1 Telemetry Analytics Suite - Engineering Station")
        self.root.geometry("1550x940")
        self.root.configure(bg="#121212")

        # Mutex Thread-Safe
        self.lock = threading.Lock()

        # Estado da Aplicação
        self.mode = "LIVE"
        self.selected_year = 2024
        self.current_track = "Aguardando jogo..."
        self.track_length = 5000.0
        self.pro_loaded = False
        self._is_loading_ref = False

        # Controle de Estado da Volta
        self.is_lap_active = False
        self.prev_dist = 0.0

        # Dados de Referência (FastF1)
        self.pro_dist = np.array([])
        self.pro_speed = np.array([])
        self.pro_throttle = np.array([])
        self.pro_time_sec = np.array([])
        self.pro_lap_time = "--:--.---"
        self.pro_session_used = "Q"
        self.pro_year_used = 2024

        # Telemetria mais recente
        self.latest_car = {
            "speed": 0.0, "throttle": 0.0, "brake": 0.0, "steer": 0.0, "gear": 0,
            "tyres_surf_temp": [0, 0, 0, 0]
        }
        self.latest_motion = {"x": 0.0, "z": 0.0, "g_lat": 0.0, "g_lon": 0.0}

        # Buffers da volta ativa
        self.my_dist: List[float] = []
        self.my_speed: List[float] = []
        self.my_throttle: List[float] = []
        self.my_brake: List[float] = []
        self.my_steer: List[float] = []
        self.my_time_sec: List[float] = []
        self.my_pos_x: List[float] = []
        self.my_pos_z: List[float] = []
        self.my_g_lat: List[float] = []
        self.my_g_lon: List[float] = []
        self.my_deltas: List[float] = []

        # Flag para reset thread-safe na GUI
        self._needs_ui_reset = False

        # Mini-Setores
        self.mini_sectors = generate_mini_sectors(5000.0, 20)

        # Montagem dos Componentes
        self._setup_styles()
        self._setup_layout()
        self._refresh_history_list()

        # Inicia UDP Listener
        self._udp = UDPEmitter(udp_ip=UDP_IP, udp_port=UDP_PORT)
        self._udp.add_session_callback(self._on_session_data)
        self._udp.add_car_telemetry_callback(self._on_car_telemetry)
        self._udp.add_lap_data_callback(self._on_lap_data)
        self._udp.add_motion_callback(self._on_motion_data)
        self._udp.start()

        # Render loop da thread principal
        self._ui_render_loop()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#121212", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1E1E1E", foreground="#AAAAAA", padding=[15, 6], font=("Arial", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#2A2A2A")], foreground=[("selected", "#00FFCC")])

    def _setup_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, width=330, bg="#1E1E1E", padx=12, pady=12)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(self.sidebar, text="F1 TELEMETRY", fg="#00FFCC", bg="#1E1E1E", font=("Arial", 15, "bold")).pack(anchor="w")
        tk.Label(self.sidebar, text="Performance Engineering Suite", fg="#888888", bg="#1E1E1E", font=("Arial", 8)).pack(anchor="w", pady=(0, 8))

        # Temporada
        cfg_frame = tk.LabelFrame(self.sidebar, text=" Temporada de Referência ", fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 9, "bold"), padx=8, pady=6)
        cfg_frame.pack(fill=tk.X, pady=4)

        self.combo_year = ttk.Combobox(cfg_frame, values=["2026", "2025", "2024", "2023", "2022"], state="readonly", font=("Arial", 9))
        self.combo_year.set(str(self.selected_year))
        self.combo_year.pack(fill=tk.X, pady=2)
        self.combo_year.bind("<<ComboboxSelected>>", self._on_year_changed)

        # Delta HUD
        delta_frame = tk.LabelFrame(self.sidebar, text=f" LIVE DELTA vs {F1_DRIVER} ", fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 9, "bold"), padx=8, pady=6)
        delta_frame.pack(fill=tk.X, pady=4)

        self.lbl_delta = tk.Label(delta_frame, text="+0.000s", fg="#FFFFFF", bg="#262626", font=("Consolas", 20, "bold"), pady=4)
        self.lbl_delta.pack(fill=tk.X)

        # Pneus & Mini-Setores
        self._tyres_panel = TyresSectorsPanel(self.sidebar)
        self._tyres_panel.pack(fill=tk.X, pady=4)

        # Status
        status_frame = tk.LabelFrame(self.sidebar, text=" Status da Sessão ", fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 9, "bold"), padx=8, pady=6)
        status_frame.pack(fill=tk.X, pady=4)

        self.lbl_track = tk.Label(status_frame, text="Pista: Aguardando...", fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 8))
        self.lbl_track.pack(anchor="w")
        self.lbl_pro = tk.Label(status_frame, text=f"Ref: {F1_DRIVER} (--:--.---)", fg="#005AFF", bg="#1E1E1E", font=("Arial", 8, "bold"))
        self.lbl_pro.pack(anchor="w")

        self.btn_live = tk.Button(self.sidebar, text="● MODO AO VIVO", bg="#00FFCC", fg="#000000", font=("Arial", 9, "bold"),
                                  relief=tk.FLAT, command=self._switch_to_live, pady=4)
        self.btn_live.pack(fill=tk.X, pady=4)

        # Histórico SQLite
        history_frame = tk.LabelFrame(self.sidebar, text=" Voltas Salvas ", fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 9, "bold"), padx=4, pady=4)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        self.lap_listbox = tk.Listbox(history_frame, bg="#121212", fg="#FFFFFF", font=("Consolas", 8),
                                      selectbackground="#005AFF", selectforeground="#FFFFFF", borderwidth=0)
        self.lap_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(history_frame, command=self.lap_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lap_listbox.config(yscrollcommand=scrollbar.set)

        btn_h = tk.Frame(self.sidebar, bg="#1E1E1E")
        btn_h.pack(fill=tk.X, pady=4)
        tk.Button(btn_h, text="Analisar", bg="#333333", fg="#FFFFFF", font=("Arial", 8), relief=tk.FLAT, command=self._load_selected_lap).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(btn_h, text="Atualizar", bg="#252525", fg="#AAAAAA", font=("Arial", 8), relief=tk.FLAT, command=self._refresh_history_list).pack(side=tk.RIGHT, padx=2)

        # Abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Aba 1: Telemetria Linear
        self.tab_linear = tk.Frame(self.notebook, bg="#121212")
        self._plots = TelemetryPlots(self.tab_linear)
        self._plots.pack(fill=tk.BOTH, expand=True)
        self.notebook.add(self.tab_linear, text=" Telemetria Linear & Delta ")

        # Aba 2: Dinâmica Veicular & Track Map
        self.tab_dynamics = tk.Frame(self.notebook, bg="#121212")
        self._dynamics = DynamicsPlots(self.tab_dynamics)
        self._dynamics.pack(fill=tk.BOTH, expand=True)
        self.notebook.add(self.tab_dynamics, text=" Dinâmica Veicular & Track Map ")

    def _on_session_data(self, data: Dict[str, Any]):
        track_name = data.get("track_name")
        track_len = data.get("track_length", 5000.0)

        if track_name and track_name != "Desconhecido" and track_name != self.current_track:
            with self.lock:
                self.current_track = track_name
                self.track_length = track_len
                self.mini_sectors = generate_mini_sectors(track_len, 20)
            self._load_fastf1_reference(track_name, self.selected_year)

    def _on_car_telemetry(self, data: Dict[str, Any]):
        with self.lock:
            self.latest_car["speed"] = data.get("speed", 0.0)
            self.latest_car["throttle"] = data.get("throttle", 0.0)
            self.latest_car["brake"] = data.get("brake", 0.0)
            self.latest_car["steer"] = data.get("steer", 0.0)
            self.latest_car["gear"] = data.get("gear", 0)
            self.latest_car["tyres_surf_temp"] = data.get("tyres_surf_temp", [0, 0, 0, 0])

    def _on_motion_data(self, data: Dict[str, Any]):
        with self.lock:
            self.latest_motion["x"] = data.get("world_pos_x", 0.0)
            self.latest_motion["z"] = data.get("world_pos_z", 0.0)
            self.latest_motion["g_lat"] = data.get("g_force_lat", 0.0)
            self.latest_motion["g_lon"] = data.get("g_force_lon", 0.0)

    def _on_lap_data(self, data: Dict[str, Any]):
        dist = data.get("lap_distance", 0.0)
        cur_time_ms = data.get("current_lap_time_ms", 0)
        last_time_ms = data.get("last_lap_time_ms", 0)

        with self.lock:
            eff_len = self.track_length if self.track_length > 0 else 5800.0

            # 1. Reset se a distância caiu bruscamente (Cruzou linha de chegada ou reiniciou no menu)
            if self.prev_dist > 300.0 and dist < (self.prev_dist - 200.0):
                # Salva a volta que completou
                if self.prev_dist > (eff_len * 0.80) and len(self.my_dist) > 100:
                    lap_s = (last_time_ms / 1000.0) if last_time_ms > 0 else (self.my_time_sec[-1] if self.my_time_sec else 0.0)
                    if lap_s > 20.0:
                        df_to_save = pd.DataFrame({
                            "Distance": list(self.my_dist),
                            "TimeMs": [int(t * 1000) for t in self.my_time_sec],
                            "Speed": list(self.my_speed),
                            "Throttle": list(self.my_throttle),
                            "Brake": list(self.my_brake),
                            "Steer": list(self.my_steer),
                            "WorldPosX": list(self.my_pos_x),
                            "WorldPosZ": list(self.my_pos_z),
                            "GForceLat": list(self.my_g_lat),
                            "GForceLon": list(self.my_g_lon)
                        })
                        threading.Thread(
                            target=self._save_lap_async,
                            args=(self.current_track, lap_s, df_to_save, self.selected_year),
                            daemon=True
                        ).start()

                # Limpa os dados em memória e sinaliza para a thread principal limpar a tela
                self._clear_raw_buffers()
                self._needs_ui_reset = True

                # Se caiu perto do metro zero, já ativa a gravação da nova volta
                self.is_lap_active = (0.0 <= dist < 150.0)
                self.prev_dist = max(dist, 0.0)
                return

            # 2. Ativação no primeiro cruzamento da linha de largada
            if not self.is_lap_active:
                if 0.0 <= dist < 150.0:
                    self.is_lap_active = True
                    self._clear_raw_buffers()
                    self._needs_ui_reset = True
                else:
                    self.prev_dist = dist
                    return

            # 3. Ingestão estritamente sequencial da volta ativa
            if self.is_lap_active and dist >= 0.0:
                if len(self.my_dist) == 0:
                    self._append_sample(dist, cur_time_ms)
                elif dist > self.my_dist[-1]:
                    if (dist - self.my_dist[-1]) < 300.0:
                        self._append_sample(dist, cur_time_ms)

                self.prev_dist = dist

    def _append_sample(self, dist: float, cur_time_ms: int):
        cur_t_sec = cur_time_ms / 1000.0
        self.my_dist.append(dist)
        self.my_speed.append(self.latest_car["speed"])
        self.my_throttle.append(self.latest_car["throttle"])
        self.my_brake.append(self.latest_car["brake"])
        self.my_steer.append(self.latest_car["steer"] * 100.0)
        self.my_time_sec.append(cur_t_sec)
        self.my_pos_x.append(self.latest_motion["x"])
        self.my_pos_z.append(self.latest_motion["z"])
        self.my_g_lat.append(self.latest_motion["g_lat"])
        self.my_g_lon.append(self.latest_motion["g_lon"])

        if self.pro_loaded and len(self.pro_dist) > 0 and dist > 15 and cur_t_sec > 0:
            inst_delta = calculate_instant_delta(self.pro_dist, self.pro_time_sec, dist, cur_t_sec)
            self.my_deltas.append(inst_delta)
        else:
            self.my_deltas.append(0.0)

    def _clear_raw_buffers(self):
        self.my_dist.clear()
        self.my_speed.clear()
        self.my_throttle.clear()
        self.my_brake.clear()
        self.my_steer.clear()
        self.my_time_sec.clear()
        self.my_pos_x.clear()
        self.my_pos_z.clear()
        self.my_g_lat.clear()
        self.my_g_lon.clear()
        self.my_deltas.clear()

    def _save_lap_async(self, track_name, lap_time_sec, df, year):
        try:
            LapRepository.save_lap(track_name, lap_time_sec, df, year)
            self.root.after(0, self._refresh_history_list)
        except Exception as e:
            print(f"[!] Erro ao salvar volta no SQLite: {e}")

    def _load_fastf1_reference(self, track_name: str, year: int):
        if self._is_loading_ref:
            return

        self._is_loading_ref = True
        self.pro_loaded = False
        self.lbl_pro.config(text=f"Ref: Carregando {year}...")

        def _fetch():
            try:
                res = fastf1_service.extract_reference_data(year, track_name, F1_SESSION, F1_DRIVER)
                if res.get("success"):
                    with self.lock:
                        self.pro_dist = res["distance"]
                        self.pro_speed = res["speed"]
                        self.pro_throttle = res["throttle"]
                        self.pro_time_sec = res["time_sec"]
                        self.pro_lap_time = res["lap_time_str"]
                        self.pro_session_used = res.get("session_used", F1_SESSION)
                        self.pro_year_used = res.get("year_used", year)
                        self.pro_loaded = True

                    self.root.after(0, lambda: self._apply_reference_to_ui(track_name, year))
                else:
                    self.root.after(0, lambda: self.lbl_pro.config(text=f"Ref: Indisponível ({year})"))
            finally:
                self._is_loading_ref = False

        threading.Thread(target=_fetch, daemon=True).start()

    def _apply_reference_to_ui(self, track_name, year):
        session_used = getattr(self, "pro_session_used", "Q")
        year_used = getattr(self, "pro_year_used", year)
        self.lbl_pro.config(text=f"Ref: {F1_DRIVER} '{str(year_used)[2:]} [{session_used}] ({self.pro_lap_time})")
        t_max = max(self.pro_dist.max(), self.track_length)
        title = f"Live Telemetry: {track_name} | Referência: {F1_DRIVER} {year_used} [{session_used}] ({self.pro_lap_time})"
        self._plots.set_reference_lap(self.pro_dist, self.pro_speed, self.pro_throttle, t_max, title)

    def _ui_render_loop(self):
        """Loop executado estritamente na thread principal do Tkinter"""
        if self.mode == "LIVE":
            with self.lock:
                self.lbl_track.config(text=f"Pista: {self.current_track}")

                # Se a thread UDP sinalizou reset, limpa a tela de forma segura
                if self._needs_ui_reset:
                    self._plots.reset_live_lines()
                    self._dynamics.reset_dynamics()
                    self._tyres_panel.reset_panel()
                    self._needs_ui_reset = False

                n_samples = len(self.my_dist)
                if n_samples > 2 and self.is_lap_active:
                    d = np.array(self.my_dist)
                    s = np.array(self.my_speed)
                    t = np.array(self.my_throttle)
                    b = np.array(self.my_brake)
                    st = np.array(self.my_steer)
                    deltas_arr = np.array(self.my_deltas)

                    self._plots.update_live_telemetry(d, s, deltas_arr, t, b, st)

                    self._dynamics.update_dynamics(
                        self.my_pos_x,
                        self.my_pos_z,
                        self.my_deltas,
                        self.my_g_lat,
                        self.my_g_lon
                    )

                    tb_score = calculate_trail_braking_score(b, st)
                    self._tyres_panel.update_tyres(self.latest_car["tyres_surf_temp"], tb_score)

                    sec_status = calculate_mini_sectors_status(self.mini_sectors, d, deltas_arr)
                    self._tyres_panel.update_sectors(sec_status)

                    if self.pro_loaded and d[-1] > 30 and len(self.pro_dist) > 0 and len(deltas_arr) > 0:
                        self._update_delta_widget(deltas_arr[-1])

        self.root.after(33, self._ui_render_loop)

    def _update_delta_widget(self, delta_val: float):
        if delta_val < 0:
            self.lbl_delta.config(text=f"{delta_val:+.3f}s", fg="#00FF66", bg="#0d2818")
        else:
            self.lbl_delta.config(text=f"{delta_val:+.3f}s", fg="#FF3366", bg="#330d18")

    def _on_year_changed(self, event):
        self.selected_year = int(self.combo_year.get())
        if self.current_track and self.current_track != "Aguardando jogo...":
            self.is_lap_active = False
            self._needs_ui_reset = True
            self._load_fastf1_reference(self.current_track, self.selected_year)

    def _switch_to_live(self):
        self.mode = "LIVE"
        self.btn_live.config(bg="#00FFCC", text="● MODO AO VIVO")
        self.is_lap_active = False
        self._clear_raw_buffers()
        self._needs_ui_reset = True

    def _refresh_history_list(self):
        self.lap_listbox.delete(0, tk.END)
        self.saved_laps = LapRepository.get_all_laps()
        for lap in self.saved_laps:
            time_str = f"{int(lap.lap_time_seconds // 60)}m{int(lap.lap_time_seconds % 60):02d}s{int((lap.lap_time_seconds % 1)*1000):03d}"
            date_str = lap.date_recorded.strftime("%d/%m %H:%M")
            self.lap_listbox.insert(tk.END, f"#{lap.id} | {lap.track_name} | {time_str} | {date_str}")

    def _load_selected_lap(self):
        selection = self.lap_listbox.curselection()
        if not selection:
            messagebox.showinfo("Aviso", "Selecione uma volta salva na lista!")
            return

        selected_lap = self.saved_laps[selection[0]]
        self.mode = "HISTORICO"
        self.btn_live.config(bg="#333333", text="Visualizando Histórico")

        df = LapRepository.get_lap_telemetry_df(selected_lap.id)
        if df.empty:
            messagebox.showwarning("Aviso", "Não há telemetria para esta volta.")
            return

        if self.current_track != selected_lap.track_name or not self.pro_loaded:
            self.current_track = selected_lap.track_name
            self.mini_sectors = generate_mini_sectors(5000.0, 20)
            self._load_fastf1_reference(selected_lap.track_name, selected_lap.year_reference)

        d = df["Distance"].to_numpy()
        s = df["Speed"].to_numpy()
        t = df["Throttle"].to_numpy()
        b = df["Brake"].to_numpy()
        st = (df["Steer"] * 100.0).to_numpy()

        if self.pro_loaded and len(self.pro_dist) > 0:
            hist_times = (df["TimeMs"] / 1000.0).to_numpy()
            deltas = calculate_cumulative_deltas(d, hist_times, self.pro_dist, self.pro_time_sec)
        else:
            deltas = np.zeros_like(d)

        self._plots.update_live_telemetry(d, s, deltas, t, b, st)

        self._dynamics.update_dynamics(
            df["WorldPosX"].to_list(),
            df["WorldPosZ"].to_list(),
            deltas.tolist(),
            df["GForceLat"].to_list(),
            df["GForceLon"].to_list()
        )

        sec_status = calculate_mini_sectors_status(self.mini_sectors, d, deltas)
        self._tyres_panel.update_sectors(sec_status)
        tb_score = calculate_trail_braking_score(b, st)
        self._tyres_panel.lbl_trail_score.config(text=f"{tb_score:.1f}%")

        if len(deltas) > 0:
            self._update_delta_widget(deltas[-1])