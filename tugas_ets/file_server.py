import socket
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from file_protocol import FileProtocol
import signal

fp = FileProtocol()

def handle_client(connection, address):
    buffer = ""
    delimiter = "\r\n\r\n"
    
    while True:
        data = connection.recv(209715200)
        if not data:
            break 
        
        buffer += data.decode()
        if delimiter in buffer:
            break

    if buffer:
        d = buffer.rstrip(delimiter)
        hasil = fp.proses_string(d)
        if hasil:
            hasil = hasil + delimiter
            connection.sendall(hasil.encode())

    connection.close()

def start_server(pool_type, pool_size, ip='0.0.0.0', port=8889):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def shutdown_handler(signum, frame):
        logging.warning("Shutdown signal received. Closing server gracefully.")
        server_socket.close()

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    try:
        server_socket.bind((ip, port))
        server_socket.listen(100)
        logging.warning(f"Server started on {ip}:{port} with {pool_type} pool (size {pool_size})")

        Executor = ThreadPoolExecutor if pool_type == 'thread' else ProcessPoolExecutor

        with Executor(max_workers=pool_size) as pool:
            while True:
                try:
                    conn, addr = server_socket.accept()
                    logging.info(f"Accepted connection from {addr}")
                    pool.submit(handle_client, conn, addr)
                except OSError as e:

                    logging.warning(f"Server socket closed. Exiting loop. ({e})")
                    break

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        logging.info("Server has shut down.")
        server_socket.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pool', choices=['thread', 'process'], default='thread', help='Type of concurrency pool')
    parser.add_argument('--poolsize', type=int, default=5, help='Number of workers in the pool')
    parser.add_argument('--ip', default='0.0.0.0', help='IP address to bind')
    parser.add_argument('--port', type=int, default=8889, help='Port number')
    args = parser.parse_args()

    start_server(args.pool, args.poolsize, args.ip, args.port)


if __name__ == "__main__":
    main()