import tkinter as tk
from tkinter import ttk

class ResultsScreen(tk.Frame):
    """Tela de resultados após calibração."""

    def __init__(self, master, app, results_data):
        super().__init__(master, bg="#f0f4f8")
        self.app = app
        self.results_data = results_data
        self.pack(expand=True, fill="both")

        self.build_ui()

    def build_ui(self):
        tk.Label(
            self, text="Resultados da Calibração",
            font=("Helvetica", 20, "bold"), bg="#f0f4f8", fg="#1a202c"
        ).pack(pady=25)

        table_frame = tk.Frame(self, bg="white", relief="raised", borderwidth=2)
        table_frame.pack(expand=True, fill="both", padx=30, pady=20)

        columns = ("Sensor", "Mínimo", "Máximo", "Threshold")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        tree.pack(expand=True, fill="both", padx=10, pady=10)

        for i, (mn, mx, th) in enumerate(
            zip(
                self.results_data["sensor_min"],
                self.results_data["sensor_max"],
                self.results_data["sensor_threshold"]
            )
        ):
            tree.insert("", "end", values=(f"Sensor {i+1}", f"{mn:.3f}", f"{mx:.3f}", f"{th:.3f}"))

        btn_frame = tk.Frame(self, bg="#f0f4f8")
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame, text="← Voltar", bg="#6B7280", fg="white",
            font=("Helvetica", 12, "bold"), padx=20, pady=8,
            command=self.app.show_calibration_screen
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame, text="Iniciar Feedback →", bg="#10B981", fg="white",
            font=("Helvetica", 12, "bold"), padx=20, pady=8,
            command=self.app.show_feedback_screen
        ).pack(side="left", padx=8)
