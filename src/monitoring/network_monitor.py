# monitoring/network_monitor.py

import threading
import json
import time
from src.monitoring.rtt_monitor import RTTMonitor
from src.monitoring.throughput_monitor import ThroughputMonitor

class NetworkMonitor:
    def __init__(self, host, interval, status_file="src/monitoring/network_status.json"):
        self.rtt_monitor = RTTMonitor(host=host, interval=interval)
        self.throughput_monitor = ThroughputMonitor(host="127.0.0.1")
        self.interval = interval
        self.status_file = status_file
        self.lock = threading.Lock()

    def start(self):
        self.rtt_monitor.start()
        thread = threading.Thread(target=self._run_throughput_monitor, daemon=True)
        thread.start()

    def _run_throughput_monitor(self):
        while True:
            self.throughput_monitor.measure()
            self._save_status()
            time.sleep(self.interval)

    def _save_status(self):
        with self.lock:
            data = {
                "rtt_ms": self.rtt_monitor.get_rtt(),
                "throughput_mbps": self.throughput_monitor.get_throughput()
            }
            try:
                with open(self.status_file, "w") as f:
                    json.dump(data, f)
            except Exception as e:
                print(f"[MONITOR] Erro ao salvar JSON: {e}")
