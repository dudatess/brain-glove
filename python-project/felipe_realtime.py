import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import queue
import os
import numpy as np
from pyopengltk import OpenGLFrame
from OpenGL.GL import *

# ============================================================
# CONFIGURAÇÕES
# ============================================================
PATH_TO_C_EXE = "./TestGlove64.exe"
GLOVE_CONNECTION_PORT = "USB0"
IMAGES_FOLDER = "../gesture-images"

SENSOR_NAMES = [
    "Thumb Near", "Thumb Far", "Thumb/Index", "Index Near", "Index Far",
    "Index/Middle", "Middle Near", "Middle Far", "Middle/Ring", "Ring Near",
    "Ring Far", "Ring/Little", "Little Near", "Little Far",
    "Thumb Palm", "Wrist Bend", "Roll", "Pitch"
]

# ============================================================
# THREAD DE COMUNICAÇÃO COM O EXECUTÁVEL C
# ============================================================
def read_from_glove_thread(output_queue, status_queue, c_exe_path, glove_port):
    try:
        process = subprocess.Popen(
            [c_exe_path, glove_port],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        status_queue.put("connected")
        for output_line in iter(process.stdout.readline, ''):
            output_queue.put(output_line.strip())
        status_queue.put("disconnected")
    except FileNotFoundError:
        status_queue.put("error_not_found")
    except Exception as e:
        status_queue.put(f"error_{str(e)}")
    finally:
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            process.wait()

# ============================================================
# CLASSE DE VISUALIZAÇÃO 3D DA MÃO
# ============================================================
class Hand3D(OpenGLFrame):
    def __init__(self, master=None, get_sensor_values=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.get_sensor_values = get_sensor_values or (lambda: [0]*5)
        self.rotation = [25, -30]
        self.bind("<B1-Motion>", self.on_drag)

    def on_drag(self, event):
        """Permite rotacionar a mão com o mouse."""
        self.rotation[0] += event.y / 5
        self.rotation[1] += event.x / 5

    def initgl(self):
        glClearColor(0.95, 0.97, 1.0, 1)
        glEnable(GL_DEPTH_TEST)
        glLineWidth(4)

    def redraw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, -1.5, -8)
        glRotatef(self.rotation[0], 1, 0, 0)
        glRotatef(self.rotation[1], 0, 1, 0)

        sensor_vals = self.get_sensor_values()
        n = len(sensor_vals)
        n_dedos = 5
        dedos_vals = np.array_split(sensor_vals[:15], n_dedos)

        base_positions = [
            (-1.5, 0, 0), (-0.75, 0, 0),
            (0, 0, 0), (0.75, 0, 0), (1.5, 0, 0)
        ]

        # Palma
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_LINES)
        for i in range(4):
            glVertex3f(base_positions[i][0], base_positions[i][1], 0)
            glVertex3f(base_positions[i+1][0], base_positions[i+1][1], 0)
        glEnd()

        # Dedos
        for i, (x, y, z) in enumerate(base_positions):
            vals = dedos_vals[i]
            flex = np.mean(vals) if len(vals) else 0
            self.draw_finger(x, y, z, flex)

    def draw_finger(self, x, y, z, flex):
        """Desenha um dedo articulado."""
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(0.1 + 0.8*flex, 0.3, 0.9 - 0.7*flex)

        seg_len = 0.7
        for j in range(3):
            glBegin(GL_LINES)
            glVertex3f(0, 0, 0)
            glVertex3f(0, seg_len, 0)
            glEnd()
            glTranslatef(0, seg_len, 0)
            glRotatef(-flex * 90 / 3, 1, 0, 0)
        glPopMatrix()

# ============================================================
# CLASSE PRINCIPAL DA APLICAÇÃO
# ============================================================
class ClinicalGloveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Neuroreabilitação - Luva 5DT")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f4f8')

        self.glove_connected = False
        self.calibration_active = False
        self.feedback_active = False
        self.sensor_threshold = [0.5]*len(SENSOR_NAMES)
        self.latest_sensor_values = [0.0]*len(SENSOR_NAMES)

        self.data_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.c_thread = None

        self.setup_main_screen()
        self.root.after(100, self.check_status)
        self.root.after(100, self.process_data)
        self.start_connection()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ---------------------------------------------------------
    # TELA PRINCIPAL
    # ---------------------------------------------------------
    def setup_main_screen(self):
        self.clear_screen()
        main_container = tk.Frame(self.root, bg='#f0f4f8')
        main_container.pack(expand=True, fill='both', padx=40, pady=40)
        tk.Label(main_container, text="Sistema de Neuroreabilitação",
                 font=("Helvetica", 28, "bold"), bg='#f0f4f8').pack(pady=(0, 10))
        tk.Button(main_container, text="Iniciar Visualização 3D",
                  font=("Helvetica", 18, "bold"), bg='#3b82f6', fg='white',
                  command=self.start_feedback_screen).pack(pady=40)

    # ---------------------------------------------------------
    # VISUALIZAÇÃO 3D DE FEEDBACK
    # ---------------------------------------------------------
    def start_feedback_screen(self):
        self.clear_screen()
        self.feedback_active = True
        container = tk.Frame(self.root, bg='#f0f4f8')
        container.pack(expand=True, fill='both', padx=20, pady=20)

        title = tk.Label(container, text="Visualização 3D da Mão (Valores dos Sensores)",
                         font=("Helvetica", 22, "bold"), bg='#f0f4f8')
        title.pack(pady=15)

        main_layout = tk.Frame(container, bg='#f0f4f8')
        main_layout.pack(expand=True, fill='both')

        left_col = tk.Frame(main_layout, bg='white', relief='raised', borderwidth=2)
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 10))

        self.hand_view = Hand3D(left_col, get_sensor_values=self.get_current_sensor_values,
                                width=500, height=500)
        self.hand_view.pack(expand=True, fill='both', pady=10)

        right_col = tk.Frame(main_layout, bg='white', relief='raised', borderwidth=2)
        right_col.pack(side='left', fill='both', expand=True, padx=(10, 0))

        tk.Label(right_col, text="Sensores em Tempo Real",
                 font=("Helvetica", 16, "bold"), bg='white').pack(pady=10)

        self.sensor_labels = []
        frame = tk.Frame(right_col, bg='white')
        frame.pack(expand=True, fill='both')
        for i, name in enumerate(SENSOR_NAMES):
            lbl = tk.Label(frame, text=f"{name}: -", font=("Courier", 10),
                           bg='white', anchor='w')
            lbl.pack(anchor='w', padx=10)
            self.sensor_labels.append(lbl)

        tk.Button(container, text="← Voltar", font=("Helvetica", 14, "bold"),
                  bg='#ef4444', fg='white', command=self.setup_main_screen).pack(pady=20)

    # ---------------------------------------------------------
    # FUNÇÕES DE ATUALIZAÇÃO
    # ---------------------------------------------------------
    def get_current_sensor_values(self):
        vals = [min(max(v / 1023, 0), 1) for v in self.latest_sensor_values]
        return vals

    def process_data(self):
        try:
            while True:
                data_string = self.data_queue.get_nowait()
                parts = data_string.split(',')
                if len(parts) != len(SENSOR_NAMES) + 1:
                    continue
                gesture_id = int(parts[0])
                sensor_values = [float(v) for v in parts[1:]]
                self.latest_sensor_values = sensor_values
                if self.feedback_active:
                    for i, v in enumerate(sensor_values):
                        if i < len(self.sensor_labels):
                            self.sensor_labels[i].config(text=f"{SENSOR_NAMES[i]}: {v:.3f}")
                    if hasattr(self, 'hand_view'):
                        self.hand_view.after_idle(self.hand_view.tkRedraw)
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self.process_data)

    def start_connection(self):
        if not self.c_thread or not self.c_thread.is_alive():
            self.c_thread = threading.Thread(
                target=read_from_glove_thread,
                args=(self.data_queue, self.status_queue, PATH_TO_C_EXE, GLOVE_CONNECTION_PORT),
                daemon=True
            )
            self.c_thread.start()

    def check_status(self):
        try:
            while True:
                status = self.status_queue.get_nowait()
                print("Status:", status)
        except queue.Empty:
            pass
        finally:
            self.root.after(200, self.check_status)

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def on_closing(self):
        self.feedback_active = False
        self.root.destroy()

# ============================================================
# PONTO DE ENTRADA
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = ClinicalGloveApp(root)
    root.mainloop()
