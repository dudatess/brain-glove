# main.py

import os
import tkinter as tk
from gui.clinical_glove_app import ClinicalGloveApp
from core.constants import IMAGES_FOLDER

# ============================================================
# PONTO DE ENTRADA
# ============================================================
if __name__ == "__main__":
    if not os.path.exists(IMAGES_FOLDER):
        print(f"AVISO: A pasta '{IMAGES_FOLDER}' não foi encontrada.")
        print("O sistema funcionará, mas sem imagens de gestos.")

    root = tk.Tk()
    app = ClinicalGloveApp(root)
    root.mainloop()

