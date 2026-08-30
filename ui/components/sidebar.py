# ================= SIDEBAR COMPONENT =================
# Barra lateral isolada com seletores de ano/pista, histórico de voltas
# e modo de exibição. Herda de tk.Frame para composição fácil.

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Optional


class Sidebar(tk.Frame):
    """Barra lateral esquerda da aplicação com controles e histórico."""

    def __init__(self, parent, on_lap_select: Callable = None,
                 on_year_change: Callable = None, **kwargs):
        super().__init__(parent, width=320, bg="#1E1E1E", padx=15, pady=15, **kwargs)
        self.on_lap_select = on_lap_select
        self.on_year_change = on_year_change
        self._mode = "LIVE"
        self._selected_year = 2024

        self._setup_layout()

    def _setup_layout(self) -> None:
        """Configura todos os elementos da sidebar."""
        # Título
        tk.Label(self, text="F1 TELEMETRY", fg="#00FFCC", bg="#1E1E1E",
                 font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 10))

        # Subtitle
        tk.Label(self, text="Real-Time Performance Suite", fg="#888888", bg="#1E1E1E",
                 font=("Arial", 9)).pack(anchor="w", pady=(0, 10))

        # --- SEÇÃO TEMPORADA ---
        self._setup_year_selector()

        # --- SEÇÃO DELTA ---
        self._setup_delta_section()

        # --- SEÇÃO STATUS ---
        self._setup_status_section()

        # --- BOTÃO MODO ---
        self._setup_mode_button()

        # --- HISTÓRICO DE VOLTAS ---
        self._setup_lap_history()

    def _setup_year_selector(self) -> None:
        """Seletor de ano da temporada de referência."""
        cfg_frame = tk.LabelFrame(self, text=" Temporada de Referência ",
                                  fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 10, "bold"),
                                  padx=10, pady=8)
        cfg_frame.pack(fill=tk.X, pady=5)

        tk.Label(cfg_frame, text="Ano da F1 Real:", fg="#CCCCCC", bg="#1E1E1E",
                 font=("Arial", 9)).pack(anchor="w")

        self.combo_year = ttk.Combobox(cfg_frame, values=["2026", "2025", "2024",
                                                          "2023", "2022", "2021"],
                                      state="readonly", font=("Arial", 9))
        self.combo_year.set("2024")
        self.combo_year.pack(fill=tk.X, pady=(2, 4))
        self.combo_year.bind("<<ComboboxSelected>>", self._on_year_changed)

    def _setup_delta_section(self) -> None:
        """Seção de delta ao vivo."""
        delta_frame = tk.LabelFrame(self, text=" LIVE DELTA vs REF ", fg="#FFFFFF",
                                     bg="#1E1E1E", font=("Arial", 10, "bold"),
                                     padx=10, pady=8)
        delta_frame.pack(fill=tk.X, pady=5)

        self.lbl_delta = tk.Label(delta_frame, text="+0.000s", fg="#FFFFFF",
                                   bg="#262626", font=("Consolas", 24, "bold"), pady=6)
        self.lbl_delta.pack(fill=tk.X)

    def _setup_status_section(self) -> None:
        """Seção de status da sessão."""
        status_frame = tk.LabelFrame(self, text=" Status da Sessão ", fg="#FFFFFF",
                                      bg="#1E1E1E", font=("Arial", 10, "bold"),
                                      padx=10, pady=8)
        status_frame.pack(fill=tk.X, pady=6)

        self.lbl_track = tk.Label(status_frame, text="Pista: Aguardando...",
                                   fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 9))
        self.lbl_track.pack(anchor="w", pady=2)

        self.lbl_pro = tk.Label(status_frame, text="Ref: VER (--:--.---)",
                                 fg="#005AFF", bg="#1E1E1E", font=("Arial", 9, "bold"))
        self.lbl_pro.pack(anchor="w", pady=2)

        self.lbl_live_speed = tk.Label(status_frame, text="Velocidade: 0 km/h",
                                        fg="#00FFCC", bg="#1E1E1E", font=("Arial", 9))
        self.lbl_live_speed.pack(anchor="w", pady=2)

    def _setup_mode_button(self) -> None:
        """Botão de alternar modo Live/Histórico."""
        self.btn_live = tk.Button(self, text="● MODO AO VIVO", bg="#00FFCC", fg="#000000",
                                   font=("Arial", 10, "bold"), relief=tk.FLAT,
                                   command=self._switch_to_live, pady=6)
        self.btn_live.pack(fill=tk.X, pady=6)

    def _setup_lap_history(self) -> None:
        """Histórico de voltas salvas."""
        history_frame = tk.LabelFrame(self, text=" Voltas Salvas (Histórico ) ",
                                      fg="#FFFFFF", bg="#1E1E1E", font=("Arial", 10, "bold"),
                                      padx=5, pady=5)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.lap_listbox = tk.Listbox(history_frame, bg="#121212", fg="#FFFFFF",
                                      font=("Consolas", 8),
                                      selectbackground="#005AFF",
                                      selectforeground="#FFFFFF", borderwidth=0)
        self.lap_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(history_frame, command=self.lap_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lap_listbox.config(yscrollcommand=scrollbar.set)

        # Botões de ação
        btn_frame = tk.Frame(self, bg="#1E1E1E")
        btn_frame.pack(fill=tk.X, pady=6)

        tk.Button(btn_frame, text="Analisar Volta", bg="#333333", fg="#FFFFFF", font=("Arial", 9),
                   relief=tk.FLAT, command=self._on_analyze_click, pady=4).pack(
                       side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        tk.Button(btn_frame, text="Atualizar", bg="#252525", fg="#AAAAAA", font=("Arial", 9),
                   relief=tk.FLAT, command=self._on_refresh_click, pady=4).pack(
                       side=tk.RIGHT, padx=(4, 0))

    # --- Event handlers (to be connected by app) ---

    def _on_year_changed(self, event) -> None:
        """Dispara callback de mudança de ano."""
        if self.on_year_change:
            try:
                new_year = int(self.combo_year.get())
                self._selected_year = new_year
                self.on_year_change(new_year)
            except ValueError:
                pass

    def _switch_to_live(self) -> None:
        """Alterna para o modo ao vivo."""
        self._mode = "LIVE"
        self.btn_live.config(bg="#00FFCC", text="● MODO AO VIVO")
        if hasattr(self, '_on_mode_change'):
            self._on_mode_change("LIVE")

    def _on_analyze_click(self) -> None:
        """Dispara ao clicar em 'Analisar Volta'."""
        selection = self.lap_listbox.curselection()
        if not selection:
            messagebox.showinfo("Aviso", "Selecione uma volta salva na lista!")
            return
        if self.on_lap_select:
            # Pega o nome do arquivo selecionado
            filename = self.lap_listbox.get(selection[0])
            self.on_lap_select(filename)

    def _on_refresh_click(self) -> None:
        """Dispara ao clicar em 'Atualizar'."""
        if self.on_year_change:
            self.on_year_change(self._selected_year)

    def set_mode_live(self) -> None:
        """Define visual do modo live."""
        self._mode = "LIVE"
        self.btn_live.config(bg="#00FFCC", text="● MODO AO VIVO")

    def set_mode_historical(self) -> None:
        """Define visual do modo histórico."""
        self._mode = "HISTORICAL"
        self.btn_live.config(bg="#333333", text="Visualizando Histórico")

    def update_track_status(self, track_name: str, track_length: float = 0) -> None:
        """Atualiza o status da pista."""
        self.lbl_track.config(text=f"Pista: {track_name}")

    def update_ref_status(self, driver: str, lap_time: str = "--:--.---") -> None:
        """Atualiza o status da referência."""
        self.lbl_pro.config(text=f"Ref: {driver} ({lap_time})")

    def update_live_speed(self, speed: int) -> None:
        """Atualiza a velocidade exibida."""
        self.lbl_live_speed.config(text=f"Velocidade: {speed} km/h")

    def get_selected_year(self) -> int:
        """Retorna o ano selecionado."""
        return int(self.combo_year.get())

    def get_lap_files(self) -> List[str]:
        """Retorna lista de arquivos de voltas salvas."""
        return [self.lap_listbox.get(i) for i in range(self.lap_listbox.size())]


# Instância global
sidebar_instance = None