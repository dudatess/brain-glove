import tkinter as tk
import math

class VectorViewer(tk.Frame):
    """
    Exibe um vetor (x,y,z) em modo 2D ou projeção 3D.
    Ideal para feedback da posição da mão.
    """

    def __init__(self, master, mode="2d", smoothing=0.2, size=220, bg="#ffffff"):
        super().__init__(master, bg=bg)

        self.mode = mode
        self.smoothing = smoothing
        self.size = size
        self.bg = bg

        self.cx = size // 2
        self.cy = size // 2
        self.radius = size * 0.45

        self.vec = [0, 0, 0]   # vetor atual (suavizado)

        self.canvas = tk.Canvas(self, width=size, height=size,
                                bg=bg, highlightthickness=0)
        self.canvas.pack()

        self._draw_static()
        self._draw_vector(0, 0)

    # ------------------------------------------------------------------
    def _draw_static(self):
        """Desenha elementos fixos (círculo e eixos)."""
        r = self.radius

        # Círculo
        self.canvas.create_oval(
            self.cx - r, self.cy - r,
            self.cx + r, self.cy + r,
            outline="#CBD5E1", width=2
        )

        # Eixos
        self.canvas.create_line(self.cx, self.cy - r, self.cx, self.cy + r,
                                fill="#94A3B8", width=1)
        self.canvas.create_line(self.cx - r, self.cy, self.cx + r, self.cy,
                                fill="#94A3B8", width=1)

    # ------------------------------------------------------------------
    def set_mode(self, mode):
        assert mode in ("2d", "3d")
        self.mode = mode

    # ------------------------------------------------------------------
    def update_vector(self, x, y, z=0):
        """
        Atualiza vetor da mão.
        Normalização + suavização + atualização gráfica.
        """

        # Normalização para evitar vetores gigantes
        norm = math.sqrt(x*x + y*y + z*z)
        if norm > 0:
            x /= norm
            y /= norm
            z /= norm

        # Suavização (LERP)
        s = self.smoothing
        self.vec[0] = self.vec[0]*(1-s) + x*s
        self.vec[1] = self.vec[1]*(1-s) + y*s
        self.vec[2] = self.vec[2]*(1-s) + z*s

        # Projeção 3D -> 2D
        if self.mode == "3d":
            px = self.vec[0] - self.vec[2] * 0.4
            py = self.vec[1] - self.vec[2] * 0.4
        else:
            px = self.vec[0]
            py = self.vec[1]

        self._draw_vector(px, py)

    # ------------------------------------------------------------------
    def _draw_vector(self, x, y):
        """Desenha seta representando o vetor (já normalizado)."""

        self.canvas.delete("vector")

        # Escala para caber dentro do círculo
        R = self.radius * 0.9
        vx = self.cx + x * R
        vy = self.cy - y * R   # eixo y invertido na tela

        # Seta (linha principal)
        self.canvas.create_line(
            self.cx, self.cy, vx, vy,
            fill="#2563EB", width=3, arrow=tk.LAST, tags="vector"
        )
