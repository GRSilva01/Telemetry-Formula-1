# ================= APP WINDOW (Main Tkinter Application) =================
# Entry point da interface gráfica. Instancia os componentes e injeta
# as dependências (Service, Repository, UI Components) seguindo o padrão
# Dependency Injection. Este arquivo é o "main.py" enxuto solicitado.

import tkinter as tk
from tkinter import ttk, messagebox

# Importação dos módulos restructurados
from config import config
from database.connection import init_db, get_session
from database.lap_repository import LapRepository
from ingestion.udp_listener import UDPEmitter
from services.fastf1_service import fastf1_service
from services.telemetry_analyzer import calculate_delta, calculate_instant_delta, smooth_signal
from ui.components.delta_hud import DeltaHUD
from ui.components.sidebar import Sidebar
from ui.components.telemetry_plots import TelemetryPlots


class F1TelemetryApp:
    """Aplicação principal de telemetria F1 com arquitetura em camadas."""

    def __init__(self, root):
        self.root = root
        self.root.title("F1 Telemetry Analytics Suite")
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.root.configure(bg="#121212")

        # Inicializar banco de dados
        init_db()

        # Estado da aplicação
        self._lap_repository = LapRepository()
        self._is_recording = False
        self._lap_samples: List[Dict] = []
        self._current_lap_id = 0

        # Injeção de dependências dos componentes UI
        self._setup_ui()

        # Iniciar listener UDP
        self._udp_emitter = UDPEmitter(
            udp_port=config.UDP_PORT,
            udp_ip=config.UDP_IP
        )
        self._setup_udp_callbacks()

        # Bind de fechamento
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self) -> None:
        """Configura a interface do usuário."""
        # Container principal
        main_container = tk.Frame(self.root, bg="#121212")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Sidebar esquerda
        self._sidebar = Sidebar(
            main_container,
            on_lap_select=self._on_lap_selected,
            on_year_change=self._on_year_changed
        )
        self._sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Área central de gráficos
        self._plots = TelemetryPlots(main_container)
        self._plots.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # HUD de Delta (embaixo dos gráficos ou lateral)
        self._delta_hud = DeltaHUD(self._plots, ref_driver="VER")
        # Posiciona o HUD na parte inferior do canvas de plots
        self._delta_hud.pack(fill=tk.X, side=tk.BOTTOM)

    def _setup_udp_callbacks(self) -> None:
        """Configura os callbacks do listener UDP para atualizar a UI."""

        # Callback para dados de sessão (identificação de pista)
        self._udp_emitter.add_session_callback(self._on_session_data)

        # Callback para telemetria do carro (speed, throttle, etc.)
        self._udp_emitter.add_car_telemetry_callback(self._on_car_telemetry)

        # Callback para dados de volta (volta completada)
        self._udp_emitter.add_lap_data_callback(self._on_lap_data)

        # Callback para finalização de volta
        self._udp_emitter.add_lap_completed_callback(self._on_lap_completed)

        # Iniciar listener
        self._udp_emitter.start()

    # --- Callback handlers from UDP emitter ---

    def _on_session_data(self, data: Dict) -> None:
        """Atualiza UI quando dados de sessão chegam (pista identificada)."""
        track_name = data.get("track_name", "Desconhecido")
        track_length = data.get("track_length", 0)

        self._sidebar.update_track_status(track_name, track_length)
        self._plots.set_facecolor("#121212")

    def _on_car_telemetry(self, data: Dict) -> None:
        """Atualiza UI com telemetria do carro em tempo real."""
        speed = data.get("speed", 0)
        throttle = data.get("throttle", 0)
        brake = data.get("brake", 0)
        steer = data.get("steer", 0)

        self._sidebar.update_live_speed(int(speed) if speed else 0)

        # Atualizar gráficos com dados atuais
        # (Em uma implementação completa, manteríamos o estado atualizado)
        pass

    def _on_lap_data(self, telemetry_update: object) -> None:
        """Recebe dados de telemetria de uma volta em andamento."""
        # Aqui acumulamos amostras para possível salvamento
        # e atualizamos os gráficos em tempo real
        pass

    def _on_lap_completed(self, lap_event: object) -> None:
        """Chamado quando uma volta é completada/finish."""
        # Salva os dados no banco de dados
        try:
            lap_time_str = lap_event.lap_time_str
            # Extrai tempo em segundos do string "1:30.123"
            try:
                parts = lap_time_str.split(":")
                if len(parts) == 2:
                    lap_time_sec = float(parts[0]) * 60 + float(parts[1])
                else:
                    lap_time_sec = float(lap_time_str)
            except (ValueError, AttributeError):
                lap_time_sec = 0.0

            # Salva meta da volta no banco
            lap_meta = self._lap_repository.save_lap(
                track_name=lap_event.lap_time_str if hasattr(lap_event, 'lap_time_str') else "Unknown",
                lap_time_seconds=lap_time_sec,
                year_reference=2024  # Seria interessante extrair do estado
            )

            # Salva as amostras de telemetria
            if self._lap_samples:
                self._lap_repository.save_telemetry_samples(lap_meta.id, self._lap_samples)
                self._lap_samples = []  # Reset after save

            # Atualizar UI
            self._sidebar.set_mode_live()
            messagebox.showinfo("Volta Gravada", 
                              f"Volta {lap_event.lap_id} salva com sucesso!\n"
                              f"Tempo: {lap_time_str}\n"
                              f"Pontos de telemetria: {len(self._lap_samples)}")

        except Exception as e:
            print(f"[App] Erro ao salvar volta: {e}")
            messagebox.showerror("Erro", f"Falha ao salvar volta: {e}")

    def _on_lap_selected(self, filename: str) -> None:
        """Chamado quando o usuário seleciona uma volta na lista histórica."""
        try:
            # Carrega dados do CSV salva
            import pandas as pd
            from pathlib import Path

            file_path = f"laps/{filename}"
            if not Path(file_path).exists():
                messagebox.showerror("Erro", f"Arquivo não encontrado: {file_path}")
                return

            df = pd.read_csv(file_path)
            track_name = Path(file_path).stem.split("_")[0] if "_" in Path(file_path).stem else "Sao Paulo"

            # Atualizar interface com dados históricos
            self._plots.update_data(
                my_dist=df["Distance"].tolist() if "Distance" in df.columns else [],
                my_speed=df["Speed"].tolist() if "Speed" in df.columns else [],
                my_throttle=df["Throttle"].tolist() if "Throttle" in df.columns else [],
                my_brake=df["Brake"].tolist() if "Brake" in df.columns else [],
                my_steer=df["Steer"].tolist() if "Steer" in df.columns else [],
                pro_dist=[],  # Seria carregado do banco/ FastF1
                pro_speed=[],
                title=f"Análise: {filename} vs VER"
            )

            # Visualizar modo histórico
            self._sidebar.set_mode_historical()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar volta: {e}")
            print(f"[App] Erro ao carregar volta selecionada: {e}")

    def _on_year_changed(self, year: int) -> None:
        """Callback quando o usuário muda o ano da temporada."""
        # Recarrega dados de referência para o novo ano
        try:
            # O FastF1 Service buscará dados do ano selecionado
            data = fastf1_service.extract_reference_data(
                year=year,
                track_name=self._sidebar.get_track_name() if hasattr(self._sidebar, 'get_track_name') else "Monaco"
            )
            # Em uma implementação completa, atualizaria os dados da referência
            print(f"[App] AnoChanged: {year} - Dados de referência atualizados")
        except Exception as e:
            print(f"[App] Erro ao mudar ano: {e}")

    def _on_closing(self) -> None:
        """Chamado ao fechar a aplicação."""
        self._udp_emitter.stop()
        self.root.destroy()

    def run(self) -> None:
        """Inicia o loop principal da aplicação."""
        self.root.mainloop()


# Ponto de entrada enxuto
if __name__ == "__main__":
    root = tk.Tk()
    app = F1TelemetryApp(root)
    app.run()