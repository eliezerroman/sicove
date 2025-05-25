# stamper_server.py
import socket

HOST = '0.0.0.0'
PORT = 5001

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"Stamper ouvindo em {HOST}:{PORT}")

    while True:
        conn, addr = s.accept()
        with conn:
            print(f"Conexão recebida de {addr}")
            total_bytes = 0
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                total_bytes += len(data)
            # Envia total de bytes de volta ao cliente
            conn.sendall(str(total_bytes).encode())
            print(f"Bytes recebidos: {total_bytes} - resposta enviada")

