#Server
import cv2
import grpc
import numpy as np
import plate_detection_pb2
import plate_detection_pb2_grpc
from concurrent import futures
from ultralytics import YOLO
import pytesseract

# Configuração do Tesseract
pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

# Carrega o modelo YOLO
model = YOLO("/home/ros/plate_detection/models/medium.pt").to("cuda")

print(f"Modelo carregado em: {model.device}")


class PlateDetectionService(plate_detection_pb2_grpc.PlateDetectionServicer):
    def DetectPlate(self, request, context):
        # Converte os bytes da imagem para um array NumPy
        nparr = np.frombuffer(request.image, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Faz a inferência
        results = model(frame)
        
        detected_text = "Nenhuma placa detectada"
        x1, y1, x2, y2 = 0, 0, 0, 0

        if results[0].boxes:
            box = results[0].boxes[0]
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Coordenadas da placa
            
            # Recorta a região da placa
            cropped_image = frame[y1:y2, x1:x2]
            
            # Executa OCR
            detected_text = pytesseract.image_to_string(cropped_image, config="--psm 8").strip()

        return plate_detection_pb2.DetectionResponse(
            plate_text=detected_text,
            x1=x1, y1=y1, x2=x2, y2=y2
        )

# Inicia o servidor gRPC com Thread Pool
def serve():
    max_clients = 4  # Define um limite de 4 conexões simultâneas
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_clients))
    plate_detection_pb2_grpc.add_PlateDetectionServicer_to_server(PlateDetectionService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print(f"Servidor gRPC rodando na porta 50051 com suporte para {max_clients} clientes simultâneos...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()

