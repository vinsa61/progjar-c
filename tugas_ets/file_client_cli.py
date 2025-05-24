import socket
import json
import base64
import logging
import argparse
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
parser = argparse.ArgumentParser()
parser.add_argument("--host", default="127.0.0.1", help="Server IP address")
parser.add_argument("--port", type=int, default=8889, help="Server port")
parser.add_argument("--operation", choices=["upload", "download"], required=True, help="Operation to perform")
parser.add_argument("--file", required=True, help="Filename to upload or download")
parser.add_argument("--filesize", type=int, required=True, help="File size in MB (used for throughput calc)")
parser.add_argument("--clients", type=int, default=1, help="Number of client workers")
args = parser.parse_args()

server_address = (args.host, args.port)
CHUNK_SIZE = 1048576 

def send_command(command_str=""):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    try:
        command_bytes = (command_str + "\r\n\r\n").encode()
        total_sent = 0
        while total_sent < len(command_bytes):
            sent = sock.send(command_bytes[total_sent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            total_sent = total_sent + sent

        data_received = ""
        # Use different buffer sizes for upload and download
        buffer_size = 1048576 if command_str.startswith("UPLOAD") else 209715200
        
        while True:
            data = sock.recv(buffer_size)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        
        if not data_received:
            return False
            
        try:
            hasil = json.loads(data_received)
            return hasil
        except json.JSONDecodeError:
            return False
    except Exception as e:
        return False
    finally:
        sock.close()

def remote_upload(filename=""):
    try:
        file_path = f"files/{filename}"
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
            
        file_size = os.path.getsize(file_path)
        
        # First, initiate upload and get upload ID
        command_str = f"UPLOAD_START {filename} {file_size}"
        result = send_command(command_str)
        if not result or result.get('status') != 'OK':
            return False
        
        upload_id = result['upload_id']
        
        with open(file_path, 'rb') as f:
            chunk_number = 0
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                    
                # Encode chunk and send
                encoded_chunk = base64.b64encode(chunk).decode()
                command_str = f"UPLOAD_CHUNK {upload_id} {chunk_number} {encoded_chunk}"
                result = send_command(command_str)
                if not result or result.get('status') != 'OK':
                    return False
                chunk_number += 1
        
        # Finalize upload
        command_str = f"UPLOAD_FINISH {upload_id}"
        result = send_command(command_str)
        return result and result.get('status') == 'OK'
    except Exception as e:
        return False

def remote_get(filename=""):
    command_str = f"GET {filename}"
    hasil = send_command(command_str)
    if hasil and hasil['status'] == 'OK':
        try:
            namafile = hasil['data_namafile']
            isifile = base64.b64decode(hasil['data_file'])
            with open(os.devnull, 'wb') as fp:
                fp.write(isifile)
            return True
        except:
            return False
    return False

# --- Start test ---
success = 0
fail = 0
start = time.time()

with ThreadPoolExecutor(max_workers=args.clients) as executor:
    futures = []
    for i in range(args.clients):
        if args.operation == "upload":
            futures.append(executor.submit(remote_upload, args.file))
        else:
            futures.append(executor.submit(remote_get, args.file))

    for fut in as_completed(futures):
        if fut.result():
            success += 1
        else:
            fail += 1

end = time.time()
total_time = end - start
throughput = (args.filesize * 1024 * 1024 * success) / total_time if total_time > 0 else 0  # bytes per second

# Output format: operation,volume,time,throughput,success,fail
print(f"{args.operation},{args.filesize}MB,{total_time:.2f},{throughput:.2f},{success},{fail}")
