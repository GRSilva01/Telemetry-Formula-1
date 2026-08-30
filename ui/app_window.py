import os
import threading
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox

from config import UDP_IP, UDP_PORT, F1_SESSION, F1_DRIVER
from database.lap_repository import LapRepository
from ingestion.udp_listener import UDPEmitter
from services.fastf1_service import fastf1_service
from services.telemetry_analyzer import calculate_instant_delta
from ui.components.telemetry_plots import TelemetryPlots


class F1TelemetryApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("F1 Telemetry Analytics Suite")
        self.root.geometry("1400x900")
        self.root.configure(bg="#121212")

        # Estado da Aplicação
        self.lock = threading.Lock()
        self.mode = "LIVE"  # "LIVE" ou "HISTORICO"
        self.selected_year = 2024
        self.current_track = "Aguardando jogo..."
        self.track_length = 5000.0
        self.pro_loaded = False

        # Dados Profissional (FastF1)
        self.pro_dist = np.array([])
        self.pro_speed = np.array([])
        self.pro_throttle = np.array([])
        self.pro_time_sec = np.array([])
        self.pro_lap_time = "--:--.---"

        # Telemetria mais recente do carro
        self.latest_car = {
            "speed": 0.0,
            "throttle": 0.0,
            "brake": 0.0,
            "steer": 0.0,
            "gear": 0
        }

        # Buffers da volta ativa do jogador
        self.my_dist: List[float] = []
        self.my_speed: List[float] = []
        self.my_throttle: List[float] = []
        self.my_brake: List[float] = []
        self.my_steer: List[float] = []
        self.my_time_sec: List[float] = []
        self.prev_dist = 0.0

        # Monta a Interface
        self._setup_layout()
        self._refresh_history_list()

        # Inicia UDP Listener
        self._udp = UDPEmitter(
            udp_ip=UDP_IP,
            udp_port=UDP_PORT
        )
        self._udp.add_session_callback(self._on_session_data)
        self._udp.add_car_telemetry_callback(self._on_car_telemetry)
        self._udp.add_lap_data_callback(self._on_lap_data)
        self._udp.start()

        # Inicia loop de renderização a ~30-60 FPS na thread da interface gráfica
        self._ui_render_loop()

    def _setup_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, width=320, bg="#1E1E1E", padx=15, pady=15)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(self.sidebar, text="F1 TELEMETRY", fg="#00FFCC", bg="#1E1E1E", font=("Arial", 16, "bold")).pack(anchor="w")
        tk.Label(self.sidebar, text="Real-Time Performance Suite", fg="#888888", bg="#1E1E1E", font=("Arial", 9)).pack(anchor="w", pady=(0, 10))

        # Configuração de Temporada
        cfg_frame = tk.LabelFrame(self.sidebar, text=" Temporada de Referência ", fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 10, "bold"), padx=10, pady=8)
        cfg_frame.pack(fill=tk.X, pady=5)

        tk.Label(cfg_frame, text="Ano da F1 Real:", fg="#CCCCCC", bg="#1E1E1E", font=("Arial", 9)).pack(anchor="w")
        self.combo_year = ttk.Combobox(cfg_frame, values=["2026", "2025", "2024", "2023", "2022", "2021"], state="readonly", font=("Arial", 9))
        self.combo_year.set(str(self.selected_year))
        self.combo_year.pack(fill=tk.X, pady=(2, 4))
        self.combo_year.bind("<<ComboboxSelected>>", self._on_year_changed)

        # Delta HUD
        delta_frame = tk.LabelFrame(self.sidebar, text=f" LIVE DELTA vs {F1_DRIVER} ", fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 10, "bold"), padx=10, pady=8)
        delta_frame.pack(fill=tk.X, pady=5)

        self.lbl_delta = tk.Label(delta_frame, text="+0.000s", fg="#FFFFFF", bg="#262626", font=("Consolas", 22, "bold"), pady=6)
        self.lbl_delta.pack(fill=tk.X)

        # Status da Sessão
        status_frame = tk.LabelFrame(self.sidebar, text=" Status da Sessão ", fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 10, "bold"), padx=10, pady=8)
        status_frame.pack(fill=tk.X, pady=6)

        self.lbl_track = tk.Label(status_frame, text="Pista: Aguardando...", fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 9))
        self.lbl_track.pack(anchor="w", pady=2)

        self.lbl_pro = tk.Label(status_frame, text=f"Ref: {F1_DRIVER} (--:--.---)", fg="#005AFF", bg="#1E1E1E", font=("Arial", 9, "bold"))
        self.lbl_pro.pack(anchor="w", pady=2)

        self.lbl_live_speed = tk.Label(status_frame, text="Velocidade: 0 km/h", fg="#00FFCC", bg="#1E1E1E", font=("Arial", 9))
        self.lbl_live_speed.pack(anchor="w", pady=2)

        self.btn_live = tk.Button(self.sidebar, text="● MODO AO VIVO", bg="#00FFCC", fg="#000000", font=("Arial", 10, "bold"),
                                  relief=tk.FLAT, command=self._switch_to_live, pady=6)
        self.btn_live.pack(fill=tk.X, pady=6)

        # Histórico SQLite
        history_frame = tk.LabelFrame(self.sidebar, text=" Voltas Salvas (Banco de Dados) ", fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 10, "bold"), padx=5, pady=5)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.lap_listbox = tk.Listbox(history_frame, bg="#121212", fg="#FFFFFF", font=("Consolas", 8),
                                      selectbackground="#005AFF", selectforeground="#FFFFFF", borderwidth=0)
        self.lap_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(history_frame, command=self.lap_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lap_listbox.config(yscrollcommand=scrollbar.set)

        btn_frame = tk.Frame(self.sidebar, bg="#1E1E1E")
        btn_frame.pack(fill=tk.X, pady=6)

        tk.Button(btn_frame, text="Analisar Volta", bg="#333333", fg="#FFFFFF", font=("Arial", 9),
                  relief=tk.FLAT, command=self._load_selected_lap, pady=4).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        tk.Button(btn_frame, text="Atualizar", bg="#252525", fg="#AAAAAA", font=("Arial", 9),
                  relief=tk.FLAT, command=self._refresh_history_list, pady=4).pack(side=tk.RIGHT, padx=(4, 0))

        # Canvas dos Gráficos
        self._plots = TelemetryPlots(self.root)
        self._plots.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def _on_session_data(self, data: Dict[str, Any]):
        track_name = data.get("track_name")
        track_len = data.get("track_length", 5000.0)

        if track_name and track_name != "Desconhecido" and track_name != self.current_track:
            self.current_track = track_name
            self.track_length = track_len
            self._load_fastf1_reference(track_name, self.selected_year)

    def _on_car_telemetry(self, data: Dict[str, Any]):
        with self.lock:
            self.latest_car["speed"] = data.get("speed", 0.0)
            self.latest_car["throttle"] = data.get("throttle", 0.0)
            self.latest_car["brake"] = data.get("brake", 0.0)
            self.latest_car["steer"] = data.get("steer", 0.0)
            self.latest_car["gear"] = data.get("gear", 0)

    def _on_lap_data(self, data: Dict[str, Any]):
        dist = data.get("lap_distance", 0.0)
        cur_time_ms = data.get("current_lap_time_ms", 0)
        last_time_ms = data.get("last_lap_time_ms", 0)

        with self.lock:
            eff_len = self.track_length if self.track_length > 0 else 5000.0

            # Detecção de linha de chegada (Fim de Volta)
            if self.prev_dist > (eff_len * 0.85) and 0 <= dist < 100.0:
                if len(self.my_dist) > 200:
                    lap_s = (last_time_ms / 1000.0) if last_time_ms > 0 else (self.my_time_sec[-1])
                    
                    df_to_save = pd.DataFrame({
                        "Distance": list(self.my_dist),
                        "TimeMs": [int(t * 1000) for t in self.my_time_sec],
                        "Speed": list(self.my_speed),
                        "Throttle": list(self.my_throttle),
                        "Brake": list(self.my_brake),
                        "Steer": list(self.my_steer)
                    })

                    threading.Thread(
                        target=self._save_lap_async,
                        args=(self.current_track, lap_s, df_to_save, self.selected_year),
                        daemon=True
                    ).start()

                self.my_dist.clear()
                self.my_speed.clear()
                self.my_throttle.clear()
                self.my_brake.clear()
                self.my_steer.clear()
                self.my_time_sec.clear()
                self._plots.reset_live_lines()

            # Adiciona amostra se estiver avançando na pista
            if dist > 0 and (len(self.my_dist) == 0 or dist > self.my_dist[-1]):
                self.my_dist.append(dist)
                self.my_speed.append(self.latest_car["speed"])
                self.my_throttle.append(self.latest_car["throttle"])
                self.my_brake.append(self.latest_car["brake"])
                self.my_steer.append(self.latest_car["steer"] * 100.0)
                self.my_time_sec.append(cur_time_ms / 1000.0)
                self.prev_dist = dist

    def _save_lap_async(self, track_name, lap_time_sec, df, year):
        try:
            LapRepository.save_lap(track_name, lap_time_sec, df, year)
            self.root.after(0, self._refresh_history_list)
        except Exception as e:
            print(f"[!] Erro ao salvar volta no SQLite: {e}")

    def _load_fastf1_reference(self, track_name: str, year: int):
        self.pro_loaded = False
        self.lbl_pro.config(text=f"Ref: Carregando {year}...")

        def _fetch():
            res = fastf1_service.extract_reference_data(year, track_name, F1_SESSION, F1_DRIVER)
            if res.get("success"):
                with self.lock:
                    self.pro_dist = res["distance"]
                    self.pro_speed = res["speed"]
                    self.pro_throttle = res["throttle"]
                    self.pro_time_sec = res["time_sec"]
                    self.pro_lap_time = res["lap_time_str"]
                    self.pro_loaded = True

                self.root.after(0, lambda: self._apply_reference_to_ui(track_name, year))
            else:
                self.root.after(0, lambda: self.lbl_pro.config(text=f"Ref: Indisponível ({year})"))

        threading.Thread(target=_fetch, daemon=True).start()

    def _apply_reference_to_ui(self, track_name, year):
        self.lbl_pro.config(text=f"Ref: {F1_DRIVER} '{str(year)[2:]} ({self.pro_lap_time})")
        t_max = max(self.pro_dist.max(), self.track_length)
        title = f"Live Telemetry: {track_name} | Referência: VER {year} ({self.pro_lap_time})"
        self._plots.set_reference_lap(self.pro_dist, self.pro_speed, self.pro_throttle, t_max, title)

    def _ui_render_loop(self):
        """Loop executado diretamente na thread principal do Tkinter"""
        if self.mode == "LIVE":
            with self.lock:
                self.lbl_track.config(text=f"Pista: {self.current_track}")
                self.lbl_live_speed.config(text=f"Velocidade: {int(self.latest_car['speed'])} km/h")

                if len(self.my_dist) > 5:
                    d = np.array(self.my_dist)
                    s = np.array(self.my_speed)
                    t = np.array(self.my_throttle)
                    b = np.array(self.my_brake)
                    st = np.array(self.my_steer)

                    self._plots.update_live_telemetry(d, s, t, b, st)

                    # Atualiza o Delta no HUD
                    if self.pro_loaded and d[-1] > 30:
                        inst_delta = calculate_instant_delta(
                            self.pro_dist,
                            self.pro_time_sec,
                            d[-1],
                            self.my_time_sec[-1]
                        )
                        self._update_delta_widget(inst_delta)

        # Repete a cada 33ms (~30 FPS estável sem engasgos)
        self.root.after(33, self._ui_render_loop)

    def _update_delta_widget(self, delta_val: float):
        if delta_val < 0:
            self.lbl_delta.config(text=f"{delta_val:+.3f}s", fg="#00FF66", bg="#0d2818")
        else:
            self.lbl_delta.config(text=f"{delta_val:+.3f}s", fg="#FF3366", bg="#330d18")

    def _on_year_changed(self, event):
        self.selected_year = int(self.combo_year.get())
        if self.current_track and self.current_track != "Aguardando jogo...":
            self._plots.reset_live_lines()
            self._load_fastf1_reference(self.current_track, self.selected_year)

    def _switch_to_live(self):
        self.mode = "LIVE"
        self.btn_live.config(bg="#00FFCC", text="● MODO AO VIVO")
        self._plots.reset_live_lines()

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

        # Carrega dados de referência se a pista mudou
        if self.current_track != selected_lap.track_name or not self.pro_loaded:
            self.current_track = selected_lap.track_name
            self._load_fastf1_reference(selected_lap.track_name, selected_lap.year_reference)

        # Plota estático
        d = df["Distance"].to_numpy()
        s = df["Speed"].to_numpy()
        t = df["Throttle"].to_numpy()
        b = df["Brake"].to_numpy()
        st = (df["Steer"] * 100.0).to_numpy()

        self._plots.update_live_telemetry(d, s, t, b, st)

        if self.pro_loaded:
            final_delta = (df["TimeMs"].iloc[-1] / 1000.0) - self.pro_time_sec[-1]
            self._update_delta_widget(final_delta)