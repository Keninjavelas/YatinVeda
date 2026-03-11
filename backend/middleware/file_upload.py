"""File upload handling for YatinVeda.

Supports profile pictures, documents, and chart images with validation.
Supports local filesystem and S3-compatible cloud storage backends
via the STORAGE_BACKEND environment variable ('local' or 's3').
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional, List, Protocol
from fastapi import UploadFile, HTTPException
from datetime import datetime
import mimetypes

logger = logging.getLogger(__name__)


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


# ── Storage Backends ──────────────────────────────────────────


class StorageBackend(Protocol):
    """Protocol for storage backends."""
    def save(self, content: bytes, key: str) -> str: ...
    def delete(self, key: str) -> bool: ...
    def get_url(self, key: str) -> str: ...
    def init(self) -> None: ...


class LocalStorageBackend:
    """Store files on the local filesystem."""

    def init(self) -> None:
        for directory in [
            FileUploadConfig.PROFILE_PICS_DIR,
            FileUploadConfig.DOCUMENTS_DIR,
            FileUploadConfig.CHART_IMAGES_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, key: str) -> str:
        file_path = Path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(content)
        return str(file_path.relative_to(FileUploadConfig.UPLOAD_DIR.parent))

    def delete(self, key: str) -> bool:
        try:
            full_path = Path(key)
            if full_path.exists() and full_path.is_file():
                full_path.unlink()
                return True
            return False
        except Exception:
            return False

    def get_url(self, key: str) -> str:
        path = key
        if path.startswith("uploads/"):
            path = path[8:]
        return f"/uploads/{path}"


class S3StorageBackend:
    """Store files in an S3-compatible bucket."""

    def __init__(self) -> None:
        self.bucket = os.getenv("S3_BUCKET", "")
        self.region = os.getenv("S3_REGION", "us-east-1")
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL")  # for MinIO / R2
        self.prefix = os.getenv("S3_KEY_PREFIX", "uploads")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import boto3
            except ImportError:
                raise RuntimeError(
                    "boto3 is required for S3 storage. Install with: pip install boto3"
                )
            kwargs = {"region_name": self.region}
            if self.endpoint_url:
                kwargs["endpoint_url"] = self.endpoint_url
            self._client = boto3.client("s3", **kwargs)
        return self._client

    def init(self) -> None:
        if not self.bucket:
            raise RuntimeError("S3_BUCKET environment variable is required for S3 storage")
        # verify connectivity
        self._get_client().head_bucket(Bucket=self.bucket)
        logger.info(f"S3 storage backend initialized: bucket={self.bucket}")

    def save(self, content: bytes, key: str) -> str:
        # key comes as e.g. "uploads/profile_pics/file.jpg" – normalise
        s3_key = key.replace("\\", "/")
        if not s3_key.startswith(self.prefix):
            s3_key = f"{self.prefix}/{s3_key}"
        self._get_client().put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=content,
        )
        return s3_key

    def delete(self, key: str) -> bool:
        try:
            self._get_client().delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def get_url(self, key: str) -> str:
        cdn = os.getenv("S3_CDN_URL")
        if cdn:
            return f"{cdn.rstrip('/')}/{key}"
        return self._get_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=3600,
        )


def _create_storage_backend() -> StorageBackend:
    backend_name = os.getenv("STORAGE_BACKEND", "local").lower()
    if backend_name == "s3":
        return S3StorageBackend()
    return LocalStorageBackend()


storage: StorageBackend = _create_storage_backend()


def ensure_upload_directories():
    """Initialise the configured storage backend."""
    storage.init()


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
    """Save uploaded file via the configured storage backend.
    
    Args:
        file: Uploaded file object
        upload_dir: Target directory / key prefix for saving
        allowed_types: Set of allowed MIME types
        max_size: Maximum file size in bytes
        file_category: Category for error messages
        
    Returns:
        Storage key / relative path to saved file
        
    Raises:
        HTTPException: If validation fails or save error
    """
    # Validate file
    await validate_file_upload(file, allowed_types, max_size, file_category)
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename or "upload")
    file_key = str(upload_dir / unique_filename)
    
    # Save via storage backend
    try:
        content = await file.read()
        return storage.save(content, file_key)
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
    """Delete a file via the configured storage backend.
    
    Args:
        file_path: Storage key / relative path to file
        
    Returns:
        True if deleted successfully, False otherwise
    """
    return storage.delete(file_path)


def get_file_url(file_path: str, base_url: str = "/uploads") -> str:
    """Convert storage key to a URL.
    
    Args:
        file_path: Storage key / relative file path
        base_url: Base URL (used only by local backend)
        
    Returns:
        Full URL to file
    """
    return storage.get_url(file_path)


# Initialize upload directories on module import
ensure_upload_directories()


__all__ = [
    "FileUploadConfig",
    "storage",
    "save_profile_picture",
    "save_chart_image",
    "save_document",
    "delete_file",
    "get_file_url",
    "ensure_upload_directories",
]
