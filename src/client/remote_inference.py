import grpc
import cv2
from src.proto import plate_detection_pb2
from src.proto import plate_detection_pb2_grpc

class RemotePlateDetector:
    def __init__(self, server_address="localhost:50051"):
        self.channel = grpc.insecure_channel(server_address)
        self.stub = plate_detection_pb2_grpc.PlateDetectionStub(self.channel)

    def detect(self, frame):
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
        _, buffer = cv2.imencode(".jpg", frame, encode_param)
        image_bytes = buffer.tobytes()

        response = self.stub.DetectPlate(plate_detection_pb2.ImageRequest(image=image_bytes))
        return response.x1, response.y1, response.x2, response.y2, response.plate_text

