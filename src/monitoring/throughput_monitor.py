import socket
import time

class ThroughputMonitor:
    def __init__(self, host, port=5001, duration=1.0, payload_size=1400):
        self.host = host
        self.port = port
        self.duration = duration
        self.payload_size = payload_size
        self.throughput_mbps = 0.0

    def measure(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                payload = b'x' * self.payload_size

                start_time = time.time()
                end_time = start_time + self.duration
                sent_bytes = 0

                while time.time() < end_time:
                    s.sendall(payload)
                    sent_bytes += len(payload)

                s.shutdown(socket.SHUT_WR)

                data = s.recv(1024)
                end_time = time.time()

                bytes_received = int(data.decode())
                duration = end_time - start_time

                self.throughput_mbps = (bytes_received * 8) / (duration * 1_000_000)
                #print(f"[THROUGHPUT] {self.throughput_mbps:.3f} Mbps")
        except Exception as e:
            print(f"[THROUGHPUT] Erro: {e}")

    def get_throughput(self):
        return self.throughput_mbps
