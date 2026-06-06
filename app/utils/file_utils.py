import os
import uuid
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

def save_upload(file_bytes, filename):
    unique_name = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return file_path

def cleanup_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)