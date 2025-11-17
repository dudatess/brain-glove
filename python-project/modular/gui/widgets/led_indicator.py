import tkinter as tk

class LEDIndicator(tk.Frame):
    """
    Indicador visual de status da luva com LED colorido.
    Estados suportados:
      - ok
      - active
      - desconectado
      - erro
    """

    COLORS = {
        "ok": "green",
        "active": "yellow",
        "desconectado": "red",
        "erro": "orange"
    }

    def __init__(self, master, label="Status", initial_state="desconectado", **kwargs):
        bg_color = kwargs.get("bg", "#f8fafc")
        super().__init__(master, bg=bg_color)

        self.state = initial_state
        self.label_text = label

        # LED (círculo)
        self.canvas = tk.Canvas(
            self, width=20, height=20,
            bg=bg_color, highlightthickness=0
        )
        self.canvas.pack(side="left", padx=(0, 6))

        # Desenha o LED
        self.circle = self.canvas.create_oval(
            2, 2, 18, 18,
            fill=self.COLORS.get(self.state, "red"),
            outline=""
        )

        # Label do estado
        self.label = tk.Label(
            self,
            text=f"{self.label_text}: {self.state.upper()}",
            font=("Helvetica", 10, "bold"),
            bg=bg_color,
            fg="#1a202c"
        )
        self.label.pack(side="left")

    # --------------------------------------------------------
    # API PÚBLICA
    # --------------------------------------------------------

    def set_state(self, state: str):
        """
        Atualiza o LED visualmente e o rótulo de texto.
        """
        if state not in self.COLORS:
            state = "desconectado"

        self.state = state
        self.canvas.itemconfig(self.circle, fill=self.COLORS[state])
        self.label.config(text=f"{self.label_text}: {state.upper()}")

    def get_state(self) -> str:
        """Retorna o estado atual."""
        return self.state
