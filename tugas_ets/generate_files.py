import os

def generate_file(filename, size_mb):
    os.makedirs("files", exist_ok=True)
    with open(f"files/{filename}", 'wb') as f:
        f.write(b'0' * size_mb * 1024 * 1024)
    print(f"{filename} ({size_mb}MB) created successfully.")

if __name__ == "__main__":
    generate_file('10mb_testfile.bin', 10)
    generate_file('50mb_testfile.bin', 50)
    generate_file('100mb_testfile.bin', 100)
