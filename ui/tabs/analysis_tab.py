import threading
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from database.lap_repository import LapRepository
from services.fastf1_service import fastf1_service
from services.telemetry_analyzer import calculate_cumulative_deltas
from ui.components.telemetry_plots import TelemetryPlots

class AnalysisTab(tk.Frame):
    def __init__(self, parent, on_compare_complete_cb=None):
        super().__init__(parent, bg="#070A12")
        self.on_compare_complete_cb = on_compare_complete_cb
        self.selected_lap = None
        self._setup_ui()

    def _setup_ui(self):
        ctrl_bar = tk.Frame(self, bg="#0E1424", padx=10, pady=8, highlightthickness=1, highlightbackground="#1B283E")
        ctrl_bar.pack(fill=tk.X, padx=6, pady=6)

        tk.Label(ctrl_bar, text="Ano:", fg="#8A99AD", bg="#0E1424", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self.combo_year = ttk.Combobox(ctrl_bar, values=["2026", "2025", "2024", "2023", "2022"], width=6, state="readonly", font=("Segoe UI", 9))
        self.combo_year.set("2024")
        self.combo_year.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(ctrl_bar, text="Sessão:", fg="#8A99AD", bg="#0E1424", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self.combo_session = ttk.Combobox(ctrl_bar, values=["Q (Classificação)", "R (Corrida)", "FP3", "FP2", "FP1"], width=18, state="readonly", font=("Segoe UI", 9))
        self.combo_session.set("Q (Classificação)")
        self.combo_session.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(ctrl_bar, text="Piloto:", fg="#8A99AD", bg="#0E1424", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self.combo_driver = ttk.Combobox(ctrl_bar, values=["VER", "PER", "NOR", "LEC", "HAM", "PIA"], width=6, state="readonly", font=("Segoe UI", 9))
        self.combo_driver.set("VER")
        self.combo_driver.pack(side=tk.LEFT, padx=(0, 12))

        tk.Button(ctrl_bar, text="Comparar com FIA", bg="#00E5FF", fg="#070A12", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, command=self.fetch_analysis_reference, padx=8).pack(side=tk.LEFT)

        self.lbl_status = tk.Label(ctrl_bar, text="Selecione uma volta na barra lateral e clique em 'Carregar Volta'.", fg="#8A99AD", bg="#0E1424", font=("Segoe UI", 8))
        self.lbl_status.pack(side=tk.LEFT, padx=(15, 0))

        self.plots = TelemetryPlots(self)
        self.plots.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

    def set_active_lap(self, lap):
        self.selected_lap = lap
        time_str = f"{int(lap.lap_time_seconds // 60)}m{lap.lap_time_seconds % 60:06.3f}s"
        self.lbl_status.config(text=f"Volta #{lap.id} ({time_str} em {lap.track_name}) pronta para comparar.", fg="#00E5FF")

    def fetch_analysis_reference(self):
        if not self.selected_lap:
            messagebox.showinfo("Aviso", "Selecione primeiro uma volta no Histórico e clique em 'Carregar Volta'!")
            return

        lap = self.selected_lap
        year = int(self.combo_year.get())
        sess_code = self.combo_session.get().split()[0]
        driver = self.combo_driver.get()

        self.lbl_status.config(text=f"Baixando dados FIA: {driver} ({year} [{sess_code}]) em {lap.track_name}...", fg="#FFD000")

        def _fetch():
            res = fastf1_service.extract_reference_data(year, lap.track_name, sess_code, driver)
            self.after(0, lambda: self._apply_analysis_data(lap, res, year, sess_code, driver))

        threading.Thread(target=_fetch, daemon=True).start()

    def _apply_analysis_data(self, lap, res, year, sess_code, driver):
        df = LapRepository.get_lap_telemetry_df(lap.id)
        if df.empty:
            self.lbl_status.config(text="Erro: Telemetria da volta salva vazia.", fg="#EA0029")
            return

        d = df["Distance"].to_numpy()
        s = df["Speed"].to_numpy()
        t = df["Throttle"].to_numpy()
        b = df["Brake"].to_numpy()
        st = (df["Steer"] * 100.0).to_numpy()
        my_times = (df["TimeMs"] / 1000.0).to_numpy()

        if res.get("success"):
            pro_dist = res["distance"]
            pro_speed = res["speed"]
            pro_thr = res["throttle"]
            pro_time = res["time_sec"]
            pro_lap_str = res["lap_time_str"]
            pro_total_sec = res.get("lap_time_sec", pro_time[-1])

            deltas = calculate_cumulative_deltas(d, my_times, pro_dist, pro_time)
            title = f"ANÁLISE: {lap.track_name.upper()} | VOCÊ ({int(lap.lap_time_seconds // 60)}m{lap.lap_time_seconds % 60:06.3f}s) vs {driver} {year} [{sess_code}] ({pro_lap_str})"
            
            self.plots.set_reference_lap(pro_dist, pro_speed, pro_thr, max(pro_dist.max(), d.max()), title)
            self.plots.update_telemetry_data(d, s, t, b, st, deltas=deltas, track_len=max(pro_dist.max(), d.max()))

            diff = lap.lap_time_seconds - pro_total_sec
            diff_str = f"+{diff:.3f}s" if diff > 0 else f"{diff:.3f}s"
            self.lbl_status.config(text=f"Comparação pronta! Delta final: {diff_str} vs {driver} {year} [{sess_code}]", fg="#00E676")

            if self.on_compare_complete_cb:
                self.on_compare_complete_cb(df, d, s, res, diff)
        else:
            self.plots.clear_reference_lap(f"ANÁLISE: {lap.track_name.upper()} (Sem dados para {driver} {year})")
            self.plots.update_telemetry_data(d, s, t, b, st, deltas=None, track_len=d.max())
            self.lbl_status.config(text=f"Aviso: {res.get('error', 'Sem dados')} em {year} [{sess_code}].", fg="#FFD000")