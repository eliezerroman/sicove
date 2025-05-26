import grpc
import threading
from concurrent import futures
from src.proto import plate_detection_pb2_grpc
from src.server.service import PlateDetectionService
from src.monitoring.stamper_server import run_stamper_server  # importe a função stamper

def serve():
    # Inicia o stamper_server numa thread daemon (background)
    threading.Thread(target=run_stamper_server, daemon=True).start()

    # Inicia o servidor gRPC normalmente
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    plate_detection_pb2_grpc.add_PlateDetectionServicer_to_server(
        PlateDetectionService("models/nano.pt"), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Servidor gRPC rodando em [::]:50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
