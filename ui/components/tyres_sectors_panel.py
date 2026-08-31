import tkinter as tk
from typing import List, Dict, Any

class TyresSectorsPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#1E1E1E", padx=10, pady=8)
        self._setup_widgets()

    def _setup_widgets(self):
        # 1. Painel de Pneus e Travamento
        tyres_frame = tk.LabelFrame(self, text=" Dinâmica de Pneus & Freios ", fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 9, "bold"), padx=8, pady=6)
        tyres_frame.pack(fill=tk.X, pady=(0, 6))

        # Grid 2x2 para os pneus
        self.tyre_labels = {}
        grid_pos = [("FL", 0, 0), ("FR", 0, 1), ("RL", 1, 0), ("RR", 1, 1)]
        names = {"FL": "Diant. Esq", "FR": "Diant. Dir", "RL": "Tras. Esq", "RR": "Tras. Dir"}

        for code, r, c in grid_pos:
            box = tk.Frame(tyres_frame, bg="#262626", padx=6, pady=4, relief=tk.RIDGE, bd=1)
            box.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
            tyres_frame.grid_columnconfigure(c, weight=1)

            lbl_name = tk.Label(box, text=names[code], fg="#888888", bg="#262626", font=("Arial", 8))
            lbl_name.pack(anchor="w")

            lbl_val = tk.Label(box, text="-- °C", fg="#00FFCC", bg="#262626", font=("Consolas", 11, "bold"))
            lbl_val.pack(anchor="center")
            self.tyre_labels[code] = lbl_val

        # Trail Braking Score
        tb_frame = tk.Frame(tyres_frame, bg="#1E1E1E", pady=4)
        tb_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        tk.Label(tb_frame, text="Trail Braking Score:", fg="#CCCCCC", bg="#1E1E1E", font=("Arial", 9)).pack(side=tk.LEFT)
        self.lbl_trail_score = tk.Label(tb_frame, text="0.0%", fg="#FFCC00", bg="#1E1E1E", font=("Consolas", 10, "bold"))
        self.lbl_trail_score.pack(side=tk.RIGHT)

        # 2. Painel de Mini-Setores (20 Micro-Sectors)
        sec_frame = tk.LabelFrame(self, text=" Mini-Setores (20 Micro-Trechos vs VER) ", fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 9, "bold"), padx=6, pady=6)
        sec_frame.pack(fill=tk.BOTH, expand=True)

        # Grid de botões/indicadores de setores
        self.sector_boxes = []
        rows, cols = 4, 5
        for i in range(20):
            r = i // cols
            c = i % cols
            lbl_s = tk.Label(sec_frame, text=f"S{i+1}", fg="#666666", bg="#121212", font=("Consolas", 8, "bold"), width=4, height=1)
            lbl_s.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
            sec_frame.grid_columnconfigure(c, weight=1)
            sec_frame.grid_rowconfigure(r, weight=1)
            self.sector_boxes.append(lbl_s)

    def update_tyres(self, surf_temps: List[int], trail_score: float):
        # Mapeamento do jogo: [RL, RR, FL, FR]
        if len(surf_temps) >= 4:
            self.tyre_labels["RL"].config(text=f"{surf_temps[0]}°C", fg=self._get_temp_color(surf_temps[0]))
            self.tyre_labels["RR"].config(text=f"{surf_temps[1]}°C", fg=self._get_temp_color(surf_temps[1]))
            self.tyre_labels["FL"].config(text=f"{surf_temps[2]}°C", fg=self._get_temp_color(surf_temps[2]))
            self.tyre_labels["FR"].config(text=f"{surf_temps[3]}°C", fg=self._get_temp_color(surf_temps[3]))

        self.lbl_trail_score.config(text=f"{trail_score:.1f}%")

    def _get_temp_color(self, temp: int) -> str:
        if temp < 85:
            return "#00CCFF" # Frio (Azul)
        elif 85 <= temp <= 105:
            return "#00FF66" # Janela ideal (Verde)
        elif 105 < temp <= 115:
            return "#FFCC00" # Aquecido (Amarelo)
        else:
            return "#FF3333" # Superaquecido (Vermelho)

    def update_sectors(self, sectors_status: List[Dict[str, Any]]):
        for i, s in enumerate(sectors_status):
            if i < len(self.sector_boxes):
                box = self.sector_boxes[i]
                status = s.get("status", "EQUAL")
                delta_val = s.get("delta", 0.0)

                if status == "GREEN":
                    box.config(bg="#006622", fg="#FFFFFF", text=f"{delta_val:+.2f}")
                elif status == "RED":
                    box.config(bg="#88001b", fg="#FFFFFF", text=f"{delta_val:+.2f}")
                elif status == "YELLOW":
                    box.config(bg="#665500", fg="#FFFFFF", text="~0.00")
                else:
                    box.config(bg="#121212", fg="#444444", text=f"S{i+1}")

    def reset_panel(self):
        for box in self.sector_boxes:
            box.config(bg="#121212", fg="#444444")
        self.lbl_trail_score.config(text="0.0%")