import cv2
import time

class CameraProcessor:
    def __init__(self, camera_id, rtsp_url, rtt_monitor, local_detector, remote_detector):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.rtt_monitor = rtt_monitor
        self.local_detector = local_detector
        self.remote_detector = remote_detector
        self.frame = None

    def start(self):
        import threading
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print(f"[{self.camera_id}] Erro ao abrir câmera.")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            rtt = self.rtt_monitor.get_rtt()
            use_local = rtt > 0.05

            try:
                if use_local:
                    result = self.local_detector.detect(frame)
                else:
                    result = self.remote_detector.detect(frame)

                if result:
                    x1, y1, x2, y2, plate_text = result
                    color = (255, 0, 0) if use_local else (0, 255, 0)
                    cv2.putText(frame, f"{self.camera_id} - Placa: {plate_text}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            except Exception as e:
                print(f"[{self.camera_id}] Erro: {e}")

            self.frame = cv2.resize(frame, (640, 360))
            time.sleep(0.033)

