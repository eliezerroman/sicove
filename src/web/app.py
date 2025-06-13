from flask import Flask, Response, render_template_string
import threading
import time
import cv2

from src.client.main import cameras

app = Flask(__name__)

HTML_PAGE = """
<html>
<head><title>Visualização Câmeras</title></head>
<body>
    {% for cam_id in cameras %}
    <h3>{{ cam_id }}</h3>
    <img src="/video/{{ cam_id }}" width="640" height="360">
    {% endfor %}
</body>
</html>
"""

@app.route("/")
def index():
    cam_ids = [cam.camera_id for cam in cameras]
    return render_template_string(HTML_PAGE, cameras=cam_ids)

def generate_mjpeg(camera):
    while True:
        frame = camera.frame
        if frame is not None:
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            else:
                print(f"[{camera.camera_id}] Falha ao codificar frame.")
        else:
            print(f"[{camera.camera_id}] Frame ainda é None.")
        time.sleep(0.05)

@app.route('/video/<cam_id>')
def video(cam_id):
    cam = next((c for c in cameras if c.camera_id == cam_id), None)
    if cam:
        print(f"Conectando stream da câmera {cam.camera_id}")
        return Response(generate_mjpeg(cam),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        print(f"Câmera {cam_id} não encontrada.")
        return "Câmera não encontrada", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=45000, debug=True, threaded=True)
