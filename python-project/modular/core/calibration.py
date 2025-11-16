# core/calibration.py

class CalibrationManager:
    def __init__(self, sensor_names, disabled_mask=None):
        self.sensor_names = sensor_names
        self.disabled_mask = disabled_mask or [False] * len(sensor_names)
        self.reset()

    def reset(self):
        self.num_loops = 10
        self.calibration_count = 0
        self.max_per_cycle = []
        self.min_per_cycle = []
        self.current_max = None
        self.current_min = None
        self.sensor_max_values = [0.0] * len(self.sensor_names)
        self.sensor_min_values = [1.0] * len(self.sensor_names)
        self.sensor_thresholds = [0.5] * len(self.sensor_names)

    def start_cycle(self):
        self.current_max = [0.0 for _ in self.sensor_names]
        self.current_min = [1.0 for _ in self.sensor_names]

    def update_cycle(self, values):
        for i, val in enumerate(values):
            if self.disabled_mask[i]:
                continue
            if val > self.current_max[i]:
                self.current_max[i] = val
            if val < self.current_min[i]:
                self.current_min[i] = val

    def finalize_cycle(self):
        self.max_per_cycle.append(self.current_max[:])
        self.min_per_cycle.append(self.current_min[:])

    def compute_thresholds(self):
        num_cycles = max(len(self.max_per_cycle), 1)
        for i, name in enumerate(self.sensor_names):
            if self.disabled_mask[i]:
                continue
            max_mean = sum(c[i] for c in self.max_per_cycle) / num_cycles
            min_mean = sum(c[i] for c in self.min_per_cycle) / num_cycles
            self.sensor_max_values[i] = max_mean
            self.sensor_min_values[i] = min_mean
            self.sensor_thresholds[i] = (max_mean + min_mean) / 2.0
        return self.sensor_thresholds
