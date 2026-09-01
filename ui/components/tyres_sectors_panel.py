import tkinter as tk
from typing import List, Dict, Any

class TyresSectorsPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#0E1424", padx=10, pady=8)
        self._setup_widgets()

    def _setup_widgets(self):
        # 1. Pneus e Dinâmica
        tyres_frame = tk.LabelFrame(self, text=" TYRE TEMPERATURES (°C) ", fg="#FFD000", bg="#0E1424", font=("Segoe UI", 8, "bold"), padx=6, pady=4)
        tyres_frame.pack(fill=tk.X, pady=(0, 6))

        self.tyre_labels = {}
        grid_pos = [("FL", 0, 0), ("FR", 0, 1), ("RL", 1, 0), ("RR", 1, 1)]
        names = {"FL": "FRONT L", "FR": "FRONT R", "RL": "REAR L", "RR": "REAR R"}

        for code, r, c in grid_pos:
            box = tk.Frame(tyres_frame, bg="#070A12", padx=4, pady=3, highlightthickness=1, highlightbackground="#1B283E")
            box.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
            tyres_frame.grid_columnconfigure(c, weight=1)

            lbl_name = tk.Label(box, text=names[code], fg="#64748B", bg="#070A12", font=("Segoe UI", 7, "bold"))
            lbl_name.pack(anchor="w")

            lbl_val = tk.Label(box, text="-- °C", fg="#00E5FF", bg="#070A12", font=("Consolas", 11, "bold"))
            lbl_val.pack(anchor="center")
            self.tyre_labels[code] = lbl_val

        # Trail Braking Score
        tb_frame = tk.Frame(tyres_frame, bg="#0E1424", pady=3)
        tb_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(3, 0))

        tk.Label(tb_frame, text="TRAIL BRAKE INDEX:", fg="#8A99AD", bg="#0E1424", font=("Segoe UI", 7, "bold")).pack(side=tk.LEFT)
        self.lbl_trail_score = tk.Label(tb_frame, text="0.0%", fg="#FFD000", bg="#0E1424", font=("Consolas", 10, "bold"))
        self.lbl_trail_score.pack(side=tk.RIGHT)

        # 2. Mini-Setores
        sec_frame = tk.LabelFrame(self, text=" MINI-SECTORS vs VER ", fg="#FFD000", bg="#0E1424", font=("Segoe UI", 8, "bold"), padx=5, pady=5)
        sec_frame.pack(fill=tk.BOTH, expand=True)

        self.sector_boxes = []
        rows, cols = 4, 5
        for i in range(20):
            r = i // cols
            c = i % cols
            lbl_s = tk.Label(sec_frame, text=f"S{i+1}", fg="#475569", bg="#070A12", font=("Consolas", 7, "bold"), width=4, height=1)
            lbl_s.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
            sec_frame.grid_columnconfigure(c, weight=1)
            sec_frame.grid_rowconfigure(r, weight=1)
            self.sector_boxes.append(lbl_s)

    def update_tyres(self, surf_temps: List[int], trail_score: float):
        if len(surf_temps) >= 4:
            self.tyre_labels["RL"].config(text=f"{surf_temps[0]}°C", fg=self._get_temp_color(surf_temps[0]))
            self.tyre_labels["RR"].config(text=f"{surf_temps[1]}°C", fg=self._get_temp_color(surf_temps[1]))
            self.tyre_labels["FL"].config(text=f"{surf_temps[2]}°C", fg=self._get_temp_color(surf_temps[2]))
            self.tyre_labels["FR"].config(text=f"{surf_temps[3]}°C", fg=self._get_temp_color(surf_temps[3]))

        self.lbl_trail_score.config(text=f"{trail_score:.1f}%")

    def _get_temp_color(self, temp: int) -> str:
        if temp < 85:
            return "#00E5FF" # Frio (Cyan)
        elif 85 <= temp <= 105:
            return "#00E676" # Janela ideal (Verde F1)
        elif 105 < temp <= 115:
            return "#FFD000" # Amarelo RBR
        else:
            return "#EA0029" # Superaquecido (Bull Red)

    def update_sectors(self, sectors_status: List[Dict[str, Any]]):
        for i, s in enumerate(sectors_status):
            if i < len(self.sector_boxes):
                box = self.sector_boxes[i]
                status = s.get("status", "EQUAL")
                delta_val = s.get("delta", 0.0)

                if status == "GREEN":
                    box.config(bg="#004D25", fg="#00E676", text=f"{delta_val:+.2f}")
                elif status == "RED":
                    box.config(bg="#4D000E", fg="#EA0029", text=f"{delta_val:+.2f}")
                elif status == "YELLOW":
                    box.config(bg="#3D3200", fg="#FFD000", text="~0.00")
                else:
                    box.config(bg="#070A12", fg="#334155", text=f"S{i+1}")

    def reset_panel(self):
        for box in self.sector_boxes:
            box.config(bg="#070A12", fg="#334155")
        self.lbl_trail_score.config(text="0.0%")