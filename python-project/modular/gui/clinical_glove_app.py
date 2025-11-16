import queue
import threading
import tkinter as tk
from tkinter import messagebox

# Importações principais
from core.glove_thread import GloveReaderThread
from core.constants import PATH_TO_C_EXE, GLOVE_CONNECTION_PORT, SENSOR_NAMES

# Importa telas
from gui.screens.main_screen import MainScreen
from gui.screens.calibration_screen import CalibrationScreen
from gui.screens.results_screen import ResultsScreen
from gui.screens.feedback_screen import FeedbackScreen


class ClinicalGloveApp:
    """
    Controlador principal da aplicação.
    Responsável por:
      - Iniciar a thread de leitura da luva;
      - Controlar as transições entre telas;
      - Gerenciar filas de dados e status.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sistema de Neuroreabilitação - Luva 5DT")
        self.root.configure(bg="#f0f4f8")

        # Estado da aplicação
        self.glove_connected = False
        self.data_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.c_thread = None
        self.active_screen = None

        # Armazena dados de calibração
        self.calibration_data = {
            "num_loops": 10,
            "disabled_sensors": [False] * len(SENSOR_NAMES),
            "sensor_min": [1.0] * len(SENSOR_NAMES),
            "sensor_max": [0.0] * len(SENSOR_NAMES),
            "sensor_threshold": [0.5] * len(SENSOR_NAMES),
        }

        # Inicializa primeira tela
        self.show_main_screen()

        # Inicia conexão
        self.start_connection()

        # Atualizações periódicas
        self.root.after(100, self.check_status)
        self.root.after(50, self.check_data)

        # Evento de fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ==========================
    # GERENCIAMENTO DE TELAS
    # ==========================
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_main_screen(self):
        self.clear_screen()
        self.active_screen = MainScreen(master=self.root, app=self)

    def show_calibration_screen(self):
        self.clear_screen()
        self.active_screen = CalibrationScreen(master=self.root, app=self)

    def show_results_screen(self, results_data):
        self.clear_screen()
        self.active_screen = ResultsScreen(master=self.root, app=self, results_data=results_data)

    def show_feedback_screen(self):
        self.clear_screen()
        self.active_screen = FeedbackScreen(master=self.root, app=self)

    # ==========================
    # CONEXÃO COM A LUVA
    # ==========================
    def start_connection(self):
        """Inicia a thread de leitura da luva, se ainda não estiver ativa."""
        if not self.c_thread or not self.c_thread.is_alive():
            try:
                self.c_thread = GloveReaderThread(
                    output_queue=self.data_queue,
                    status_queue=self.status_queue,
                    c_exe_path=PATH_TO_C_EXE,
                    glove_port=GLOVE_CONNECTION_PORT,
                    sampling_rate=60  # Hz (ajustável)
                )
                self.c_thread.start()

            except Exception as e:
                print(f"[ERRO] Falha ao iniciar conexão com a luva: {e}")
                self.status_queue.put("error_start")

    # ==========================
    # MONITORAMENTO
    # ==========================
    def check_status(self):
        try:
            while True:
                status = self.status_queue.get_nowait()
                if status == "connected":
                    self.glove_connected = True
                    if hasattr(self.active_screen, "update_glove_status"):
                        self.active_screen.update_glove_status(connected=True)
                elif status == "disconnected":
                    self.glove_connected = False
                    if hasattr(self.active_screen, "update_glove_status"):
                        self.active_screen.update_glove_status(connected=False)
        except queue.Empty:
            pass
        finally:
            self.root.after(200, self.check_status)

    def check_data(self):
        try:
            while True:
                data = self.data_queue.get_nowait()
                if hasattr(self.active_screen, "process_glove_data"):
                    self.active_screen.process_glove_data(data)
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self.check_data)

    # ==========================
    # EVENTOS
    # ==========================
    def on_close(self):
        if messagebox.askokcancel("Sair", "Deseja realmente encerrar o programa?"):
            if self.c_thread and self.c_thread.is_alive():
                self.c_thread.stop()
            self.root.destroy()
