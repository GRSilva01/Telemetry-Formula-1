import tkinter as tk
from database.connection import init_db
from ui.app_window import F1TelemetryApp

def main():
    init_db()  # Cria o arquivo telemetry.db e as tabelas caso não existam
    root = tk.Tk()
    app = F1TelemetryApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()