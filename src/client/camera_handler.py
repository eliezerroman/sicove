import cv2
import time
import json
import threading

class CameraProcessor:
    def __init__(self, camera_id, rtsp_url, local_detector, remote_detector, status_file="src/monitoring/network_status.json"):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.local_detector = local_detector
        self.remote_detector = remote_detector
        self.status_file = status_file
        self.frame = None
        self.last_detection_result = None

        # Flags para evitar múltiplas threads simultâneas
        self.is_local_detecting = False
        self.is_remote_detecting = False

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _load_network_status(self):
        try:
            with open(self.status_file, "r") as f:
                data = json.load(f)
                rtt_ms = data.get("rtt_ms", 999.0)
                throughput_mbps = data.get("throughput_mbps", 0.0)
                return rtt_ms, throughput_mbps
        except Exception as e:
            print(f"[{self.camera_id}] Erro ao ler status de rede: {e}")
            return 999.0, 0.0

    def _async_detect(self, frame, use_local):
        try:
            if use_local:
                result = self.local_detector.detect(frame)
            else:
                result = self.remote_detector.detect(frame)

            if result:
                self.last_detection_result = (result, use_local)
        except Exception as e:
            print(f"[{self.camera_id}] Erro na detecção {'local' if use_local else 'remota'}: {e}")
        finally:
            if use_local:
                self.is_local_detecting = False
            else:
                self.is_remote_detecting = False

    def _run(self):
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print(f"[{self.camera_id}] Erro ao abrir câmera.")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            rtt_ms, throughput_mbps = self._load_network_status()
            use_local = rtt_ms > 18 or throughput_mbps < 5_000

            # Inicia a detecção assíncrona se ainda não estiver em andamento
            if use_local and not self.is_local_detecting:
                self.is_local_detecting = True
                threading.Thread(target=self._async_detect, args=(frame.copy(), True), daemon=True).start()
            elif not use_local and not self.is_remote_detecting:
                self.is_remote_detecting = True
                threading.Thread(target=self._async_detect, args=(frame.copy(), False), daemon=True).start()

            # Desenha última detecção válida
            if self.last_detection_result:
                try:
                    (x1, y1, x2, y2, plate_text), result_was_local = self.last_detection_result
                    color = (255, 0, 0) if result_was_local else (0, 255, 0)
                    cv2.putText(frame, f"{self.camera_id} - Placa: {plate_text}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                except Exception as e:
                    print(f"[{self.camera_id}] Erro ao desenhar resultado: {e}")

            self.frame = cv2.resize(frame, (640, 360))
            # time.sleep(0.033)  # Se quiser limitar o FPS
