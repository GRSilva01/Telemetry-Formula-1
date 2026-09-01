import tkinter as tk

class ShiftLightsPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#0E1424", padx=6, pady=4, highlightthickness=1, highlightbackground="#1B283E")
        self._setup_widgets()

    def _setup_widgets(self):
        # 1. Barra Superior de LEDs estilo Volante de F1 (15 LEDs)
        self.led_frame = tk.Frame(self, bg="#070A12", padx=4, pady=3)
        self.led_frame.pack(fill=tk.X, pady=(0, 4))

        self.leds = []
        # 5 Verdes, 5 Vermelhos, 5 Azuis
        self.led_colors = (
            ["#00E676"] * 5 + 
            ["#EA0029"] * 5 + 
            ["#00E5FF"] * 5
        )

        for i in range(15):
            led = tk.Canvas(self.led_frame, width=12, height=10, bg="#070A12", highlightthickness=0)
            led.pack(side=tk.LEFT, expand=True, padx=1)
            circle = led.create_oval(1, 1, 11, 9, fill="#182338", outline="")
            self.leds.append((led, circle))

        # 2. Display Central: Marcha Gigante + RPM + Score de Eficiência
        main_disp = tk.Frame(self, bg="#0E1424")
        main_disp.pack(fill=tk.X)

        # Marcha
        gear_box = tk.Frame(main_disp, bg="#070A12", padx=10, pady=2, highlightthickness=1, highlightbackground="#1B283E")
        gear_box.pack(side=tk.LEFT, padx=(0, 6))
        
        tk.Label(gear_box, text="GEAR", fg="#64748B", bg="#070A12", font=("Segoe UI", 6, "bold")).pack(anchor="w")
        self.lbl_gear = tk.Label(gear_box, text="N", fg="#FFD000", bg="#070A12", font=("Consolas", 22, "bold"))
        self.lbl_gear.pack(anchor="center")

        # RPM & Shift Rating
        info_box = tk.Frame(main_disp, bg="#0E1424")
        info_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        rpm_row = tk.Frame(info_box, bg="#0E1424")
        rpm_row.pack(fill=tk.X)
        tk.Label(rpm_row, text="ENGINE RPM:", fg="#8A99AD", bg="#0E1424", font=("Segoe UI", 7, "bold")).pack(side=tk.LEFT)
        self.lbl_rpm = tk.Label(rpm_row, text="0", fg="#FFFFFF", bg="#0E1424", font=("Consolas", 8, "bold"))
        self.lbl_rpm.pack(side=tk.RIGHT)

        eff_row = tk.Frame(info_box, bg="#0E1424")
        eff_row.pack(fill=tk.X, pady=(2, 0))
        tk.Label(eff_row, text="SHIFT EFFICIENCY:", fg="#8A99AD", bg="#0E1424", font=("Segoe UI", 7, "bold")).pack(side=tk.LEFT)
        self.lbl_efficiency = tk.Label(eff_row, text="100.0%", fg="#00E676", bg="#0E1424", font=("Consolas", 9, "bold"))
        self.lbl_efficiency.pack(side=tk.RIGHT)

        # Última Troca (Feedback)
        self.lbl_last_shift = tk.Label(self, text="LAST SHIFT: READY", fg="#64748B", bg="#0E1424", font=("Segoe UI", 7, "bold"))
        self.lbl_last_shift.pack(anchor="w", pady=(3, 0))

    def update_cockpit(self, gear: int, rpm: int, rev_pct: int, shift_eff: float, last_shift_status: str):
        # 1. Marcha
        g_str = "R" if gear == -1 else ("N" if gear == 0 else str(gear))
        self.lbl_gear.config(text=g_str)
        self.lbl_rpm.config(text=f"{rpm:,} RPM".replace(",", "."))

        # 2. Shift Lights LEDs
        # Converte a porcentagem (0-100) para a quantidade de LEDs acessos (0-15)
        active_leds = int((rev_pct / 100.0) * 15) if rev_pct > 0 else 0
        
        for i, (canvas, circle) in enumerate(self.leds):
            if i < active_leds:
                canvas.itemconfig(circle, fill=self.led_colors[i])
            else:
                canvas.itemconfig(circle, fill="#182338")

        # 3. Eficiência
        self.lbl_efficiency.config(text=f"{shift_eff:.1f}%")
        if shift_eff >= 85:
            self.lbl_efficiency.config(fg="#00E676")
        elif shift_eff >= 65:
            self.lbl_efficiency.config(fg="#FFD000")
        else:
            self.lbl_efficiency.config(fg="#EA0029")

        # 4. Status da última troca
        if last_shift_status == "OPTIMAL":
            self.lbl_last_shift.config(text="LAST SHIFT: OPTIMAL (POWER BAND)", fg="#00E676")
        elif last_shift_status == "EARLY":
            self.lbl_last_shift.config(text="LAST SHIFT: SHORT-SHIFT (<90%)", fg="#FFD000")
        elif last_shift_status == "LATE":
            self.lbl_last_shift.config(text="LAST SHIFT: OVER-REV / LIMITER", fg="#EA0029")
        else:
            self.lbl_last_shift.config(text="LAST SHIFT: --", fg="#64748B")

    def reset_panel(self):
        for canvas, circle in self.leds:
            canvas.itemconfig(circle, fill="#182338")
        self.lbl_gear.config(text="N")
        self.lbl_rpm.config(text="0 RPM")
        self.lbl_efficiency.config(text="100.0%", fg="#00E676")
        self.lbl_last_shift.config(text="LAST SHIFT: READY", fg="#64748B")