import os
import json
import cv2
import threading
import time
from flask import Flask, request, Response, render_template, redirect, url_for, jsonify
from src.client.local_inference import LocalPlateDetector
from src.client.remote_inference import RemotePlateDetector
from src.monitoring.network_monitor import NetworkMonitor
from src.client.camera_handler import CameraProcessor
from src.data.history_manager import PlateHistory

CAMERA_CONFIG_PATH = "src/data/camera_config.json"

app = Flask(__name__, template_folder="../interface/templates", static_folder="../interface/static")
cameras = {}

plate_history = PlateHistory(db_path="src/data/plates.db")

def load_camera_config():
    if os.path.exists(CAMERA_CONFIG_PATH):
        with open(CAMERA_CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def save_camera_config(config):
    with open(CAMERA_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def start_camera(cam_id, rtsp_url):
    local_detector = LocalPlateDetector("models/nano.pt")
    remote_detector = RemotePlateDetector()
    cam = CameraProcessor(cam_id, rtsp_url, local_detector, remote_detector)
    cam.start()
    cameras[cam_id] = cam

# Inicialização dos componentes
camera_config = load_camera_config()
for cam_id, rtsp in camera_config.items():
    start_camera(cam_id, rtsp)

network_monitor = NetworkMonitor(host="192.168.15.1", interval=1, status_file="src/monitoring/network_status.json")
threading.Thread(target=network_monitor.start, daemon=True).start()

@app.route("/", methods=["GET"])
def index():
    history = plate_history.list_all()
    return render_template("index.html", cameras=cameras, plate_history=history)


@app.route("/add_camera", methods=["POST"])
def add_camera():
    cam_id = request.form["cam_id"]
    rtsp_url = request.form["rtsp_url"]
    if cam_id not in cameras:
        start_camera(cam_id, rtsp_url)
        camera_config[cam_id] = rtsp_url
        save_camera_config(camera_config)
    return redirect(url_for("index"))

@app.route("/remove_camera/<cam_id>")
def remove_camera(cam_id):
    if cam_id in cameras:
        cameras[cam_id].stop()
        del cameras[cam_id]
        if cam_id in camera_config:
            del camera_config[cam_id]
            save_camera_config(camera_config)
    return redirect(url_for("index"))

def generate_mjpeg(camera):
    while True:
        frame = camera.frame
        if frame is not None:
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n")
        time.sleep(0.05)

@app.route("/video/<cam_id>")
def video(cam_id):
    cam = cameras.get(cam_id)
    if cam:
        return Response(generate_mjpeg(cam), mimetype="multipart/x-mixed-replace; boundary=frame")
    return "Câmera não encontrada", 404

@app.route("/api/ultimas_placas")
def ultimas_placas():
    history = plate_history.list_all(limit=10)
    return jsonify(history)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=45000, debug=True, threaded=True)
