import cv2
import time
import json
import threading
import re
from src.data.history_manager import PlateHistory

class CameraProcessor:
    def __init__(self, camera_id, rtsp_url, local_detector, remote_detector, network_status_file_path="src/monitoring/network_status.json"):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.local_detector = local_detector
        self.remote_detector = remote_detector
        self.history_manager = PlateHistory()
        self.network_status_file_path = network_status_file_path
        self.frame = None
        self.last_detection_result = None
        self.last_detection_time = 0
        self.detection_timeout = 0.5

        self.is_local_detecting = False
        self.is_remote_detecting = False

        self.running = False
        self.cap = None
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        print(f"[{self.camera_id}] Encerrando câmera...")
        self.running = False
        if self.cap is not None:
            self.cap.release()
        if self.thread is not None:
            self.thread.join(timeout=2)
        print(f"[{self.camera_id}] Câmera encerrada.")

    def is_valid_brazilian_plate(self, plate: str) -> bool:
        # Remove tudo que não for letra ou número
        plate = re.sub(r'[^A-Za-z0-9]', '', plate.upper())
        # Expressões regulares para os dois formatos de placa válidos
        padrao_mercosul = re.fullmatch(r"[A-Z]{3}[0-9][A-Z][0-9]{2}", plate)
        padrao_antigo = re.fullmatch(r"[A-Z]{3}[0-9]{4}", plate)
        return bool(padrao_mercosul or padrao_antigo)
    
    def clear_plate(self, plate):
        plate = re.sub(r'[^A-Za-z0-9]', '', plate.upper())
        return plate
        

    def _load_network_status(self):
        try:
            with open(self.network_status_file_path, "r") as f:
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
                self.last_detection_time = time.time()
        except Exception as e:
            print(f"[{self.camera_id}] Erro na detecção {'local' if use_local else 'remota'}: {e}")
        finally:
            if use_local:
                self.is_local_detecting = False
            else:
                self.is_remote_detecting = False

    def _run(self):
        self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        if not self.cap.isOpened():
            print(f"[{self.camera_id}] Erro ao abrir câmera.")
            return

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            rtt_ms, throughput_mbps = self._load_network_status()
            use_local = rtt_ms > 18 or throughput_mbps < 2_000

            if use_local and not self.is_local_detecting:
                self.is_local_detecting = True
                threading.Thread(target=self._async_detect, args=(frame.copy(), True), daemon=True).start()
            elif not use_local and not self.is_remote_detecting:
                self.is_remote_detecting = True
                threading.Thread(target=self._async_detect, args=(frame.copy(), False), daemon=True).start()

            if self.last_detection_result and (time.time() - self.last_detection_time < self.detection_timeout):
                try:
                    (x1, y1, x2, y2, plate_text), result_was_local = self.last_detection_result
                    color = (255, 0, 0) if result_was_local else (0, 255, 0)
                    if self.is_valid_brazilian_plate(plate_text):
                        clean_plate_text = self.clear_plate(plate_text)
                        cv2.putText(frame, f"{self.camera_id} - Placa: {clean_plate_text}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                        self.history_manager.add_entry(clean_plate_text, self.camera_id)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                except Exception as e:
                    print(f"[{self.camera_id}] Erro ao desenhar resultado: {e}")

            self.frame = cv2.resize(frame, (640, 360))
            time.sleep(0.033)  # 30 FPS aproximado
