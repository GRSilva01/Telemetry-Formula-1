import os
import sys
import ctypes
import tkinter as tk
from database.connection import init_db
from ui.app_window import F1TelemetryApp

def main():
    if sys.platform == "win32":
        myappid = "redbull.telemetry.pitwall.suite"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    init_db()

    root = tk.Tk()

    # Carrega o ícone da janela a partir da pasta assets
    base_dir = os.path.dirname(__file__)
    window_icon_path = os.path.join(base_dir, "icon", "Icon.png")
    
    if os.path.exists(window_icon_path):
        app_icon = tk.PhotoImage(file=window_icon_path)
        root.iconphoto(True, app_icon)

    app = F1TelemetryApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()