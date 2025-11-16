# main.py
import tkinter as tk
from gui.clinical_glove_app import ClinicalGloveApp

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Luva 5DT - Sistema de Neuroreabilitação")

    # 🔹 Ajusta automaticamente à resolução da tela
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Margem opcional (10% menor que o total da tela)
    app_width = int(screen_width * 0.9)
    app_height = int(screen_height * 0.9)

    # Centraliza a janela
    x = (screen_width // 2) - (app_width // 2)
    y = (screen_height // 2) - (app_height // 2)

    root.geometry(f"{app_width}x{app_height}+{x}+{y}")

    # Impede redimensionamento manual se quiser manter layout fixo
    root.minsize(800, 600)

    app = ClinicalGloveApp(root)
    root.mainloop()
