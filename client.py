import subprocess
import cv2
import grpc
import plate_detection_pb2
import plate_detection_pb2_grpc
import numpy as np
import time
import threading
from ultralytics import YOLO  # para inferência local

# Configura o canal de comunicação com o servidor
channel = grpc.insecure_channel("localhost:50051")
stub = plate_detection_pb2_grpc.PlateDetectionStub(channel)

# Endereços RTSP das duas câmeras IP
RTSP_STREAMS = {
    "cam1": "rtsp://admin:sicove2025@192.168.15.9:554/onvif2",
    "cam2": "rtsp://admin:sicove2025@192.168.15.26:554/onvif2"
}

# Armazena os últimos frames processados para exibição
display_frames = {
    "cam1": None,
    "cam2": None
}

# Carrega modelo local nano.pt para CPU
local_model = YOLO("models/nano.pt")
local_model.to("cpu")

# Alternância entre cliente e servidor
USE_LOCAL = True

frame_counter = {
    "cam1": 0,
    "cam2": 0
}

# Variável global para armazenar RTT
rtt_value = 0.0
rtt_lock = threading.Lock()

def update_rtt_periodically(host="localhost", interval=5):
    global rtt_value
    while True:
        try:
            result = subprocess.run(["ping", "-c", "1", host],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    timeout=2)
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "time=" in line:
                        time_str = line.split("time=")[1].split(" ")[0]
                        with rtt_lock:
                            rtt_value = float(time_str)
                        print(f"[RTT Monitor] RTT atualizado: {rtt_value} ms")
            else:
                print("[RTT Monitor] Falha no ping")
        except Exception as e:
            print(f"[RTT Monitor] Erro ao medir RTT: {e}")
        time.sleep(interval)

def run_local_inference(frame):
    results = local_model(frame)[0]
    if results.boxes:
        box = results.boxes[0]
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        plate_text = "local"
        return x1, y1, x2, y2, plate_text
    return None

def process_camera(camera_id, rtsp_url):
    global USE_LOCAL
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print(f"[ERRO] Não foi possível abrir {rtsp_url} com OpenCV FFmpeg.")
        return

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print(f"[{camera_id}] Frame inválido, pulando...")
            time.sleep(0.5)
            continue

        frame_counter[camera_id] += 1

        try:
            # Verifica a qualidade da conexão com base no RTT global
            with rtt_lock:
                current_rtt = rtt_value

            if current_rtt > 0.02:
                USE_LOCAL = True
                if frame_counter[camera_id] == 1:
                    print(f"[{camera_id}] RTT alto ({current_rtt:.2f} ms), usando inferência LOCAL")
            else:
                USE_LOCAL = False
                if frame_counter[camera_id] == 1:
                    print(f"[{camera_id}] RTT ok ({current_rtt:.2f} ms), usando inferência REMOTA")

            if USE_LOCAL:
                result = run_local_inference(frame)
                if result:
                    x1, y1, x2, y2, plate_text = result
                    cv2.putText(frame, f"{camera_id} - Placa: {plate_text}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            else:
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                _, buffer = cv2.imencode(".jpg", frame, encode_param)
                image_bytes = buffer.tobytes()

                response = stub.DetectPlate(plate_detection_pb2.ImageRequest(image=image_bytes))
                cv2.putText(frame, f"{camera_id} - Placa: {response.plate_text}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.rectangle(frame, (response.x1, response.y1), (response.x2, response.y2), (0, 255, 0), 2)

        except Exception as e:
            print(f"[{camera_id}] Erro na inferência: {e}")

        # Salva para exibição
        display_frames[camera_id] = cv2.resize(frame, (640, 360))

        time.sleep(0.033)

# Inicia a thread de RTT
threading.Thread(target=update_rtt_periodically, daemon=True).start()

# Inicia uma thread para cada câmera
for cam_id, rtsp_url in RTSP_STREAMS.items():
    threading.Thread(target=process_camera, args=(cam_id, rtsp_url), daemon=True).start()

# Janela principal
cv2.namedWindow("Detecção Alternada", cv2.WINDOW_NORMAL)

while True:
    frames = [display_frames["cam1"], display_frames["cam2"]]
    if all(f is not None for f in frames):
        combined = cv2.hconcat(frames)
        cv2.imshow("Detecção Alternada", combined)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()

