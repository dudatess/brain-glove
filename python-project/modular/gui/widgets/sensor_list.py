import tkinter as tk
from tkinter import ttk

class SensorList(tk.Frame):

    def __init__(self, master, sensor_names, max_value=1.0, bg="#ffffff"):
        super().__init__(master, bg=bg)
        self.sensor_names = sensor_names
        self.max_value = max_value
        self.bg = bg
        self.rows = []

        # Área com scroll
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient='vertical',
                                       command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)

        self.canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')

        self._build_rows()
        self._update_scroll_region()

    # -----------------------------------------------------------
    def _update_scroll_region(self):
        """Atualiza região do scroll sempre que necessário."""
        self.inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    # -----------------------------------------------------------
    def _build_rows(self):
        BAR_W = 160
        BAR_H = 12

        for name in self.sensor_names:
            row_frame = tk.Frame(self.inner, bg=self.bg)
            row_frame.pack(fill='x', pady=4, padx=4)

            # Nome
            lbl = tk.Label(row_frame, text=name, width=12,
                           anchor='w', bg=self.bg)
            lbl.pack(side='left')

            # Barra horizontal
            bar_canvas = tk.Canvas(row_frame, width=BAR_W, height=BAR_H,
                                   bg="#e6e6e6", highlightthickness=0)
            bar_canvas.pack(side='left', padx=6)
            bar_rect = bar_canvas.create_rectangle(0, 0, 1, BAR_H,
                                                   fill="#67a6f7", width=0)

            # Valor numérico
            val_lbl = tk.Label(row_frame, text="0.000", width=6, bg=self.bg)
            val_lbl.pack(side='left', padx=6)

            # Status
            status_lbl = tk.Label(row_frame, text="⚪", width=3, bg=self.bg)
            status_lbl.pack(side='left')

            self.rows.append({
                "frame": row_frame,
                "label": lbl,
                "bar": bar_canvas,
                "bar_rect": bar_rect,
                "value": val_lbl,
                "status": status_lbl
            })

    # -----------------------------------------------------------
    def update_values(self, values, thresholds=None, active_mask=None):
        """
        values: lista de valores dos sensores
        thresholds: lista opcional do mesmo tamanho
        active_mask: lista de booleans para ativar/desativar sensores
        """
        BAR_W = 160

        for i, row in enumerate(self.rows):
            if i >= len(values):
                continue

            v = float(values[i])
            row["value"].config(text=f"{v:.3f}")

            # Redimensionamento da barra
            bar_canvas = row["bar"]
            rect = row["bar_rect"]
            fill_w = max(1, min(BAR_W, int((v / self.max_value) * BAR_W)))

            # Lógica de cor / status
            color = "#67a6f7"   # Normal azul

            if active_mask and not active_mask[i]:
                color = "#888888"   # Cinza — desativado
                row["status"].config(text="◼️")

            elif thresholds and v >= thresholds[i]:
                color = "#ff5b5b"   # Vermelho — acima do limite
                row["status"].config(text="🔴")

            else:
                row["status"].config(text="🟢" if thresholds else "⚪")

            bar_canvas.coords(rect, 0, 0, fill_w, 12)
            bar_canvas.itemconfig(rect, fill=color)

        self._update_scroll_region()
