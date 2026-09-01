import tkinter as tk
from ui.components.shift_lights_panel import ShiftLightsPanel
from ui.components.tyres_sectors_panel import TyresSectorsPanel

class SidebarPanel(tk.Frame):
    def __init__(self, parent, on_load_lap_cb, on_refresh_laps_cb):
        super().__init__(parent, width=330, bg="#0E1424", padx=12, pady=10, highlightthickness=1, highlightbackground="#1B283E")
        self.on_load_lap_cb = on_load_lap_cb
        self.on_refresh_laps_cb = on_refresh_laps_cb
        self._setup_widgets()

    def _setup_widgets(self):
        # 1. Cabeçalho
        tk.Label(self, text="ORACLE RED BULL", fg="#FFD000", bg="#0E1424", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(self, text="Telemetry & Pit-Wall Engineering", fg="#00E5FF", bg="#0E1424", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 4))

        # 2. Shift Lights & Marcha
        self.shift_panel = ShiftLightsPanel(self)
        self.shift_panel.pack(fill=tk.X, pady=3)

        # 3. Delta HUD vs Recorde (PB)
        delta_frame = tk.LabelFrame(self, text=" DELTA vs SEU RECORDE (PB) ", fg="#FFD000", bg="#0E1424", font=("Segoe UI", 8, "bold"), padx=8, pady=3)
        delta_frame.pack(fill=tk.X, pady=3)

        self.lbl_delta = tk.Label(delta_frame, text="+0.000s", fg="#FFFFFF", bg="#070A12", font=("Consolas", 18, "bold"), pady=3)
        self.lbl_delta.pack(fill=tk.X)

        # 4. Pneus & Mini-Setores
        self.tyres_panel = TyresSectorsPanel(self)
        self.tyres_panel.pack(fill=tk.X, pady=3)

        # 5. Status da Sessão & Pit Status
        status_frame = tk.LabelFrame(self, text=" STATUS DA SESSÃO ", fg="#FFD000", bg="#0E1424", font=("Segoe UI", 8, "bold"), padx=8, pady=4)
        status_frame.pack(fill=tk.X, pady=3)

        self.lbl_track = tk.Label(status_frame, text="Pista: Aguardando...", fg="#E2E8F0", bg="#0E1424", font=("Segoe UI", 8))
        self.lbl_track.pack(anchor="w")

        self.lbl_pit_status = tk.Label(status_frame, text="● ON TRACK", fg="#00E676", bg="#0E1424", font=("Segoe UI", 8, "bold"))
        self.lbl_pit_status.pack(anchor="w")

        self.lbl_pb = tk.Label(status_frame, text="Seu Recorde: Nenhum", fg="#00E5FF", bg="#0E1424", font=("Consolas", 8, "bold"))
        self.lbl_pb.pack(anchor="w")

        self.lbl_lap_time = tk.Label(status_frame, text="Modo: Ao Vivo", fg="#FFFFFF", bg="#0E1424", font=("Consolas", 8))
        self.lbl_lap_time.pack(anchor="w")

        # 6. Histórico de Voltas
        history_frame = tk.LabelFrame(self, text=" HISTÓRICO DE VOLTAS ", fg="#FFD000", bg="#0E1424", font=("Segoe UI", 8, "bold"), padx=4, pady=4)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=3)

        self.lap_listbox = tk.Listbox(
            history_frame,
            bg="#070A12",
            fg="#E2E8F0",
            font=("Consolas", 8),
            selectbackground="#FFD000",
            selectforeground="#070A12",
            borderwidth=0
        )
        self.lap_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(history_frame, command=self.lap_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lap_listbox.config(yscrollcommand=scrollbar.set)

        btn_h = tk.Frame(self, bg="#0E1424")
        btn_h.pack(fill=tk.X, pady=3)
        tk.Button(btn_h, text="Carregar Volta", bg="#FFD000", fg="#070A12", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, command=self.on_load_lap_cb).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(btn_h, text="Atualizar", bg="#131C2E", fg="#8A99AD", font=("Segoe UI", 8), relief=tk.FLAT, command=self.on_refresh_laps_cb).pack(side=tk.RIGHT, padx=2)

    def update_delta_widget(self, delta_val: float):
        if delta_val < 0:
            self.lbl_delta.config(text=f"{delta_val:+.3f}s", fg="#00E676", bg="#003314")
        else:
            self.lbl_delta.config(text=f"{delta_val:+.3f}s", fg="#EA0029", bg="#330008")