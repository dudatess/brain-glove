# core/data_processing.py
import queue

class DataProcessor:
    def __init__(self, sensor_count, window=5, threshold=0.15):
        self.sensor_count = sensor_count
        self.buffers = [[] for _ in range(sensor_count)]
        self.window = window
        self.threshold = threshold

    def clean_values(self, sensor_values):
        cleaned = []
        for i, val in enumerate(sensor_values):
            buf = self.buffers[i]
            buf.append(val)
            if len(buf) > self.window:
                buf.pop(0)
            mean_val = sum(buf) / len(buf) if buf else val
            if abs(val - mean_val) > self.threshold and len(buf) >= 2:
                cleaned.append(mean_val)
            else:
                cleaned.append(val)
        return cleaned

    def parse_packet(self, data_string, sensor_names):
        data_list = data_string.split(',')
        if len(data_list) != len(sensor_names) + 1:
            return None, None
        try:
            gesture_id = int(data_list[0])
            sensor_values = [float(v) for v in data_list[1:]]
            return gesture_id, sensor_values
        except ValueError:
            return None, None
