# gui/screens/calibration_screen.py

import tkinter as tk
from tkinter import ttk, messagebox

from core.calibration_mode import CalibrationMode
from gui.widgets.sensor_list import SensorList
from gui.widgets.led_indicator import LEDIndicator


class CalibrationScreen(tk.Frame):
    """Tela de calibração baseada no novo CalibrationMode."""

    def __init__(self, master, app):
        super().__init__(master, bg="#f0f4f8")
        self.app = app
        self.pack(expand=True, fill="both")

        # Instância do modo de calibração
        self.calib = CalibrationMode(sensor_names=self.app.calibration_data["sensor_min"])

        # Registrar callbacks GUI
        self.calib.on_cycle_start = self.on_cycle_start
        self.calib.on_cycle_progress = self.on_cycle_progress
        self.calib.on_cycle_end = self.on_cycle_end
        self.calib.on_continuous_update = self.on_continuous_update
        self.calib.on_finish = self.on_finish

        self.build_ui()

        # Cortina de dados da luva
        self.root = self.app.root

    # ============================================================
    # INTERFACE
    # ============================================================
    def build_ui(self):
        title = tk.Label(
            self, text="Calibração da Luva",
            font=("Helvetica", 20, "bold"),
            bg="#f0f4f8", fg="#1a202c"
        )
        title.pack(pady=20)

        # Indicador da luva
        self.led = LEDIndicator(self, label="Status da Luva")
        self.led.pack(pady=5)

        # Container central
        main_frame = tk.Frame(self, bg="white", relief="groove", borderwidth=2)
        main_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # --- Seleção de modo ---
        mode_frame = tk.Frame(main_frame, bg="white")
        mode_frame.pack(pady=10)

        tk.Label(
            mode_frame, text="Modo de Calibração:",
            font=("Helvetica", 12, "bold"), bg="white"
        ).grid(row=0, column=0, padx=5)

        self.mode_var = tk.StringVar(value="cycles")
        ttk.Radiobutton(mode_frame, text="Ciclos", value="cycles",
                        variable=self.mode_var).grid(row=0, column=1)
        ttk.Radiobutton(mode_frame, text="Contínuo", value="continuous",
                        variable=self.mode_var).grid(row=0, column=2)

        # --- Parâmetros ---
        param_frame = tk.Frame(main_frame, bg="white")
        param_frame.pack(pady=10)

        tk.Label(param_frame, text="Nº de ciclos:", bg="white").grid(row=0, column=0)
        tk.Label(param_frame, text="Duração (s):", bg="white").grid(row=1, column=0)

        self.entry_cycles = tk.Entry(param_frame, width=5)
        self.entry_cycles.insert(0, "10")
        self.entry_cycles.grid(row=0, column=1, padx=5)

        self.entry_duration = tk.Entry(param_frame, width=5)
        self.entry_duration.insert(0, "4")
        self.entry_duration.grid(row=1, column=1, padx=5)

        # --- Lista de sensores ---
        tk.Label(
            main_frame, text="Sensores Ativos",
            font=("Helvetica", 12, "bold"), bg="white"
        ).pack(pady=5)

        self.sensor_list = SensorList(
            main_frame,
            sensor_values=[0.0] * len(self.app.calibration_data["sensor_min"]),
            allow_selection=True
        )
        self.sensor_list.pack(fill="both", expand=True, padx=10, pady=10)

        # Progresso
        self.progress = ttk.Progressbar(self, length=300, mode="determinate")
        self.progress.pack(pady=10)

        # Botões
        btn_frame = tk.Frame(self, bg="#f0f4f8")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, text="Iniciar Calibração",
            font=("Helvetica", 13, "bold"),
            bg="#3B82F6", fg="white",
            padx=25, pady=8,
            command=self.start_calibration
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame, text="Ver Resultados",
            font=("Helvetica", 13, "bold"),
            bg="#10B981", fg="white",
            padx=25, pady=8,
            command=self.go_to_results
        ).pack(side="left", padx=10)

    # ============================================================
    # INTEGRAÇÃO COM CalibrationMode
    # ============================================================
    def start_calibration(self):
        """Inicia o modo de calibração real."""

        if not self.app.glove_connected:
            messagebox.showerror("Erro", "A luva não está conectada.")
            return

        # LED ativo
        self.led.set_state("active")

        # Configura modo
        mode = self.mode_var.get()
        self.calib.set_mode(mode)

        if mode == "cycles":
            try:
                num_cycles = int(self.entry_cycles.get())
                duration = float(self.entry_duration.get())
            except ValueError:
                messagebox.showerror("Erro", "Parâmetros inválidos.")
                return

            self.calib.set_cycle_parameters(num_cycles, duration)

        # Sensores ativos
        self.calib.set_disabled_sensors(self.sensor_list.get_disabled_mask())

        # Inicia calibração
        self.calib.start()

    # Chamado continuamente pelo app (ClinicalGloveApp.check_data)
    def process_glove_data(self, data_str):
        """Recebe pacotes da luva e envia para o CalibrationMode."""
        # Data string: "gesture,x1,x2,..."
        try:
            parts = data_str.split(",")
            values = [float(v) for v in parts[1:]]
        except:
            return

        self.calib.update(values)

        # Atualizar UI com os valores atuais
        self.sensor_list.update_values(values)

    # ============================================================
    # CALLBACKS DO CalibrationMode
    # ============================================================
    def on_cycle_start(self, n):
        self.progress["value"] = 0

    def on_cycle_progress(self, progress_01):
        self.progress["value"] = progress_01 * 100

    def on_cycle_end(self, n):
        self.progress["value"] = 100

    def on_continuous_update(self, mins, maxs):
        # Aqui você pode exibir num gráfico futuramente
        pass

    def on_finish(self, results):
        self.led.set_state("ok")
        self.app.calibration_data = results  # salvar no app
        messagebox.showinfo("Concluído", "Calibração finalizada!")

    # ============================================================
    # NAVEGAÇÃO
    # ============================================================
    def update_glove_status(self, connected: bool):
        self.led.set_state("conectado" if connected else "desconectado")

    def go_to_results(self):
        self.app.show_results_screen(self.app.calibration_data)
