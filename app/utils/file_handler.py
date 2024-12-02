# In app/utils/file_handler.py
import os
from fastapi import UploadFile

def handle_uploaded_file(file: UploadFile) -> str:
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as f:
        f.write(file.file.read())
    return temp_file_path

def delete_temp_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)
