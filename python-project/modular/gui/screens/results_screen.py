# gui/screens/results_screen.py

import tkinter as tk
from tkinter import ttk, messagebox
import datetime


class ResultsScreen(tk.Frame):
    """Tela de resultados após o processo de calibração."""

    def __init__(self, master, app, results_data):
        super().__init__(master, bg="#f0f4f8")
        self.app = app
        self.results_data = results_data
        self.pack(expand=True, fill="both")

        self.build_ui()

    # ============================================================
    # UI
    # ============================================================
    def build_ui(self):
        title = tk.Label(
            self, text="Resultados da Calibração",
            font=("Helvetica", 20, "bold"),
            bg="#f0f4f8", fg="#1a202c"
        )
        title.pack(pady=25)

        # --------------------------
        # Tabela
        # --------------------------
        table_frame = tk.Frame(self, bg="white", relief="raised", borderwidth=2)
        table_frame.pack(expand=True, fill="both", padx=30, pady=20)

        columns = ("Sensor", "Mínimo", "Máximo", "Threshold")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="center")

        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        # Inserção dos resultados
        self.populate_table()

        # --------------------------
        # Botões
        # --------------------------
        btn_frame = tk.Frame(self, bg="#f0f4f8")
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame, text="← Voltar",
            bg="#6B7280", fg="white",
            font=("Helvetica", 12, "bold"),
            padx=20, pady=8,
            command=self.app.show_calibration_screen
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame, text="Exportar Sessão",
            bg="#3B82F6", fg="white",
            font=("Helvetica", 12, "bold"),
            padx=20, pady=8,
            command=self.export_session
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame, text="Iniciar Feedback →",
            bg="#10B981", fg="white",
            font=("Helvetica", 12, "bold"),
            padx=20, pady=8,
            command=self.app.show_feedback_screen
        ).pack(side="left", padx=8)

    # ============================================================
    # POPULAR TABELA
    # ============================================================
    def populate_table(self):
        """Preenche a tabela com os valores calibrados."""
        mins = self.results_data["sensor_min"]
        maxs = self.results_data["sensor_max"]
        ths = self.results_data["sensor_threshold"]

        self.tree.delete(*self.tree.get_children())

        for i, (mn, mx, th) in enumerate(zip(mins, maxs, ths)):
            self.tree.insert("", "end", values=(
                f"Sensor {i+1}",
                f"{mn:.3f}",
                f"{mx:.3f}",
                f"{th:.3f}"
            ))

    # ============================================================
    # EXPORTAÇÃO
    # ============================================================
    def export_session(self):
        """
        Salva a sessão de calibração via state_manager.
        """
        try:
            session_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "sensor_min": self.results_data["sensor_min"],
                "sensor_max": self.results_data["sensor_max"],
                "sensor_threshold": self.results_data["sensor_threshold"],
                "num_sensors": len(self.results_data["sensor_min"]),
                "mode": "calibration"
            }

            # Dá suporte ao seu state_manager
            if hasattr(self.app, "state_manager"):
                path = self.app.state_manager.save_session(session_data)
            else:
                path = "data/sessions/calibration_export.json"
                import json, os
                os.makedirs("data/sessions", exist_ok=True)
                with open(path, "w") as f:
                    json.dump(session_data, f, indent=4)

            messagebox.showinfo("Exportação realizada", f"Sessão salva em:\n{path}")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar sessão:\n{e}")
