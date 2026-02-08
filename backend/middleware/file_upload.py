"""File upload handling for YatinVeda.

Supports profile pictures, documents, and chart images with validation.
Uses local filesystem storage with configurable upload directory.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile, HTTPException
from datetime import datetime
import mimetypes


class FileUploadConfig:
    """Configuration for file uploads."""
    
    # Base upload directory (relative to backend root)
    UPLOAD_DIR = Path("uploads")
    
    # Subdirectories for different file types
    PROFILE_PICS_DIR = UPLOAD_DIR / "profile_pics"
    DOCUMENTS_DIR = UPLOAD_DIR / "documents"
    CHART_IMAGES_DIR = UPLOAD_DIR / "chart_images"
    
    # Maximum file sizes (in bytes)
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Allowed MIME types
    ALLOWED_IMAGE_TYPES = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
    }
    
    ALLOWED_DOCUMENT_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    
    # File extensions
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx"}


def ensure_upload_directories():
    """Create upload directories if they don't exist."""
    for directory in [
        FileUploadConfig.PROFILE_PICS_DIR,
        FileUploadConfig.DOCUMENTS_DIR,
        FileUploadConfig.CHART_IMAGES_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving extension.
    
    Args:
        original_filename: Original uploaded filename
        
    Returns:
        Unique filename with timestamp and UUID
    """
    # Get file extension
    _, ext = os.path.splitext(original_filename)
    
    # Generate unique name: timestamp_uuid.ext
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    
    return f"{timestamp}_{unique_id}{ext.lower()}"


async def validate_file_upload(
    file: UploadFile,
    allowed_types: set,
    max_size: int,
    file_category: str = "file"
) -> None:
    """Validate uploaded file type and size.
    
    Args:
        file: Uploaded file object
        allowed_types: Set of allowed MIME types
        max_size: Maximum file size in bytes
        file_category: Category for error messages
        
    Raises:
        HTTPException: If validation fails
    """
    # Check file extension
    _, ext = os.path.splitext(file.filename or "")
    if not ext:
        raise HTTPException(
            status_code=400,
            detail=f"File must have an extension"
        )
    
    # Read file content to check size
    content = await file.read()
    file_size = len(content)
    
    # Reset file pointer for later use
    await file.seek(0)
    
    # Validate size
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"{file_category} size exceeds maximum allowed size of {max_mb:.1f}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail=f"{file_category} is empty"
        )
    
    # Validate MIME type
    content_type = file.content_type
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {file_category} type. Allowed types: {', '.join(allowed_types)}"
        )


async def save_upload_file(
    file: UploadFile,
    upload_dir: Path,
    allowed_types: set,
    max_size: int,
    file_category: str = "file"
) -> str:
    """Save uploaded file to disk with validation.
    
    Args:
        file: Uploaded file object
        upload_dir: Target directory for saving
        allowed_types: Set of allowed MIME types
        max_size: Maximum file size in bytes
        file_category: Category for error messages
        
    Returns:
        Relative path to saved file
        
    Raises:
        HTTPException: If validation fails or save error
    """
    # Ensure upload directory exists
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate file
    await validate_file_upload(file, allowed_types, max_size, file_category)
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename or "upload")
    file_path = upload_dir / unique_filename
    
    # Save file
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Return relative path from uploads directory
        return str(file_path.relative_to(FileUploadConfig.UPLOAD_DIR.parent))
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save {file_category}: {str(e)}"
        )


async def save_profile_picture(file: UploadFile) -> str:
    """Save user profile picture.
    
    Args:
        file: Uploaded image file
        
    Returns:
        Relative URL path to saved image
    """
    return await save_upload_file(
        file=file,
        upload_dir=FileUploadConfig.PROFILE_PICS_DIR,
        allowed_types=FileUploadConfig.ALLOWED_IMAGE_TYPES,
        max_size=FileUploadConfig.MAX_IMAGE_SIZE,
        file_category="profile picture"
    )


async def save_chart_image(file: UploadFile) -> str:
    """Save birth chart image.
    
    Args:
        file: Uploaded image file
        
    Returns:
        Relative URL path to saved image
    """
    return await save_upload_file(
        file=file,
        upload_dir=FileUploadConfig.CHART_IMAGES_DIR,
        allowed_types=FileUploadConfig.ALLOWED_IMAGE_TYPES,
        max_size=FileUploadConfig.MAX_IMAGE_SIZE,
        file_category="chart image"
    )


async def save_document(file: UploadFile) -> str:
    """Save document file (PDF, Word, etc.).
    
    Args:
        file: Uploaded document file
        
    Returns:
        Relative URL path to saved document
    """
    return await save_upload_file(
        file=file,
        upload_dir=FileUploadConfig.DOCUMENTS_DIR,
        allowed_types=FileUploadConfig.ALLOWED_DOCUMENT_TYPES,
        max_size=FileUploadConfig.MAX_DOCUMENT_SIZE,
        file_category="document"
    )


def delete_file(file_path: str) -> bool:
    """Delete a file from the filesystem.
    
    Args:
        file_path: Relative path to file
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        full_path = Path(file_path)
        if full_path.exists() and full_path.is_file():
            full_path.unlink()
            return True
        return False
    except Exception:
        return False


def get_file_url(file_path: str, base_url: str = "/uploads") -> str:
    """Convert file path to URL.
    
    Args:
        file_path: Relative file path
        base_url: Base URL for uploads
        
    Returns:
        Full URL to file
    """
    # Remove 'uploads/' prefix if present
    if file_path.startswith("uploads/"):
        file_path = file_path[8:]
    
    return f"{base_url}/{file_path}"


# Initialize upload directories on module import
ensure_upload_directories()


__all__ = [
    "FileUploadConfig",
    "save_profile_picture",
    "save_chart_image",
    "save_document",
    "delete_file",
    "get_file_url",
    "ensure_upload_directories",
]
