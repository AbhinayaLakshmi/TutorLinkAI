import os
import uuid
import shutil
from fastapi import UploadFile
from backend.app.core.config import settings
from backend.app.core.exceptions import BadRequestException

def save_uploaded_file(
    file: UploadFile, 
    subfolder: str, 
    max_size_bytes: int, 
    allowed_extensions: set
) -> tuple[str, str, int]:
    """
    Saves an uploaded file securely.
    Returns: (stored_file_path, original_filename, file_size)
    """
    # 1. Validate file extension
    filename = file.filename or ""
    parts = filename.rsplit(".", 1)
    if len(parts) != 2:
        raise BadRequestException("File has no extension")
    
    ext = parts[1].lower()
    if ext not in allowed_extensions:
        raise BadRequestException(f"Unsupported file extension: .{ext}")
    
    # 2. Setup folders
    folder_path = os.path.join(settings.UPLOAD_DIR, subfolder)
    os.makedirs(folder_path, exist_ok=True)
    
    # Generate unique safe filename
    unique_filename = f"{uuid.uuid4()}.{ext}"
    dest_path = os.path.join(folder_path, unique_filename)
    
    # 3. Save file & enforce size validation
    size = 0
    try:
        with open(dest_path, "wb") as buffer:
            # Read in chunks to prevent loading large files in memory
            while True:
                chunk = file.file.read(8192)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_size_bytes:
                    raise BadRequestException(
                        f"File size exceeds maximum limit of {max_size_bytes / (1024 * 1024):.1f}MB"
                    )
                buffer.write(chunk)
    except Exception as e:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        if isinstance(e, BadRequestException):
            raise e
        raise BadRequestException(f"Failed to save file: {str(e)}")
        
    return dest_path, filename, size
