import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import threading
import queue
import os

# ============================================================
# CONFIGURAÇÕES (ajuste conforme necessário)
# ============================================================
PATH_TO_C_EXE = "./TestGlove64.exe"
GLOVE_CONNECTION_PORT = "USB0"
IMAGES_FOLDER = "../gesture-images"

IMAGE_MAP = {
    0: "0.png", 1: "1.png", 2: "2.png", 3: "3.png", 4: "4.png",
    5: "5.png", 6: "6.png", 7: "7.png", 8: "8.png", 9: "9.png",
    10: "10.png", 11: "11.png", 12: "12.png", 13: "13.png",
    14: "14.png", 15: "15.png", -1: "-1.png",
}

SENSOR_NAMES = [
    "Thumb Near", "Thumb Far", "Thumb/Index", "Index Near", "Index Far",
    "Index/Middle", "Middle Near", "Middle Far", "Middle/Ring", "Ring Near",
    "Ring Far", "Ring/Little", "Little Near", "Little Far",
    "Thumb Palm", "Wrist Bend", "Roll", "Pitch"
]

# ============================================================
# THREAD DE COMUNICAÇÃO (lê stdout do executável C)
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
        
        while True:
            output_line = process.stdout.readline()
            if not output_line:
                status_queue.put("disconnected")
                break
            output_queue.put(output_line.strip())
                
    except FileNotFoundError:
        status_queue.put("error_not_found")
    except Exception as e:
        status_queue.put(f"error_{str(e)}")
    finally:
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            process.wait()

# ============================================================
# APLICAÇÃO PRINCIPAL
# ============================================================
class ClinicalGloveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Neuroreabilitação - Luva 5DT")

        # Ajuste dinâmico de janela à resolução do usuário
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        self.root.geometry(f"{screen_w}x{screen_h}")
        # Permitir redimensionar (mantive True para permitir janelas menores se desejado)
        self.root.resizable(True, True)
        self.root.configure(bg='#f0f4f8')

        # Estados e variáveis
        self.glove_connected = False
        self.calibration_active = False
        self.feedback_active = False
        self.calibration_count = 0

        self.num_loops = 10  # valor default (será pedidono início da calibração)
        self.disabled_from_calibration = [False] * len(SENSOR_NAMES)  # sensores excluídos da calibração
        self.active_sensors = [tk.BooleanVar(value=True) for _ in SENSOR_NAMES]  # usados em runtime (feedback)

        # Calibração: armazena valores máximos e mínimos de cada ciclo
        self.calibration_max_per_cycle = []
        self.calibration_min_per_cycle = []
        self.current_cycle_max = None
        self.current_cycle_min = None

        # Valores finais de calibração
        self.sensor_max_values = [0.0] * len(SENSOR_NAMES)
        self.sensor_min_values = [1.0] * len(SENSOR_NAMES)
        self.sensor_threshold = [0.5] * len(SENSOR_NAMES)

        # Estado dos dedos (True = fechado, False = aberto)
        self.finger_states = [False] * len(SENSOR_NAMES)

        # Buffers para remoção de artefatos (lista de listas)
        self._artifact_buffer = [[] for _ in SENSOR_NAMES]
        # parâmetros de filtragem
        self.artifact_window = 5
        self.artifact_threshold = 0.15  # ajuste conforme necessário

        self.images = self.load_images()
        self.data_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.c_thread = None

        # Monta interface
        self.setup_main_screen()

        # Laços periódicos
        self.root.after(100, self.check_status)
        self.root.after(50, self.process_data)

        # Inicia conexão (thread) com executável C
        self.start_connection()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # -------------------------
    # Imagens
    # -------------------------
    def load_images(self):
        images = {}
        # Ajusta tamanho das imagens tomando uma fração da tela para melhor layout
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        target_size = min(int(screen_w * 0.25), int(screen_h * 0.45), 600)
        for gesture_id, filename in IMAGE_MAP.items():
            path = os.path.join(IMAGES_FOLDER, filename)
            if os.path.exists(path):
                try:
                    img = Image.open(path).resize((target_size, target_size), Image.Resampling.LANCZOS)
                    images[gesture_id] = ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"Aviso: falha ao carregar imagem '{path}': {e}")
            else:
                print(f"Aviso: Imagem '{path}' não encontrada.")
        return images

    # -------------------------
    # Tela principal
    # -------------------------
    def setup_main_screen(self):
        self.clear_screen()
        main_container = tk.Frame(self.root, bg='#f0f4f8')
        main_container.pack(expand=True, fill='both', padx=40, pady=40)

        title = tk.Label(main_container, text="Sistema de Neuroreabilitação",
                        font=("Helvetica", 28, "bold"), bg='#f0f4f8', fg='#1a202c')
        title.pack(pady=(0, 10))

        subtitle = tk.Label(main_container, text="Luva 5DT - Reconhecimento de Gestos em Tempo Real",
                           font=("Helvetica", 16), bg='#f0f4f8', fg='#4a5568')
        subtitle.pack(pady=(0, 40))

        status_card = tk.Frame(main_container, bg='white', relief='raised', borderwidth=2)
        status_card.pack(pady=20, ipadx=40, ipady=30)

        status_label = tk.Label(status_card, text="Status da Luva",
                               font=("Helvetica", 18, "bold"), bg='white', fg='#2d3748')
        status_label.pack(pady=(0, 20))

        led_frame = tk.Frame(status_card, bg='white')
        led_frame.pack(pady=10)

        self.led_canvas = tk.Canvas(led_frame, width=60, height=60, bg='white', highlightthickness=0)
        self.led_canvas.pack(side='left', padx=10)
        self.led_indicator = self.led_canvas.create_oval(10, 10, 50, 50, fill='#ef4444',
                                                         outline='#dc2626', width=3)

        self.status_text = tk.Label(led_frame, text="Desconectado",
                                   font=("Helvetica", 20, "bold"), bg='white', fg='#ef4444')
        self.status_text.pack(side='left', padx=10)

        self.start_calibration_btn = tk.Button(
            main_container, text="Iniciar Calibração", font=("Helvetica", 16, "bold"),
            bg='#3b82f6', fg='white', activebackground='#2563eb', activeforeground='white',
            padx=40, pady=15, cursor='hand2', state='disabled',
            command=self.show_calibration_instructions
        )
        self.start_calibration_btn.pack(pady=30)

        info_frame = tk.Frame(main_container, bg='#e2e8f0', relief='flat', borderwidth=1)
        info_frame.pack(pady=20, fill='x', padx=50)

        info_text = """📋 Instruções:

1. Conecte a luva 5DT ao computador
2. Aguarde o indicador verde de conexão
3. Clique em "Iniciar Calibração" para começar
4. Visualize os gestos reconhecidos em tempo real!"""

        info_label = tk.Label(info_frame, text=info_text, font=("Helvetica", 12),
                             bg='#e2e8f0', fg='#2d3748', justify='left')
        info_label.pack(padx=20, pady=15)

    # -------------------------
    # Instruções de calibração (permite selecionar sensores a excluir)
    # -------------------------
    def show_calibration_instructions(self):
        self.clear_screen()
        container = tk.Frame(self.root, bg='#f0f4f8')
        container.pack(expand=True, fill='both', padx=50, pady=30)

        title = tk.Label(container, text="Protocolo de Calibração",
                        font=("Helvetica", 26, "bold"), bg='#f0f4f8', fg='#1a202c')
        title.pack(pady=(0, 20))

        # Texto de instruções
        instructions_card = tk.Frame(container, bg='white', relief='raised', borderwidth=2)
        instructions_card.pack(fill='both', expand=True, padx=10, pady=10)

        instructions_text = """📝 Instruções do Protocolo de Calibração

Durante a calibração você realizará múltiplos ciclos de abertura e fechamento.
O sistema registrará valores máximos e mínimos por sensor.
Você pode escolher quantos ciclos deseja executar e excluir sensores da calibração se suspeitar de artefatos.
"""
        instructions_label = tk.Label(instructions_card, text=instructions_text,
                                     font=("Courier", 11), bg='white', fg='#2d3748', justify='left')
        instructions_label.pack(padx=20, pady=20)

        # Frame para opções: número de loops e seleção de sensores para excluir
        options_frame = tk.Frame(container, bg='#f0f4f8')
        options_frame.pack(pady=10)

        loops_btn = tk.Button(options_frame, text="Definir número de ciclos",
                              font=("Helvetica", 12), bg='#3b82f6', fg='white',
                              padx=20, pady=10, cursor='hand2',
                              command=self.ask_num_loops)
        loops_btn.pack(side='left', padx=8)

        exclude_btn = tk.Button(options_frame, text="Selecionar sensores a excluir da calibração",
                                font=("Helvetica", 12), bg='#f59e0b', fg='white',
                                padx=20, pady=10, cursor='hand2',
                                command=self.show_exclude_sensors_dialog)
        exclude_btn.pack(side='left', padx=8)

        # Exibir uma linha de identificação dos sensores excluídos
        self.excluded_label = tk.Label(container, text="Sensores excluídos: Nenhum",
                                       font=("Helvetica", 11), bg='#f0f4f8')
        self.excluded_label.pack(pady=10)

        button_frame = tk.Frame(container, bg='#f0f4f8')
        button_frame.pack(pady=20)

        back_btn = tk.Button(button_frame, text="← Voltar", font=("Helvetica", 14),
                            bg='#6b7280', fg='white', activebackground='#4b5563',
                            padx=30, pady=12, cursor='hand2', command=self.setup_main_screen)
        back_btn.pack(side='left', padx=10)

        start_btn = tk.Button(button_frame, text="Iniciar Protocolo →",
                             font=("Helvetica", 14, "bold"), bg='#10b981', fg='white',
                             activebackground='#059669', padx=30, pady=12, cursor='hand2',
                             command=self.start_calibration)
        start_btn.pack(side='left', padx=10)

        # atualizar rótulo com sensores excluídos
        self.update_excluded_label()

    def ask_num_loops(self):
        val = simpledialog.askinteger(
            "Configuração de Calibração",
            "Quantos ciclos de abertura e fechamento deseja realizar?",
            minvalue=1, maxvalue=60, initialvalue=self.num_loops
        )
        if val:
            self.num_loops = val

    def show_exclude_sensors_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Excluir sensores da calibração")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg='white')
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        tk.Label(frame, text="Marque os sensores que NÃO devem participar da calibração:",
                 bg='white', font=("Helvetica", 12)).pack(pady=(0,10))

        list_frame = tk.Frame(frame, bg='white')
        list_frame.pack(fill='both', expand=True)

        # Variáveis temporárias para a janela de diálogo
        temp_vars = [tk.BooleanVar(value=self.disabled_from_calibration[i]) for i in range(len(SENSOR_NAMES))]

        canvas = tk.Canvas(list_frame, bg='white', highlightthickness=0)
        scb = tk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
        inner = tk.Frame(canvas, bg='white')

        canvas.create_window((0,0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=scb.set)
        canvas.pack(side='left', fill='both', expand=True)
        scb.pack(side='right', fill='y')

        for i, name in enumerate(SENSOR_NAMES):
            chk = tk.Checkbutton(inner, text=f"{i}: {name}", variable=temp_vars[i], bg='white', anchor='w')
            chk.pack(fill='x', padx=10, pady=4)

        inner.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox('all'))

        def apply_and_close():
            for i in range(len(SENSOR_NAMES)):
                self.disabled_from_calibration[i] = bool(temp_vars[i].get())
            self.update_excluded_label()
            dialog.destroy()

        btn_frame = tk.Frame(frame, bg='white')
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Aplicar", command=apply_and_close, bg='#3b82f6', fg='white').pack(side='left', padx=6)
        tk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side='left', padx=6)

    def update_excluded_label(self):
        excluded = [f"{i}:{name}" for i, name in enumerate(SENSOR_NAMES) if self.disabled_from_calibration[i]]
        if excluded:
            text = "Sensores excluídos: " + ", ".join(excluded)
        else:
            text = "Sensores excluídos: Nenhum"
        if hasattr(self, 'excluded_label'):
            self.excluded_label.config(text=text)

    # -------------------------
    # Calibração
    # -------------------------
    def start_calibration(self):
        # se num_loops não setado, pede ao usuário
        if not isinstance(self.num_loops, int) or self.num_loops <= 0:
            self.ask_num_loops()

        self.clear_screen()
        self.calibration_active = True
        self.calibration_count = 0
        self.calibration_max_per_cycle = []
        self.calibration_min_per_cycle = []

        container = tk.Frame(self.root, bg='#f0f4f8')
        container.pack(expand=True, fill='both')

        self.calibration_counter = tk.Label(container, text=f"Calibração 0/{self.num_loops}",
                                           font=("Helvetica", 20, "bold"),
                                           bg='#f0f4f8', fg='#3b82f6')
        self.calibration_counter.pack(pady=20)

        self.calibration_instruction = tk.Label(container, text="",
                                               font=("Helvetica", 32, "bold"),
                                               bg='#f0f4f8', fg='#1a202c', wraplength=800)
        self.calibration_instruction.pack(pady=40)

        self.timer_canvas = tk.Canvas(container, width=400, height=400,
                                      bg='#f0f4f8', highlightthickness=0)
        self.timer_canvas.pack(pady=20)

        progress_frame = tk.Frame(container, bg='#f0f4f8')
        progress_frame.pack(pady=30, fill='x', padx=100)

        self.progress_bar = ttk.Progressbar(progress_frame, length=800,
                                           mode='determinate', maximum=self.num_loops)
        self.progress_bar.pack()
        self.root.after(500, self.calibration_cycle)  # leve atraso para repintura

    def calibration_cycle(self):
        if not self.calibration_active:
            return

        if self.calibration_count >= self.num_loops:
            self.finish_calibration()
            return

        self.calibration_count += 1
        self.calibration_counter.config(text=f"Calibração {self.calibration_count}/{self.num_loops}")
        self.progress_bar['value'] = self.calibration_count

        # Inicializar rastreamento do ciclo atual, ignorando sensores excluídos
        self.current_cycle_max = [0.0 if not self.disabled_from_calibration[i] else 0.0 for i in range(len(SENSOR_NAMES))]
        self.current_cycle_min = [1.0 if not self.disabled_from_calibration[i] else 1.0 for i in range(len(SENSOR_NAMES))]

        self.calibration_instruction.config(text="✋ ABRA A MÃO COMPLETAMENTE", fg='#10b981')
        self.animate_timer(5, '#10b981', lambda: self.close_hand_phase())

    def close_hand_phase(self):
        if not self.calibration_active:
            return
        self.calibration_instruction.config(text="✊ FECHE A MÃO COMPLETAMENTE", fg='#ef4444')
        self.animate_timer(5, '#ef4444', lambda: self.end_cycle())

    def end_cycle(self):
        """Finaliza o ciclo atual e salva os valores máximos e mínimos (ignorando sensores excluídos)"""
        # Guardar apenas valores dos sensores que não foram excluídos
        self.calibration_max_per_cycle.append(self.current_cycle_max[:])
        self.calibration_min_per_cycle.append(self.current_cycle_min[:])

        print(f"Ciclo {self.calibration_count} completo:")
        print(f"  Máximos: {[f'{v:.3f}' for v in self.current_cycle_max]}")
        print(f"  Mínimos: {[f'{v:.3f}' for v in self.current_cycle_min]}")

        # continua para o próximo ciclo
        self.calibration_cycle()

    def animate_timer(self, seconds, color, callback):
        self.timer_canvas.delete('all')
        start_time = 0.0

        def draw_arc(remaining):
            if not self.calibration_active:
                return
            if remaining < 0:
                callback()
                return

            self.timer_canvas.delete('all')
            self.timer_canvas.create_oval(50, 50, 350, 350, outline='#e5e7eb', width=15)

            extent = -(360 * remaining / seconds)
            self.timer_canvas.create_arc(50, 50, 350, 350, start=90, extent=extent,
                                        outline=color, width=15, style='arc')

            self.timer_canvas.create_text(200, 200, text=str(int(remaining) + 1),
                                         font=("Helvetica", 80, "bold"), fill=color)

            # 100ms passo para suavidade
            self.root.after(100, lambda: draw_arc(remaining - 0.1))

        draw_arc(seconds)

    def finish_calibration(self):
        """Calcula as médias dos valores máximos e mínimos e define os thresholds.
           Sensores excluídos permanecem com valores padrão e não influenciam thresholds."""
        self.calibration_active = False

        num_cycles = len(self.calibration_max_per_cycle) or 1

        for i in range(len(SENSOR_NAMES)):
            if self.disabled_from_calibration[i]:
                # manter valores padrões caso excluído da calibração
                continue

            # Média dos valores máximos deste sensor em todos os ciclos
            max_sum = sum(cycle[i] for cycle in self.calibration_max_per_cycle)
            self.sensor_max_values[i] = max_sum / num_cycles

            # Média dos valores mínimos deste sensor em todos os ciclos
            min_sum = sum(cycle[i] for cycle in self.calibration_min_per_cycle)
            self.sensor_min_values[i] = min_sum / num_cycles

            # Threshold é o ponto médio entre max e min
            self.sensor_threshold[i] = (self.sensor_max_values[i] + self.sensor_min_values[i]) / 2.0

        print("\n" + "="*60)
        print("CALIBRAÇÃO CONCLUÍDA - Valores Calculados:")
        print("="*60)
        for i, name in enumerate(SENSOR_NAMES):
            print(f"{name:15} | Max: {self.sensor_max_values[i]:.3f} | "
                  f"Min: {self.sensor_min_values[i]:.3f} | "
                  f"Threshold: {self.sensor_threshold[i]:.3f}")
        print("="*60 + "\n")

        self.show_calibration_results()

    def show_calibration_results(self):
        self.clear_screen()
        container = tk.Frame(self.root, bg='#f0f4f8')
        container.pack(expand=True, fill='both', padx=40, pady=40)

        success_label = tk.Label(container, text="✓ Calibração Concluída!",
                                font=("Helvetica", 36, "bold"), bg='#f0f4f8', fg='#10b981')
        success_label.pack(pady=20)

        info_label = tk.Label(container, text="Valores de calibração calculados com sucesso",
                             font=("Helvetica", 16), bg='#f0f4f8', fg='#4a5568')
        info_label.pack(pady=10)

        results_frame = tk.Frame(container, bg='white', relief='raised', borderwidth=2)
        results_frame.pack(pady=30, padx=50, fill='both', expand=True)

        results_title = tk.Label(results_frame, text="Valores Calibrados",
                                font=("Helvetica", 18, "bold"), bg='white')
        results_title.pack(pady=15)

        canvas = tk.Canvas(results_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=canvas.yview)
        results_inner = tk.Frame(canvas, bg='white')

        canvas.create_window((0, 0), window=results_inner, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True, padx=20, pady=10)
        scrollbar.pack(side='right', fill='y')

        for i, name in enumerate(SENSOR_NAMES):
            sensor_frame = tk.Frame(results_inner, bg='#f8fafc', relief='groove', borderwidth=1)
            sensor_frame.pack(fill='x', padx=10, pady=5)

            name_label = tk.Label(sensor_frame, text=f"{name}:", 
                                 font=("Courier", 11, "bold"), bg='#f8fafc', anchor='w', width=20)
            name_label.pack(side='left', padx=10, pady=8)

            values_text = f"Max: {self.sensor_max_values[i]:.3f}  |  Min: {self.sensor_min_values[i]:.3f}  |  Threshold: {self.sensor_threshold[i]:.3f}"
            values_label = tk.Label(sensor_frame, text=values_text,
                                   font=("Courier", 10), bg='#f8fafc', anchor='w')
            values_label.pack(side='left', padx=10, pady=8)

        results_inner.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox('all'))

        continue_btn = tk.Button(container, text="Iniciar Detecção de Gestos →",
                                font=("Helvetica", 14, "bold"), bg='#3b82f6', fg='white',
                                activebackground='#2563eb', padx=40, pady=15,
                                cursor='hand2', command=self.start_feedback_screen)
        continue_btn.pack(pady=20)

    # -------------------------
    # Tela de feedback (visualização do movimento)
    # -------------------------
    def start_feedback_screen(self):
        self.clear_screen()
        self.feedback_active = True

        container = tk.Frame(self.root, bg='#f0f4f8')
        container.pack(expand=True, fill='both', padx=20, pady=20)

        title_frame = tk.Frame(container, bg='white', relief='raised', borderwidth=2)
        title_frame.pack(fill='x', pady=(0, 20))

        title = tk.Label(title_frame, text="Detecção de Gestos em Tempo Real",
                        font=("Helvetica", 22, "bold"), bg='white', fg='#1a202c')
        title.pack(pady=15)

        main_layout = tk.Frame(container, bg='#f0f4f8')
        main_layout.pack(expand=True, fill='both')

        # Coluna esquerda - Imagem do gesto
        left_col = tk.Frame(main_layout, bg='white', relief='raised', borderwidth=2)
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 10))

        gesture_title = tk.Label(left_col, text="Gesto Detectado",
                                font=("Helvetica", 18, "bold"), bg='white', fg='#1a202c')
        gesture_title.pack(pady=15)

        self.image_label = tk.Label(left_col, bg='white')
        self.image_label.pack(pady=20, expand=True)

        self.gesture_id_label = tk.Label(left_col, text="Gesto: -",
                                        font=("Helvetica", 24, "bold"), bg='white', fg='#3b82f6')
        self.gesture_id_label.pack(pady=15)

        # Coluna central - Valores dos sensores
        right_col = tk.Frame(main_layout, bg='white', relief='raised', borderwidth=2)
        right_col.pack(side='left', fill='both', expand=True, padx=(10, 0))

        sensor_title = tk.Label(right_col, text="Estado dos Sensores",
                               font=("Helvetica", 16, "bold"), bg='white')
        sensor_title.pack(pady=10)

        legend_frame = tk.Frame(right_col, bg='#f0f4f8', relief='flat')
        legend_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(legend_frame, text="🟢 Aberto (< threshold)  |  🔴 Fechado (≥ threshold)  |  ◼️ Desabilitado",
                font=("Helvetica", 10), bg='#f0f4f8').pack()

        sensor_canvas = tk.Canvas(right_col, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_col, orient='vertical', command=sensor_canvas.yview)
        sensor_frame = tk.Frame(sensor_canvas, bg='white')

        sensor_canvas.create_window((0, 0), window=sensor_frame, anchor='nw')
        sensor_canvas.configure(yscrollcommand=scrollbar.set)

        sensor_canvas.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y')

        self.sensor_labels = []
        self.sensor_state_labels = []

        for i, name in enumerate(SENSOR_NAMES):
            frame = tk.Frame(sensor_frame, bg='white')
            frame.pack(fill='x', pady=3, padx=5)

            label = tk.Label(frame, text=f"{name}: -",
                           font=("Courier", 10), bg='white', anchor='w', width=45)
            label.pack(side='left')

            state_label = tk.Label(frame, text="⚪",
                                  font=("Helvetica", 14), bg='white', width=4)
            state_label.pack(side='left', padx=5)

            self.sensor_labels.append(label)
            self.sensor_state_labels.append(state_label)

        sensor_frame.update_idletasks()
        sensor_canvas.configure(scrollregion=sensor_canvas.bbox('all'))

        # Coluna direita (painel) - controles rápidos: checkboxes para desabilitar sensores durante a visualização
        side_panel = tk.Frame(main_layout, bg='#f8fafc', relief='raised', borderwidth=2, width=280)
        side_panel.pack(side='left', fill='y', padx=(10, 0))

        tk.Label(side_panel, text="Controles", font=("Helvetica", 14, "bold"), bg='#f8fafc').pack(pady=10)
        tk.Label(side_panel, text="Desmarque para DESABILITAR sensor durante a visualização:",
                 bg='#f8fafc', font=("Helvetica", 9), wraplength=240, justify='left').pack(padx=8)

        chk_frame = tk.Frame(side_panel, bg='#f8fafc')
        chk_frame.pack(fill='both', expand=True, padx=8, pady=6)

        chk_canvas = tk.Canvas(chk_frame, bg='#f8fafc', highlightthickness=0)
        chk_scb = tk.Scrollbar(chk_frame, orient='vertical', command=chk_canvas.yview)
        chk_inner = tk.Frame(chk_canvas, bg='#f8fafc')

        chk_canvas.create_window((0,0), window=chk_inner, anchor='nw')
        chk_canvas.configure(yscrollcommand=chk_scb.set)
        chk_canvas.pack(side='left', fill='both', expand=True)
        chk_scb.pack(side='right', fill='y')

        for i, name in enumerate(SENSOR_NAMES):
            cb = tk.Checkbutton(chk_inner, text=f"{i}: {name}", variable=self.active_sensors[i],
                                onvalue=True, offvalue=False, bg='#f8fafc', anchor='w')
            cb.pack(fill='x', padx=6, pady=2)

        chk_inner.update_idletasks()
        chk_canvas.configure(scrollregion=chk_canvas.bbox('all'))

        # Botões de controle da sessão
        finish_btn = tk.Button(container, text="Finalizar Sessão",
                              font=("Helvetica", 14, "bold"), bg='#ef4444', fg='white',
                              activebackground='#dc2626', padx=30, pady=12,
                              cursor='hand2', command=self.finish_session)
        finish_btn.pack(pady=20)

    def finish_session(self):
        self.feedback_active = False
        messagebox.showinfo("Sessão Finalizada", "Sessão encerrada com sucesso!")
        self.setup_main_screen()

    # -------------------------
    # Processamento de dados recebidos
    # -------------------------
    def process_data(self):
        try:
            while True:
                data_string = self.data_queue.get_nowait()
                data_list = data_string.split(',')

                # formato esperado: gesture_id, s0, s1, ..., sN
                if len(data_list) != len(SENSOR_NAMES) + 1:
                    # descartamos linhas com formato inválido
                    continue

                try:
                    gesture_id = int(data_list[0])
                    sensor_values = [float(v) for v in data_list[1:]]
                except Exception:
                    continue

                # Remoção simples de artefatos (buffer + substituição por média se outlier)
                sensor_values = self.remove_artifacts(sensor_values)

                if self.calibration_active:
                    self.update_calibration_values(sensor_values)

                if self.feedback_active:
                    self.update_feedback(gesture_id, sensor_values)
        except queue.Empty:
            pass
        finally:
            # chama novamente periodicamente
            self.root.after(50, self.process_data)

    # -------------------------
    # Remoção de artefatos (média móvel + detecção de outliers)
    # -------------------------
    def remove_artifacts(self, sensor_values, window=None, threshold=None):
        """Mantém um buffer por sensor e substitui valores muito discrepantes pela média do buffer."""
        if window is None:
            window = self.artifact_window
        if threshold is None:
            threshold = self.artifact_threshold

        cleaned = []
        for i, val in enumerate(sensor_values):
            buf = self._artifact_buffer[i]
            buf.append(val)
            if len(buf) > window:
                buf.pop(0)
            mean_val = sum(buf) / len(buf) if buf else val

            # Se valor atual é um outlier comparado à média do buffer, substitui pela média
            if len(buf) >= 2 and abs(val - mean_val) > threshold:
                cleaned.append(mean_val)
            else:
                cleaned.append(val)
        return cleaned

    # -------------------------
    # Atualização de calibração
    # -------------------------
    def update_calibration_values(self, sensor_values):
        """Atualiza máximos e mínimos do ciclo atual, ignorando sensores excluídos."""
        if self.current_cycle_max is None or self.current_cycle_min is None:
            return

        for i, value in enumerate(sensor_values):
            if self.disabled_from_calibration[i]:
                continue
            # Atualizar máximo do ciclo atual
            if value > self.current_cycle_max[i]:
                self.current_cycle_max[i] = value
            # Atualizar mínimo do ciclo atual
            if value < self.current_cycle_min[i]:
                self.current_cycle_min[i] = value

    # -------------------------
    # Atualização de feedback (visual)
    # -------------------------
    def update_feedback(self, gesture_id, sensor_values):
        """Atualiza a interface com a imagem do gesto e o estado dos sensores.
           Sensores desmarcados em self.active_sensors são mostrados como DESABILITADOS."""
        # Atualizar imagem do gesto (se houver)
        image = self.images.get(gesture_id, self.images.get(-1))
        if image:
            self.image_label.config(image=image)
            self.image_label.image = image

        self.gesture_id_label.config(text=f"Gesto: {gesture_id}")

        for i, value in enumerate(sensor_values):
            if i >= len(self.sensor_labels):
                continue

            # Se sensor estiver desabilitado pelo usuário durante a visualização
            if not self.active_sensors[i].get():
                text = f"{SENSOR_NAMES[i]}: ◼️ DESABILITADO"
                self.sensor_labels[i].config(text=text, fg='#6b7280')
                self.sensor_state_labels[i].config(text="◼️")
                # Não alteramos finger_states nem thresholds
                continue

            # Caso sensor esteja ativo: comparar com threshold (threshold pode ter sido mantido/default se excluído na calibração)
            thresh = self.sensor_threshold[i]
            if value >= thresh:
                state = "FECHADO"
                color = '#ef4444'
                emoji = "🔴"
                self.finger_states[i] = True
            else:
                state = "ABERTO"
                color = '#10b981'
                emoji = "🟢"
                self.finger_states[i] = False

            text = f"{SENSOR_NAMES[i]}: {value:.3f} (T:{thresh:.3f}) {state}"
            self.sensor_labels[i].config(text=text, fg=color)
            self.sensor_state_labels[i].config(text=emoji)

    # -------------------------
    # Gerenciamento da conexão com o executável
    # -------------------------
    def start_connection(self):

        print("\n========================")
        print(" [ClinicalGloveApp] Iniciando conexão com a luva…")
        print("========================")

        # 1 — Mostra a porta configurada
        print(f"[ClinicalGloveApp] Porta configurada: {GLOVE_CONNECTION_PORT}")
        print("[ClinicalGloveApp] Testando porta informada…")

        try:
            test = subprocess.run(
                [PATH_TO_C_EXE, GLOVE_CONNECTION_PORT],
                capture_output=True,
                text=True,
                timeout=2
            )

            print("[TEST STDOUT]")
            print(test.stdout.strip())
            print("[TEST STDERR]")
            print(test.stderr.strip())

            if "falhou" in test.stdout.lower() or "error" in test.stdout.lower():
                print("\n[ERRO] O executável NÃO conseguiu abrir essa porta!")
                print("Conexão cancelada.\n")
                return

        except subprocess.TimeoutExpired:
            print("[INFO] O executável está rodando (timeout normal).")

        # 3 — Verifica se o executável existe
        if not os.path.exists(PATH_TO_C_EXE):
            print(f"[ERRO] Executável não encontrado: {PATH_TO_C_EXE}")
            print("       Conexão cancelada.\n")
            return
        else:
            print(f"[OK] Executável encontrado: {PATH_TO_C_EXE}")

        # 4 — Evita múltiplas threads
        if self.c_thread and self.c_thread.is_alive():
            print("[ClinicalGloveApp] A thread de comunicação já está rodando.")
            return

        print("[ClinicalGloveApp] Iniciando thread de leitura…")

        # 5 — Inicia thread da luva
        try:
            self.c_thread = threading.Thread(
                target=read_from_glove_thread,
                args=(self.data_queue, self.status_queue, PATH_TO_C_EXE, GLOVE_CONNECTION_PORT),
                daemon=True
            )
            self.c_thread.start()
            print("[OK] Thread de comunicação iniciada.\n")
        except Exception as e:
            print("[ERRO] Falha ao iniciar a thread de comunicação:", e)
            print(" Conexão abortada.\n")


    def check_status(self):
        try:
            while True:
                status = self.status_queue.get_nowait()

                print(f"[ClinicalGloveApp] STATUS RECEBIDO → {status}")

                if status == "connected":
                    print("[OK] Luva conectada na porta informada.")
                    self.glove_connected = True
                    self.led_canvas.itemconfig(self.led_indicator, fill='#10b981', outline='#059669')
                    self.status_text.config(text="Conectado", fg='#10b981')
                    if hasattr(self, 'start_calibration_btn'):
                        self.start_calibration_btn.config(state='normal')

                elif status == "disconnected":
                    print("[WARN] A luva desconectou. O executável foi encerrado.")
                    self.glove_connected = False
                    self.led_canvas.itemconfig(self.led_indicator, fill='#ef4444', outline='#dc2626')
                    self.status_text.config(text="Desconectado", fg='#ef4444')
                    if hasattr(self, 'start_calibration_btn'):
                        self.start_calibration_btn.config(state='disabled')

                elif status.startswith("error"):
                    print("[ERRO] Ocorreu um erro no processo da luva!")
                    print("      Detalhes:", status)
                    self.glove_connected = False
                    self.led_canvas.itemconfig(self.led_indicator, fill='#ef4444', outline='#dc2626')
                    self.status_text.config(text="Erro na conexão", fg='#ef4444')
                    if hasattr(self, 'start_calibration_btn'):
                        self.start_calibration_btn.config(state='disabled')

        except queue.Empty:
            pass
        finally:
            self.root.after(200, self.check_status)

    # -------------------------
    # Utilitários de interface
    # -------------------------
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def on_closing(self):
        # encerra loops e fecha
        self.feedback_active = False
        self.calibration_active = False
        self.root.destroy()


# ============================================================
# PONTO DE ENTRADA
# ============================================================
if __name__ == "__main__":
    if not os.path.exists(IMAGES_FOLDER):
        print(f"AVISO: A pasta '{IMAGES_FOLDER}' não foi encontrada.")
        print("O sistema funcionará, mas sem imagens de gestos.")

    root = tk.Tk()
    app = ClinicalGloveApp(root)
    root.mainloop()



