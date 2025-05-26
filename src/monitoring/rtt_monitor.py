# monitoring/rtt_monitor.py

import subprocess
import time
import threading

class RTTMonitor:
    def __init__(self, host, interval=1):
        self.host = host
        self.interval = interval
        self.rtt = 0.0
        self.lock = threading.Lock()

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        while True:
            try:
                result = subprocess.run(["ping", "-c", "1", self.host],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        timeout=2)
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if "time=" in line:
                            time_str = line.split("time=")[1].split(" ")[0]
                            with self.lock:
                                self.rtt = float(time_str)
                            #print(f"[RTT] {self.rtt:.2f} ms")
            except Exception as e:
                print(f"[RTT] Erro: {e}")
            time.sleep(self.interval)

    def get_rtt(self):
        with self.lock:
            return self.rtt
