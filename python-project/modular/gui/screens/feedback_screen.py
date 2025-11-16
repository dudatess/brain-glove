import tkinter as tk
from gui.widgets.sensor_list import SensorList
from gui.widgets.led_indicator import LEDIndicator

class FeedbackScreen(tk.Frame):
    """Tela de feedback em tempo real."""

    def __init__(self, master, app):
        super().__init__(master, bg="#f0f4f8")
        self.app = app
        self.pack(expand=True, fill="both")

        self.build_ui()

    def build_ui(self):
        tk.Label(
            self, text="Feedback em Tempo Real",
            font=("Helvetica", 20, "bold"),
            bg="#f0f4f8", fg="#1a202c"
        ).pack(pady=25)

        self.led = LEDIndicator(self, label="Status da Luva", initial_state="ok")
        self.led.pack(pady=5)

        layout = tk.Frame(self, bg="#f0f4f8")
        layout.pack(expand=True, fill="both", padx=20, pady=20)

        # Coluna esquerda (modelo 3D ou imagem)
        left = tk.Frame(layout, bg="white", relief="raised", borderwidth=2)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            left, text="Modelo 3D (placeholder)",
            font=("Helvetica", 16, "bold"),
            bg="white"
        ).pack(pady=10)

        self.canvas_3d = tk.Canvas(left, bg="white", highlightthickness=0)
        self.canvas_3d.pack(expand=True, fill="both", padx=10, pady=10)

        # Coluna direita (sensores)
        right = tk.Frame(layout, bg="white", relief="raised", borderwidth=2)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        tk.Label(
            right, text="Sensores",
            font=("Helvetica", 16, "bold"), bg="white"
        ).pack(pady=10)

        self.sensor_list = SensorList(right, self.app.calibration_data["sensor_min"])
        self.sensor_list.pack(expand=True, fill="both", padx=10, pady=10)

        # Botão de finalização
        tk.Button(
            self, text="Finalizar Sessão",
            font=("Helvetica", 14, "bold"),
            bg="#EF4444", fg="white", padx=30, pady=10,
            command=self.finish_session
        ).pack(pady=20)

    def process_glove_data(self, data):
        """Recebe os dados da luva e atualiza o painel."""
        thresholds = self.app.calibration_data["sensor_threshold"]
        self.sensor_list.update_values(data, thresholds=thresholds)

    def finish_session(self):
        self.app.show_main_screen()
