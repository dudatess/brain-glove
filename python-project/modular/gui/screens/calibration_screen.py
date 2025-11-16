import tkinter as tk
from tkinter import ttk
from gui.widgets.sensor_list import SensorList
from gui.widgets.led_indicator import LEDIndicator

class CalibrationScreen(tk.Frame):
    """Tela de calibração dos sensores."""

    def __init__(self, master, app):
        super().__init__(master, bg="#f0f4f8")
        self.app = app
        self.pack(expand=True, fill="both")

        self.build_ui()

    def build_ui(self):
        title = tk.Label(
            self, text="Calibração da Luva",
            font=("Helvetica", 20, "bold"),
            bg="#f0f4f8", fg="#1a202c"
        )
        title.pack(pady=30)

        self.led = LEDIndicator(self, label="Status da Luva")
        self.led.pack(pady=5)

        frame = tk.Frame(self, bg="white", relief="raised", borderwidth=2)
        frame.pack(padx=30, pady=20, fill="both", expand=True)

        tk.Label(
            frame, text="Leitura dos Sensores (modo calibração)",
            font=("Helvetica", 14, "bold"),
            bg="white"
        ).pack(pady=10)

        self.sensor_list = SensorList(frame, self.app.calibration_data["sensor_min"])
        self.sensor_list.pack(expand=True, fill="both", padx=10, pady=10)

        button_frame = tk.Frame(self, bg="#f0f4f8")
        button_frame.pack(pady=20)

        start_btn = tk.Button(
            button_frame, text="Iniciar Coleta",
            font=("Helvetica", 13, "bold"),
            bg="#3B82F6", fg="white", padx=25, pady=8,
            command=self.start_calibration
        )
        start_btn.pack(side="left", padx=10)

        next_btn = tk.Button(
            button_frame, text="Ver Resultados",
            font=("Helvetica", 13, "bold"),
            bg="#10B981", fg="white", padx=25, pady=8,
            command=self.go_to_results
        )
        next_btn.pack(side="left", padx=10)

    def start_calibration(self):
        """Inicia coleta dos dados de calibração."""
        self.led.set_state("active")

        # Aqui você chamaria sua função real de calibração
        # (mock de exemplo)
        for i in range(len(self.app.calibration_data["sensor_min"])):
            self.app.calibration_data["sensor_min"][i] = 0.1
            self.app.calibration_data["sensor_max"][i] = 0.9

        self.app.calibration_data["sensor_threshold"] = [
            (mn + mx) / 2 for mn, mx in zip(
                self.app.calibration_data["sensor_min"],
                self.app.calibration_data["sensor_max"]
            )
        ]
        self.led.set_state("ok")

    def go_to_results(self):
        """Avança para tela de resultados."""
        self.app.show_results_screen(self.app.calibration_data)
