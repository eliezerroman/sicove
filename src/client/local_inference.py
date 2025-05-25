from ultralytics import YOLO

class LocalPlateDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.model.to("cpu")

    def detect(self, frame):
        results = self.model(frame)[0]
        if results.boxes:
            box = results.boxes[0]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            return x1, y1, x2, y2, "local"
        return None

