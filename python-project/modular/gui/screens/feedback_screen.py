# gui/screens/feedback_screen.py

import tkinter as tk
from tkinter import ttk

from gui.widgets.sensor_list import SensorList
from gui.widgets.led_indicator import LEDIndicator
from gui.widgets.vector_viewer import VectorViewer
from gui.widgets.frequency_plot import FrequencyPlot
from core.data_processing import extract_gesture_state, compute_vector, compute_frequency


class FeedbackScreen(tk.Frame):
    """Tela de feedback em tempo real integrada com processamento e visualização."""

    def __init__(self, master, app):
        super().__init__(master, bg="#f0f4f8")
        self.app = app

        # Buffers de dados para processamento mais avançado
        self.freq_buffer = []

        self.pack(expand=True, fill="both")
        self.build_ui()

    # ============================================================
    # UI
    # ============================================================
    def build_ui(self):
        title = tk.Label(
            self, text="Feedback em Tempo Real",
            font=("Helvetica", 20, "bold"),
            bg="#f0f4f8", fg="#1a202c"
        )
        title.pack(pady=20)

        # LED
        self.led = LEDIndicator(self, label="Status da Luva", initial_state="ok")
        self.led.pack(pady=5)

        # Layout principal
        main = tk.Frame(self, bg="#f0f4f8")
        main.pack(expand=True, fill="both", padx=20, pady=20)

        # ============================================================
        # COLUNA ESQUERDA → Vetor 2D/3D + Frequência
        # ============================================================
        left = tk.Frame(main, bg="white", relief="raised", borderwidth=2)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            left, text="Visualização do Vetor",
            font=("Helvetica", 15, "bold"),
            bg="white"
        ).pack(pady=5)

        # Viewer do vetor (2D ou 3D dependendo da config)
        self.vector_viewer = VectorViewer(left, mode="3d")
        self.vector_viewer.pack(expand=True, fill="both", padx=10, pady=5)

        tk.Label(
            left, text="Análise de Frequência",
            font=("Helvetica", 15, "bold"),
            bg="white"
        ).pack(pady=10)

        self.frequency_plot = FrequencyPlot(left)
        self.frequency_plot.pack(fill="x", padx=10, pady=10)

        # Gestos
        self.label_gesture = tk.Label(
            left, text="Gesto: --",
            font=("Helvetica", 14, "bold"),
            bg="white", fg="#1a202c"
        )
        self.label_gesture.pack(pady=10)

        # ============================================================
        # COLUNA DIREITA → Sensores
        # ============================================================
        right = tk.Frame(main, bg="white", relief="raised", borderwidth=2)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        tk.Label(
            right, text="Sensores",
            font=("Helvetica", 16, "bold"), bg="white"
        ).pack(pady=10)

        self.sensor_list = SensorList(
            right, 
            sensor_values=[0] * self.app.num_sensors,
            thresholds=self.app.calibration_data.get("sensor_threshold")
        )
        self.sensor_list.pack(expand=True, fill="both", padx=10, pady=10)

        # Botão final
        tk.Button(
            self, text="Finalizar Sessão",
            font=("Helvetica", 14, "bold"),
            bg="#EF4444", fg="white",
            padx=30, pady=10,
            command=self.finish_session
        ).pack(pady=20)

    # ============================================================
    # PROCESSAMENTO DO STREAM
    # ============================================================
    def process_glove_data(self, raw_data):
        """
        Chamado continuamente por ClinicalGloveApp.check_data().
        O pacote vem como string: "gesture,x1,x2,..."
        """

        try:
            parts = raw_data.split(",")
            vals = [float(v) for v in parts[1:]]
        except:
            return

        # ------------------------------------------------------------
        # 1) Atualizar sensores
        # ------------------------------------------------------------
        thresholds = self.app.calibration_data.get("sensor_threshold")
        self.sensor_list.update_values(vals, thresholds=thresholds)

        # ------------------------------------------------------------
        # 2) Estado do gesto (processado)
        # ------------------------------------------------------------
        gesture = extract_gesture_state(vals, thresholds)
        self.label_gesture.config(text=f"Gesto: {gesture}")

        # ------------------------------------------------------------
        # 3) Vetor 2D/3D
        # ------------------------------------------------------------
        vec = compute_vector(vals)
        self.vector_viewer.update_vector(vec)

        # ------------------------------------------------------------
        # 4) Frequência
        # ------------------------------------------------------------
        self.freq_buffer.append(vals)
        if len(self.freq_buffer) > 128:   # janela para FFT
            self.freq_buffer.pop(0)

        freq = compute_frequency(self.freq_buffer)
        if freq is not None:
            self.frequency_plot.update(freq)

    # ============================================================
    # FINALIZAÇÃO
    # ============================================================
    def update_glove_status(self, connected: bool):
        self.led.set_state("ok" if connected else "error")

    def finish_session(self):
        self.app.show_main_screen()
