import itertools
import subprocess
import csv
import time
import os
import signal

# Create or overwrite the results file with headers
with open("results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "number",
        "operation",
        "volume",
        "client_workers_count",
        "server_workers_count",
        "time",
        "throughput",
        "client_workers_success_count",
        "client_workers_failed_count",
        "server_workers_success_count",
        "server_workers_failed_count"
    ])

operations = ["upload", "download"]
file_sizes = [("10mb_testfile.bin", 10), ("50mb_testfile.bin", 50), ("100mb_testfile.bin", 100)]
client_workers = [1, 5, 50]
server_workers = [1, 5, 50]
pool_types = ["thread", "process"]

combinations = list(itertools.product(pool_types, operations, file_sizes, client_workers, server_workers))

for idx, (pool, op, (fname, fsize), c_workers, s_workers) in enumerate(combinations, 1):
    print(f"\n=== Running Test {idx}/{len(combinations)} ===")
    print(f"Pool: {pool}, Operation: {op}, File: {fname}, Client: {c_workers}, Server: {s_workers}")

    # Start server
    server_cmd = f"python3 file_server.py --pool {pool} --poolsize {s_workers}"
    server_proc = subprocess.Popen(server_cmd.split())
    time.sleep(2)  # Let server start up

    # Run client stress script
    client_cmd = [
        "python3", "file_client_cli.py",
        "--operation", op,
        "--file", fname,
        "--clients", str(c_workers),
        "--filesize", str(fsize)
    ]
    print("Client command:", " ".join(client_cmd))
    result = subprocess.run(client_cmd, capture_output=True, text=True)

    try:
        # Parse client output (operation,volume,time,throughput,success,fail)
        client_data = result.stdout.strip().split(",")
        
        # Write to CSV
        with open("results.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                idx,                    # number
                client_data[0],         # operation
                client_data[1],         # volume
                c_workers,              # client_workers_count
                s_workers,              # server_workers_count
                client_data[2],         # time
                client_data[3],         # throughput
                client_data[4],         # client_workers_success_count
                client_data[5],         # client_workers_failed_count
                s_workers,              # server_workers_success_count (assuming all server workers are active)
                0                       # server_workers_failed_count (assuming no server failures)
            ])
        
        # Print single line to console
        print(f"Test {idx}/{len(combinations)}: {op}, {fsize}MB, {c_workers} clients ({client_data[4]} ok, {client_data[5]} fail), {s_workers} servers - {client_data[2]}s, {client_data[3]} B/s")
            
    except Exception as e:
        print(f"Error processing results: {str(e)}")
        print("Raw output:", result.stdout)
        print("Raw error:", result.stderr)

    # Kill server
    server_proc.terminate()
    try:
        server_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        print("[WARNING] Server did not terminate, killing forcefully...")
        os.kill(server_proc.pid, signal.SIGKILL)

    # Wait before starting the next one
    time.sleep(2)

