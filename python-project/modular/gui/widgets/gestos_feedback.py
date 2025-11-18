import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import math

class GestosFeedback(tk.Frame):
    """
    Widget que mostra a imagem do gesto, um rótulo grande e uma lista compacta
    com os valores dos sensores + "amplitude máxima" (registro de menor valor,
    compatível com realtime_glove_feedback).
    Uso:
      gf = GestosFeedback(parent, size=320, images=imgs_dict, sensor_names=[...])
      gf.update_from_values(gesture_id, values, label_text="Gesto: X")
      gf.reset_max_amplitude()
    """

    def __init__(self, master, size=320, images_dir=None, images=None,
                 sensor_names=None, bg="white"):
        super().__init__(master, bg=bg)
        self.size = size
        self.bg = bg
        self.images = images or {}
        self.sensor_names = sensor_names or []
        self.default_image = None

        # UI: imagem + labels + sensor list
        top = tk.Frame(self, bg=bg)
        top.pack(fill="x", padx=6, pady=6)

        # imagem do gesto
        self.image_label = tk.Label(top, bg=bg)
        self.image_label.pack(side="left", padx=6)

        # área de texto grande com gesto e status
        txt_frame = tk.Frame(top, bg=bg)
        txt_frame.pack(side="left", fill="y", padx=8)

        self.gesture_big = tk.Label(txt_frame, text="Gesto: --", font=("Helvetica", 24, "bold"), bg=bg)
        self.gesture_big.pack(anchor="w", pady=(6,4))

        self.gesture_small = tk.Label(txt_frame, text="Estado: --", font=("Helvetica", 12), bg=bg, fg="#374151")
        self.gesture_small.pack(anchor="w")

        # controle de amplitude (reset)
        ctrl = tk.Frame(txt_frame, bg=bg)
        ctrl.pack(anchor="w", pady=(10,0))
        self.reset_btn = tk.Button(ctrl, text="Registrar nova sessão", command=self.reset_max_amplitude,
                                   bg="#06b6d4", fg="white")
        self.reset_btn.pack(side="left", padx=(0,6))
        self.last_ts_label = tk.Label(ctrl, text="", bg=bg, font=("Helvetica", 10))
        self.last_ts_label.pack(side="left")

        # sensor list (scroll)
        sensors_frame = tk.Frame(self, bg=bg)
        sensors_frame.pack(fill="both", expand=True, padx=6, pady=(0,6))

        self.canvas = tk.Canvas(sensors_frame, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(sensors_frame, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)

        self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # preparar linhas de sensores (vazias por enquanto)
        self.sensor_rows = []  # list of dicts {name,label_value,label_max}
        self.max_amplitude = []  # menor valor encontrado (inicial grande)

        # carregar imagens se necessário (apenas se self.images vazio)
        if not self.images:
            if images_dir is None:
                images_dir = os.path.join(os.getcwd(), "assets", "gesture-images")
            try:
                if os.path.isdir(images_dir):
                    for fname in sorted(os.listdir(images_dir)):
                        base, _ = os.path.splitext(fname)
                        try:
                            key = int(base)
                        except Exception:
                            continue
                        path = os.path.join(images_dir, fname)
                        try:
                            img = Image.open(path).resize((self.size, self.size), Image.Resampling.LANCZOS)
                            self.images[key] = ImageTk.PhotoImage(img)
                        except Exception:
                            continue
            except Exception:
                self.images = {}

        self.default_image = self.images.get(-1)
        if self.default_image:
            self.image_label.config(image=self.default_image)
            self.image_label.image = self.default_image

        # inicializar sensor rows com nomes (se fornecidos) ou placeholders
        count = len(self.sensor_names) if self.sensor_names else 0
        if count == 0:
            # não sabemos quantos sensores; rows serão criadas dinamicamente na primeira atualização
            self.max_amplitude = []
        else:
            self._build_sensor_rows(count)

        # ajustes do scroll region
        self.inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _build_sensor_rows(self, count):
        # limpar existentes
        for w in self.sensor_rows:
            for v in w.values():
                try:
                    v.destroy()
                except Exception:
                    pass
        self.sensor_rows = []
        self.max_amplitude = [1e9] * count

        for i in range(count):
            row = tk.Frame(self.inner, bg=self.bg)
            row.pack(fill="x", pady=2, padx=6)
            name = self.sensor_names[i] if i < len(self.sensor_names) else f"S{i+1}"
            lbl_name = tk.Label(row, text=name + ":", width=30, anchor="w", bg=self.bg, font=("Helvetica", 10))
            lbl_name.pack(side="left")
            lbl_val = tk.Label(row, text="-", width=8, anchor="e", bg=self.bg, font=("Helvetica", 10))
            lbl_val.pack(side="left", padx=(6,8))
            lbl_max = tk.Label(row, text="-", width=8, anchor="e", bg=self.bg, font=("Helvetica", 10), fg="green")
            lbl_max.pack(side="left")
            self.sensor_rows.append({"name": lbl_name, "value": lbl_val, "max": lbl_max})

    def reset_max_amplitude(self):
        # reinicia o registro (seta valores altos para detectar novos mínimos)
        n = len(self.max_amplitude)
        if n == 0 and self.sensor_rows:
            n = len(self.sensor_rows)
        if n == 0:
            # indefinido ainda — será configurado no primeiro update
            self.max_amplitude = []
        else:
            self.max_amplitude = [1e9] * n
        from datetime import datetime
        self.last_ts_label.config(text=f"Registrando: {datetime.now().strftime('%H:%M:%S')}")
        # limpar labels de max
        for r in self.sensor_rows:
            r["max"].config(text="-")

    def update_from_values(self, gesture_id, values, label_text=None):
        """
        Atualiza imagem, labels e sensores a partir dos valores atuais.
        gesture_id: int or None
        values: iterable de floats
        label_text: texto opcional para o label principal
        """
        try:
            # garantir lista
            vals = list(values) if values is not None else []
        except Exception:
            vals = []

        # criar sensor rows dinamicamente se não existirem
        if not self.sensor_rows and vals:
            self._build_sensor_rows(len(vals))

        # atualizar imagem
        try:
            gid = None
            if gesture_id is not None:
                try:
                    gid = int(gesture_id)
                except Exception:
                    gid = None
            img = self.images.get(gid, self.default_image)
            if img:
                self.image_label.config(image=img)
                self.image_label.image = img
        except Exception:
            pass

        # atualizar labels do gesto
        try:
            if label_text is not None:
                self.gesture_big.config(text=label_text)
            else:
                self.gesture_big.config(text=f"Gesto: {gid if gid is not None else '--'}")
        except Exception:
            pass

        # atualizar sensores e max amplitudes (registro de menores valores)
        try:
            for i, v in enumerate(vals):
                if i >= len(self.sensor_rows):
                    # criar row extra se necessário
                    self._build_sensor_rows(len(vals))
                # format value
                try:
                    fv = float(v)
                except Exception:
                    fv = 0.0
                self.sensor_rows[i]["value"].config(text=f"{fv:.3f}")
                # atualizar registro de "amplitude" (menor valor)
                if i >= len(self.max_amplitude):
                    self.max_amplitude += [1e9] * (i + 1 - len(self.max_amplitude))
                if fv < self.max_amplitude[i]:
                    self.max_amplitude[i] = fv
                    self.sensor_rows[i]["max"].config(text=f"{self.max_amplitude[i]:.3f}")
        except Exception:
            pass

        # ajustar scrollregion
        try:
            self.inner.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception:
            pass