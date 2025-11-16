# ================================================================
# glove_thread.py
# Comunicação assíncrona com a luva 5DT via subprocesso externo
# ================================================================

import subprocess
import threading
import queue
import time
import os
import sys

# Taxa de amostragem padrão (em Hz)
DEFAULT_SAMPLING_RATE = 60

class GloveReaderThread(threading.Thread):
    """
    Thread dedicada para leitura contínua dos dados da luva.
    Gerencia reconexão automática, eventos de status e taxa de amostragem.
    """

    def __init__(self, output_queue: queue.Queue, status_queue: queue.Queue,
                 c_exe_path: str, glove_port: str, sampling_rate: int = DEFAULT_SAMPLING_RATE):
        super().__init__(daemon=True)
        self.output_queue = output_queue
        self.status_queue = status_queue
        self.c_exe_path = c_exe_path
        self.glove_port = glove_port
        self.sampling_rate = sampling_rate
        self._stop_event = threading.Event()
        self._process = None
        self._last_status = None

    # ============================================================
    # Thread principal
    # ============================================================
    def run(self):
        while not self._stop_event.is_set():
            try:
                # --- Tenta iniciar comunicação com o executável C ---
                if not os.path.exists(self.c_exe_path):
                    self._update_status("error_not_found")
                    time.sleep(2)
                    continue

                self._process = subprocess.Popen(
                    [self.c_exe_path, self.glove_port],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )

                self._update_status("connected")

                # --- Loop de leitura contínua ---
                while not self._stop_event.is_set():
                    start_time = time.time()

                    output_line = self._process.stdout.readline()
                    if not output_line:
                        # Processo finalizado inesperadamente
                        self._update_status("disconnected")
                        break

                    self.output_queue.put(output_line.strip())

                    # Controle da taxa de amostragem (Hz)
                    elapsed = time.time() - start_time
                    sleep_time = max(0, (1 / self.sampling_rate) - elapsed)
                    time.sleep(sleep_time)

            except FileNotFoundError:
                self._update_status("error_not_found")

            except Exception as e:
                self._update_status(f"error_{str(e)}")

            finally:
                # Finaliza processo e aguarda antes de tentar reconectar
                self._terminate_process()
                if not self._stop_event.is_set():
                    time.sleep(2)  # Espera antes de reconectar

    # ============================================================
    # Controle de status e reconexão
    # ============================================================
    def _update_status(self, new_status: str):
        """Evita repetição de mensagens de status."""
        if new_status != self._last_status:
            self.status_queue.put(new_status)
            self._last_status = new_status

    def _terminate_process(self):
        """Finaliza o processo C de forma segura."""
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=2)
            except Exception:
                pass
        self._process = None

    # ============================================================
    # Métodos públicos de controle
    # ============================================================
    def stop(self):
        """Encerra a thread e o processo."""
        self._stop_event.set()
        self._terminate_process()
        self._update_status("stopped")

    def is_running(self) -> bool:
        return not self._stop_event.is_set()
