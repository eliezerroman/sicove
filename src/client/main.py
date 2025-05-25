import cv2
from src.client.local_inference import LocalPlateDetector
from src.client.remote_inference import RemotePlateDetector
from src.client.network_monitor import RTTMonitor
from src.client.camera_handler import CameraProcessor

RTSP_STREAMS = {
    "cam1": "rtsp://admin:sicove2025@192.168.15.9:554/onvif2",
    "cam2": "rtsp://admin:sicove2025@192.168.15.26:554/onvif2"
}

def main():
    rtt_monitor = RTTMonitor()
    rtt_monitor.start()

    local_detector = LocalPlateDetector("models/nano.pt")
    remote_detector = RemotePlateDetector()

    cameras = []
    for cam_id, rtsp in RTSP_STREAMS.items():
        cam = CameraProcessor(cam_id, rtsp, rtt_monitor, local_detector, remote_detector)
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

