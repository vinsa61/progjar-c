import socket

HOST = '172.16.16.101'
PORT = 45000

def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall((command + '\r\n').encode('utf-8'))
        response = s.recv(1024)
        print("Response:", response.decode('utf-8').strip())

        if command != "QUIT":
            s.sendall(b"QUIT\r\n")  # Kirim QUIT supaya koneksi ditutup dengan baik

if __name__ == "__main__":
    send_command("TIME")
