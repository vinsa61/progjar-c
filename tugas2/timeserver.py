from socket import *
import socket
import threading
import logging
import time
import sys
from datetime import datetime

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        logging.warning(f"[THREAD] Handling client from {self.address}")
        buffer = b''
        try:
            while True:
                data = self.connection.recv(1024)
                if not data:
                    break
                buffer += data

                while b"\r\n" in buffer:
                    line, buffer = buffer.split(b"\r\n", 1)
                    command = line.decode("utf-8").strip()

                    if command == "TIME":
                        now = datetime.now().strftime("%H:%M:%S")
                        response = f"JAM {now}\r\n"
                        self.connection.sendall(response.encode("utf-8"))
                    elif command == "QUIT":
                        logging.warning(f"[QUIT] Connection closed by {self.address}")
                        self.connection.close()
                        return
                    else:
                        # Command tidak dikenal, bisa diabaikan atau ditangani
                        continue
        except Exception as e:
            logging.error(f"[ERROR] {self.address} - {e}")
        finally:
            self.connection.close()

class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(('0.0.0.0', 45000))
        self.my_socket.listen(5)
        logging.warning("[SERVER] Time server started on port 45000")

        while True:
            connection, client_address = self.my_socket.accept()
            logging.warning(f"[CONNECT] Connection from {client_address}")

            clt = ProcessTheClient(connection, client_address)
            clt.start()
            self.the_clients.append(clt)

def main():
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    svr = Server()
    svr.start()

if __name__ == "__main__":
    main()
