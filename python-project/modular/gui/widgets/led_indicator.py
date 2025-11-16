import tkinter as tk

class LEDIndicator(tk.Frame):
    """
    Indicador visual de status da luva com LED colorido.
    """

    COLORS = {
        "off": "#9CA3AF",        # cinza
        "ok": "#10B981",         # verde
        "error": "#EF4444",      # vermelho
        "warning": "#F59E0B",    # amarelo
        "active": "#3B82F6",     # azul
    }

    def __init__(self, master, label="Status", initial_state="off", **kwargs):
        super().__init__(master, bg=kwargs.get("bg", "#f8fafc"))
        self.state = initial_state
        self.label_text = label

        self.canvas = tk.Canvas(self, width=20, height=20, bg=self["bg"], highlightthickness=0)
        self.canvas.pack(side="left", padx=(0, 6))
        self.circle = self.canvas.create_oval(2, 2, 18, 18, fill=self.COLORS[self.state], outline="")

        self.label = tk.Label(self, text=f"{self.label_text}: {self.state.upper()}",
                              font=("Helvetica", 10, "bold"), bg=self["bg"], fg="#1a202c")
        self.label.pack(side="left")

    def set_state(self, state: str):
        """Atualiza a cor e o texto do LED."""
        if state not in self.COLORS:
            state = "off"
        self.state = state
        self.canvas.itemconfig(self.circle, fill=self.COLORS[state])
        self.label.config(text=f"{self.label_text}: {state.upper()}")

    def get_state(self) -> str:
        return self.state
