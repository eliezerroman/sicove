import socket

HOST = '127.0.0.1'
PORT = 5001

def run_stamper_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"[STAMPER] Servidor ouvindo em {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"[STAMPER] Conexão de {addr}")
                total_bytes = 0

                while True:
                    data = conn.recv(4096)
                    if not data:
                        break
                    total_bytes += len(data)

                conn.sendall(str(total_bytes).encode())
                print(f"[STAMPER] Total de bytes recebidos: {total_bytes}")

if __name__ == "__main__":
    run_stamper_server()
