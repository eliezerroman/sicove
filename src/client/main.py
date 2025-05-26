import cv2
import threading
from src.client.local_inference import LocalPlateDetector
from src.client.remote_inference import RemotePlateDetector
from src.monitoring.network_monitor import NetworkMonitor  # Atualizado
from src.client.camera_handler import CameraProcessor

RTSP_STREAMS = {
    "cam1": "rtsp://admin:sicove2025@192.168.15.9:554/onvif2",
    "cam2": "rtsp://admin:sicove2025@192.168.15.26:554/onvif2"
}

def main():
    # Iniciar o monitoramento de rede
    network_monitor = NetworkMonitor(host="192.168.15.1", interval=1, status_file="src/monitoring/network_status.json")
    threading.Thread(target=network_monitor.start, daemon=True).start()

    #local_detector = LocalPlateDetector("models/nano.pt")
    ##remote_detector = RemotePlateDetector()

    cameras = []
    for cam_id, rtsp in RTSP_STREAMS.items():
        local_detector = LocalPlateDetector("models/nano.pt")
        remote_detector = RemotePlateDetector()
        cam = CameraProcessor(cam_id, rtsp, local_detector, remote_detector)
        cam.start()
        cameras.append(cam)


    cv2.namedWindow("Placas", cv2.WINDOW_NORMAL)
    while True:
        frames = [cam.frame for cam in cameras if cam.frame is not None]
        if len(frames) == len(cameras):
            combined = cv2.hconcat(frames)
            cv2.imshow("Placas", combined)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
