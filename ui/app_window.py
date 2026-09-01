import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np

from config import UDP_IP, UDP_PORT
from database.lap_repository import LapRepository
from ingestion.udp_listener import UDPEmitter
from services.live_telemetry_service import LiveTelemetryService
from services.telemetry_analyzer import calculate_cumulative_deltas, calculate_trail_braking_score
from ui.components.telemetry_plots import TelemetryPlots
from ui.components.dynamics_plots import DynamicsPlots
from ui.components.sidebar_panel import SidebarPanel
from ui.tabs.analysis_tab import AnalysisTab


class F1TelemetryApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ORACLE RED BULL RACING — Telemetry Performance Suite")
        self.root.geometry("1550x940")
        self.root.configure(bg="#070A12")

        self.is_inspecting_saved_lap = False

        # 1. Serviço de Telemetria Live
        self.live_service = LiveTelemetryService(on_lap_completed_callback=self._on_lap_saved_event)

        # 2. Setup de Estilos e Layout
        self._setup_styles()
        self._setup_layout()
        self._refresh_history_list()

        # 3. Listener UDP
        self._udp = UDPEmitter(udp_ip=UDP_IP, udp_port=UDP_PORT)
        self._udp.add_session_callback(self._on_session_data)
        self._udp.add_car_telemetry_callback(self.live_service.handle_car_telemetry)
        self._udp.add_lap_data_callback(self.live_service.handle_lap)
        self._udp.add_motion_callback(self.live_service.handle_motion)
        self._udp.start()

        # 4. Render Loop
        self._ui_render_loop()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#070A12", borderwidth=0)
        style.configure("TNotebook.Tab", background="#0E1424", foreground="#8A99AD", padding=[16, 7], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#1B283E")], foreground=[("selected", "#FFD000")])

    def _setup_layout(self):
        # Sidebar
        self.sidebar = SidebarPanel(self.root, on_load_lap_cb=self._load_saved_lap_to_view, on_refresh_laps_cb=self._refresh_history_list)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Notebook Central
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Aba 1: Live / PB
        self.tab_live = tk.Frame(self.notebook, bg="#070A12")
        self._plots_live = TelemetryPlots(self.tab_live)
        self._plots_live.pack(fill=tk.BOTH, expand=True)
        self.notebook.add(self.tab_live, text=" 🏎️ Telemetria & Delta vs Recorde (PB) ")

        # Aba 2: Comparar com Piloto FIA
        self.tab_analysis = AnalysisTab(self.notebook, on_compare_complete_cb=self._on_fia_compare_completed)
        self.notebook.add(self.tab_analysis, text=" 📊 Comparar com Piloto FIA ")

        # Aba 3: Dinâmica Veicular & Track Map
        self.tab_dynamics = tk.Frame(self.notebook, bg="#070A12")
        self._dynamics = DynamicsPlots(self.tab_dynamics)
        self._dynamics.pack(fill=tk.BOTH, expand=True)
        self.notebook.add(self.tab_dynamics, text=" 📍 Dinâmica Veicular & Track Map ")

    def _load_personal_best_for_track(self, track_name: str):
        best_lap = LapRepository.get_best_lap(track_name)
        if best_lap:
            df = LapRepository.get_lap_telemetry_df(best_lap.id)
            if not df.empty:
                dist = df["Distance"].to_numpy()
                time_sec = (df["TimeMs"] / 1000.0).to_numpy()
                speed = df["Speed"].to_numpy()
                thr = df["Throttle"].to_numpy()

                self.live_service.load_pb_data(dist, time_sec, speed, thr)
                time_str = f"{int(best_lap.lap_time_seconds // 60)}m{int(best_lap.lap_time_seconds % 60):02d}s{int((best_lap.lap_time_seconds % 1)*1000):03d}"
                self.sidebar.lbl_pb.config(text=f"Seu Recorde: #{best_lap.id} ({time_str})")
                if not self.is_inspecting_saved_lap:
                    self._plots_live.set_reference_lap(dist, speed, thr, max(dist.max(), self.live_service.track_length), f"LIVE: {track_name.upper()} | REFERÊNCIA: SEU RECORDE ({time_str})")
                return

        self.live_service.load_pb_data(np.array([]), np.array([]), np.array([]), np.array([]))
        self.sidebar.lbl_pb.config(text="Seu Recorde: Nenhum")
        if not self.is_inspecting_saved_lap:
            self._plots_live.clear_reference_lap(f"LIVE: {track_name.upper()} (Sem recorde salvo ainda)")

    def _on_session_data(self, data):
        self.live_service.handle_session(data)
        track_name = data.get("track_name")
        if track_name and track_name != "Desconhecido":
            self.root.after(0, lambda: self._load_personal_best_for_track(track_name))

    def _on_lap_saved_event(self, track_name):
        self.root.after(0, self._refresh_history_list)
        self.root.after(0, lambda: self._load_personal_best_for_track(track_name))

    def _ui_render_loop(self):
        srv = self.live_service
        with srv.lock:
            self.sidebar.lbl_track.config(text=f"Pista: {srv.current_track}")
            
            # Atualiza Badge de Pit Status
            if srv.is_in_pits:
                if srv.pit_status_str == "IN GARAGE":
                    self.sidebar.lbl_pit_status.config(text="● IN GARAGE", fg="#94A3B8")
                else:
                    self.sidebar.lbl_pit_status.config(text=f"● {srv.pit_status_str}", fg="#FFD000")
            else:
                self.sidebar.lbl_pit_status.config(text="● ON TRACK", fg="#00E676")

            # Atualiza shift lights e indicadores instantâneos
            total_shifts = len(srv.shift_events)
            optimal_shifts = srv.shift_events.count("OPTIMAL")
            shift_eff = (optimal_shifts / total_shifts * 100.0) if total_shifts > 0 else 100.0

            self.sidebar.shift_panel.update_cockpit(
                gear=srv.latest_car["gear"],
                rpm=srv.latest_car["engine_rpm"],
                rev_pct=srv.latest_car["rev_lights_percent"],
                shift_eff=shift_eff,
                last_shift_status=srv.last_shift_status
            )

            # Só renderiza telemetria live se você não estiver inspecionando uma volta salva
            if not self.is_inspecting_saved_lap:
                if len(srv.live_time_sec) > 0:
                    cur_s = srv.live_time_sec[-1]
                    self.sidebar.lbl_lap_time.config(text=f"Volta Atual: {int(cur_s//60):02d}:{cur_s%60:06.3f}")

                if srv.needs_ui_reset:
                    self._plots_live.reset_live_lines()
                    self._dynamics.reset_dynamics()
                    self.sidebar.tyres_panel.reset_panel()
                    self.sidebar.shift_panel.reset_panel()
                    srv.needs_ui_reset = False

                n_samples = len(srv.live_dist)
                if n_samples > 2:
                    d = np.array(srv.live_dist)
                    s = np.array(srv.live_speed)
                    t = np.array(srv.live_throttle)
                    b = np.array(srv.live_brake)
                    st = np.array(srv.live_steer)
                    deltas_arr = np.array(srv.live_deltas)

                    self._plots_live.update_telemetry_data(d, s, t, b, st, deltas=deltas_arr, track_len=srv.track_length)

                    if self.notebook.index(self.notebook.select()) == 2:
                        self._dynamics.render_map_and_diagnostics(
                            x_coords=srv.live_pos_x,
                            z_coords=srv.live_pos_z,
                            my_speed=s,
                            my_gear=np.array(srv.live_gear) if len(srv.live_gear) == len(s) else np.zeros_like(s),
                            my_dist=d,
                            pro_dist=srv.pb_dist if len(srv.pb_dist) > 0 else None,
                            pro_speed=srv.pb_speed if len(srv.pb_speed) > 0 else None,
                            pro_gear=None,
                            g_lat=srv.live_g_lat,
                            g_lon=srv.live_g_lon
                        )

                    tb_score = calculate_trail_braking_score(b, st)
                    self.sidebar.tyres_panel.update_tyres(srv.latest_car["tyres_surf_temp"], tb_score)

                    if len(deltas_arr) > 0 and len(srv.pb_dist) > 0:
                        self.sidebar.update_delta_widget(deltas_arr[-1])

        self.root.after(33, self._ui_render_loop)

    def _refresh_history_list(self):
        self.sidebar.lap_listbox.delete(0, tk.END)
        self.saved_laps = LapRepository.get_all_laps()
        for lap in self.saved_laps:
            time_str = f"{int(lap.lap_time_seconds // 60)}m{int(lap.lap_time_seconds % 60):02d}s{int((lap.lap_time_seconds % 1)*1000):03d}"
            date_str = lap.date_recorded.strftime("%d/%m %H:%M")
            self.sidebar.lap_listbox.insert(tk.END, f"#{lap.id} | {lap.track_name} | {time_str} | {date_str}")

    def _load_saved_lap_to_view(self):
        selection = self.sidebar.lap_listbox.curselection()
        if not selection:
            messagebox.showinfo("Aviso", "Selecione uma volta salva na lista!")
            return

        selected_lap = self.saved_laps[selection[0]]
        self.is_inspecting_saved_lap = True
        self.tab_analysis.set_active_lap(selected_lap)

        if self.live_service.current_track != selected_lap.track_name:
            self.live_service.current_track = selected_lap.track_name
            self._load_personal_best_for_track(selected_lap.track_name)

        df = LapRepository.get_lap_telemetry_df(selected_lap.id)
        if df.empty:
            messagebox.showwarning("Aviso", "A telemetria desta volta está vazia.")
            return

        d = df["Distance"].to_numpy()
        s = df["Speed"].to_numpy()
        t = df["Throttle"].to_numpy()
        b = df["Brake"].to_numpy()
        st = (df["Steer"] * 100.0).to_numpy()
        my_times = (df["TimeMs"] / 1000.0).to_numpy()
        my_gears = df["Gear"].to_numpy() if "Gear" in df else np.zeros_like(d)

        srv = self.live_service
        if len(srv.pb_dist) > 0 and len(srv.pb_time_sec) > 0:
            deltas = calculate_cumulative_deltas(d, my_times, srv.pb_dist, srv.pb_time_sec)
        else:
            deltas = np.zeros_like(d)

        time_str = f"{int(selected_lap.lap_time_seconds // 60)}m{selected_lap.lap_time_seconds % 60:06.3f}s"
        self.sidebar.lbl_lap_time.config(text=f"Volta #{selected_lap.id} ({time_str})")

        # Plota na Aba 1
        self._plots_live.set_reference_lap(
            srv.pb_dist, srv.pb_speed, srv.pb_throttle,
            max(d.max(), srv.track_length),
            f"HISTÓRICO: VOLTA #{selected_lap.id} ({time_str}) vs SEU RECORDE"
        )
        self._plots_live.update_telemetry_data(d, s, t, b, st, deltas=deltas, track_len=max(d.max(), srv.track_length))

        # Plota na Aba 3
        self._dynamics.render_map_and_diagnostics(
            x_coords=df["WorldPosX"].to_list(),
            z_coords=df["WorldPosZ"].to_list(),
            my_speed=s,
            my_gear=my_gears,
            my_dist=d,
            pro_dist=srv.pb_dist if len(srv.pb_dist) > 0 else None,
            pro_speed=srv.pb_speed if len(srv.pb_speed) > 0 else None,
            pro_gear=None,
            g_lat=df["GForceLat"].to_list(),
            g_lon=df["GForceLon"].to_list()
        )

        if len(deltas) > 0 and len(srv.pb_dist) > 0:
            self.sidebar.update_delta_widget(deltas[-1])

    def _on_fia_compare_completed(self, df, d, s, res, diff):
        my_gears = df["Gear"].to_numpy() if "Gear" in df else np.zeros_like(d)
        self._dynamics.render_map_and_diagnostics(
            x_coords=df["WorldPosX"].to_list(),
            z_coords=df["WorldPosZ"].to_list(),
            my_speed=s,
            my_gear=my_gears,
            my_dist=d,
            pro_dist=res["distance"],
            pro_speed=res["speed"],
            pro_gear=res.get("gear", np.zeros_like(res["distance"])),
            g_lat=df["GForceLat"].to_list(),
            g_lon=df["GForceLon"].to_list()
        )
        self.sidebar.update_delta_widget(diff)