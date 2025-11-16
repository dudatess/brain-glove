import tkinter as tk
from gui.widgets.led_indicator import LEDIndicator

class MainScreen(tk.Frame):
    """Tela inicial da aplicação."""

    def __init__(self, master, app):
        super().__init__(master, bg="#f0f4f8")
        self.app = app
        self.pack(expand=True, fill="both")
        self.build_ui()

    def build_ui(self):
        # Cabeçalho com o título e o indicador LED
        header = tk.Frame(self, bg="#f0f4f8")
        header.pack(fill="x", pady=(20, 10))

        title = tk.Label(
            header,
            text="Sistema de Neuroreabilitação - Luva 5DT",
            font=("Helvetica", 20, "bold"),
            bg="#f0f4f8", fg="#1a202c"
        )
        title.pack(side="left", padx=40)

        # LED indicador de status da luva
        self.led = LEDIndicator(header, status="desconectado")
        self.led.pack(side="right", padx=40)

        # Mensagem de instrução
        info = tk.Label(
            self,
            text="Conecte a luva e inicie a calibração para continuar.",
            font=("Helvetica", 12),
            bg="#f0f4f8"
        )
        info.pack(pady=10)

        # Botão de iniciar calibração
        start_btn = tk.Button(
            self, text="Iniciar Calibração",
            font=("Helvetica", 14, "bold"),
            bg="#3B82F6", fg="white",
            padx=25, pady=10,
            command=self.app.show_calibration_screen
        )
        start_btn.pack(pady=30)

        # Botão de sair
        exit_btn = tk.Button(
            self, text="Sair",
            font=("Helvetica", 12, "bold"),
            bg="#EF4444", fg="white",
            padx=20, pady=8,
            command=self.app.on_close
        )
        exit_btn.pack(pady=10)

    # Método chamado pelo app para atualizar o LED
    def update_glove_status(self, connected: bool):
        """Atualiza o LED conforme o status da conexão."""
        if connected:
            self.led.set_status("conectado")
        else:
            self.led.set_status("desconectado")
