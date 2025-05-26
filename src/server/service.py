import cv2
import numpy as np
import pytesseract
from ultralytics import YOLO
from src.proto import plate_detection_pb2
from src.proto import plate_detection_pb2_grpc


class PlateDetectionService(plate_detection_pb2_grpc.PlateDetectionServicer):
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.model.to("mps")  # ou "cuda" conforme necessário

    def DetectPlate(self, request, context):
        nparr = np.frombuffer(request.image, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        results = self.model(frame)
        x1, y1, x2, y2 = 0, 0, 0, 0
        plate_text = "Nenhuma placa"

        if results[0].boxes:
            box = results[0].boxes[0]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            roi = frame[y1:y2, x1:x2]
            #plate_text = pytesseract.image_to_string(roi, config="--psm 8").strip()
            plate_text = "000-0000"  # Simulação de texto de placa para teste

        return plate_detection_pb2.DetectionResponse(
            plate_text=plate_text, x1=x1, y1=y1, x2=x2, y2=y2
        )

