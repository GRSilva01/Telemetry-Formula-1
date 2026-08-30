# ================= MAIN ENTRY POINT (Injeção de Dependência) =================
# Este arquivo serve como entry point limpo da aplicação.
# Instancia as dependências necessárias e inicia o loop da aplicação.
# Responsabilidade única: orquestrar a criação dos componentes.

import tkinter as tk
from ui.app_window import F1TelemetryApp


def main():
    """Ponto de entrada da aplicação."""
    root = tk.Tk()
    app = F1TelemetryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()