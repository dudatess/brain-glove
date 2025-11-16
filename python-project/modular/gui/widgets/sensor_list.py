import tkinter as tk
from tkinter import ttk

class SensorList(tk.Frame):
    """
    Exibe a lista de sensores com valores e estado visual.
    Pode ser atualizada dinamicamente a partir do loop de dados.
    """

    def __init__(self, master, sensor_names, bg="#ffffff"):
        super().__init__(master, bg=bg)
        self.sensor_names = sensor_names
        self.bg = bg
        self.labels = []
        self.state_labels = []

        # Canvas rolável
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)

        self.canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')

        self._build_sensor_rows()
        self.inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _build_sensor_rows(self):
        for i, name in enumerate(self.sensor_names):
            frame = tk.Frame(self.inner, bg=self.bg)
            frame.pack(fill='x', pady=2, padx=4)

            label = tk.Label(frame, text=f"{name}: -", font=("Courier", 10),
                             bg=self.bg, anchor='w', width=40)
            label.pack(side='left')

            state_label = tk.Label(frame, text="⚪", font=("Helvetica", 12),
                                   bg=self.bg, width=3)
            state_label.pack(side='left', padx=4)

            self.labels.append(label)
            self.state_labels.append(state_label)

    def update_values(self, values, thresholds=None, active_mask=None):
        """
        Atualiza os valores e o estado visual dos sensores.
        thresholds: lista de limites para indicar 'aberto' (🟢) ou 'fechado' (🔴)
        active_mask: lista booleana indicando sensores ativos (True) ou desativados (False)
        """
        for i, (label, state_label) in enumerate(zip(self.labels, self.state_labels)):
            if i >= len(values):
                continue

            val = values[i]
            label.config(text=f"{self.sensor_names[i]}: {val:.3f}")

            # Define cor do estado
            if active_mask and not active_mask[i]:
                state_label.config(text="◼️")  # desativado
            elif thresholds and val >= thresholds[i]:
                state_label.config(text="🔴")
            elif thresholds:
                state_label.config(text="🟢")
            else:
                state_label.config(text="⚪")
