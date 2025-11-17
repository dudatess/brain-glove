# core/calibration.py

import time


class CalibrationManager:
    """
    Gerencia toda a calibração da luva 5DT.
    Suporta:
        - Calibração contínua
        - Calibração por ciclos
        - Seleção de sensores
        - Número de ciclos e duração configuráveis
        - Registro estruturado de min/max por ciclo
        - Threshold automático
        - Eventos de status (para GUI ou cycle_control)
    """

    def __init__(self, sensor_names, disabled_mask=None):
        self.sensor_names = sensor_names
        self.disabled_mask = disabled_mask or [False] * len(sensor_names)

        # Modo de operação: "continuous" ou "cycles"
        self.mode = "cycles"

        # Parâmetros de ciclos
        self.num_cycles = 10
        self.cycle_duration = 4.0

        # Callbacks (opcionais)
        self.on_cycle_start = None
        self.on_cycle_finish = None
        self.on_calibration_finish = None
        self.on_continuous_update = None

        # Dados
        self.reset()

    # -----------------------------------------------------
    def reset(self):
        """Reseta variáveis internas."""
        self.current_cycle = 0
        self.cycle_start_time = None

        self.current_max = None
        self.current_min = None

        self.max_per_cycle = []
        self.min_per_cycle = []
        self.cycle_metadata = []  # <-- NOVO

        # Valores globais
        n = len(self.sensor_names)
        self.sensor_max_values = [0.0] * n
        self.sensor_min_values = [1.0] * n
        self.sensor_thresholds = [0.5] * n

    # -----------------------------------------------------
    # CONFIGURAÇÃO
    # -----------------------------------------------------
    def set_mode(self, mode: str):
        assert mode in ("continuous", "cycles")
        self.mode = mode

    def set_cycle_parameters(self, num_cycles: int, cycle_duration: float):
        self.num_cycles = num_cycles
        self.cycle_duration = cycle_duration

    def set_disabled_sensors(self, disabled_mask):
        self.disabled_mask = disabled_mask

    # -----------------------------------------------------
    # CICLO
    # -----------------------------------------------------
    def start_cycle(self):
        """Inicia um ciclo (modo ciclos)."""
        self.current_cycle += 1
        self.cycle_start_time = time.time()

        n = len(self.sensor_names)
        self.current_max = [0.0] * n
        self.current_min = [1.0] * n

        if self.on_cycle_start:
            self.on_cycle_start(self.current_cycle)

    def cycle_active(self):
        """Retorna True se o ciclo ainda está rodando."""
        if self.cycle_start_time is None:
            return False
        return (time.time() - self.cycle_start_time) < self.cycle_duration

    # -----------------------------------------------------
    # ATUALIZAÇÃO DE VALORES
    # -----------------------------------------------------
    def update(self, values):
        """Atualiza min/max dependendo do modo."""
        if self.mode == "continuous":
            self._update_continuous(values)
        else:
            self._update_cycle(values)

    def _update_cycle(self, values):
        for i, val in enumerate(values):
            if self.disabled_mask[i]:
                continue

            if val > self.current_max[i]:
                self.current_max[i] = val

            if val < self.current_min[i]:
                self.current_min[i] = val

    def _update_continuous(self, values):
        for i, val in enumerate(values):
            if self.disabled_mask[i]:
                continue

            if val > self.sensor_max_values[i]:
                self.sensor_max_values[i] = val

            if val < self.sensor_min_values[i]:
                self.sensor_min_values[i] = val

        if self.on_continuous_update:
            self.on_continuous_update(self.sensor_min_values, self.sensor_max_values)

    # -----------------------------------------------------
    # FINALIZAÇÃO DE CICLO
    # -----------------------------------------------------
    def finalize_cycle(self):
        """Salva dados de um ciclo e limpa estado."""
        if self.current_max is None:
            return

        self.max_per_cycle.append(self.current_max[:])
        self.min_per_cycle.append(self.current_min[:])

        self.cycle_metadata.append({
            "cycle_index": self.current_cycle,
            "start_time": self.cycle_start_time,
            "end_time": time.time(),
            "duration": time.time() - self.cycle_start_time,
        })

        if self.on_cycle_finish:
            self.on_cycle_finish(self.current_cycle)

    def cycles_completed(self):
        return self.current_cycle >= self.num_cycles

    # -----------------------------------------------------
    # RESULTADOS FINAIS
    # -----------------------------------------------------
    def compute_thresholds(self):
        if self.mode == "continuous":
            for i in range(len(self.sensor_names)):
                if self.disabled_mask[i]:
                    continue
                self.sensor_thresholds[i] = (
                    self.sensor_max_values[i] + self.sensor_min_values[i]
                ) / 2
            return self.sensor_thresholds

        # Modo ciclos
        num = max(len(self.max_per_cycle), 1)
        for i in range(len(self.sensor_names)):
            if self.disabled_mask[i]:
                continue
            mx = sum(c[i] for c in self.max_per_cycle) / num
            mn = sum(c[i] for c in self.min_per_cycle) / num
            self.sensor_max_values[i] = mx
            self.sensor_min_values[i] = mn
            self.sensor_thresholds[i] = (mx + mn) / 2

        if self.on_calibration_finish:
            self.on_calibration_finish()

        return self.sensor_thresholds

    # -----------------------------------------------------
    # EXPORTAÇÃO
    # -----------------------------------------------------
    def get_export_data(self):
        """Dados formatados para JSON/CSV."""
        return {
            "mode": self.mode,
            "num_cycles": self.num_cycles,
            "cycle_duration": self.cycle_duration,
            "sensor_max": self.sensor_max_values,
            "sensor_min": self.sensor_min_values,
            "sensor_thresholds": self.sensor_thresholds,
            "raw_cycles_max": self.max_per_cycle,
            "raw_cycles_min": self.min_per_cycle,
            "cycle_metadata": self.cycle_metadata,
            "disabled_sensors": self.disabled_mask,
        }
