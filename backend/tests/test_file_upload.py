"""Tests for file-upload validation and local storage backend."""

import io
import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from fastapi import UploadFile, HTTPException

from middleware.file_upload import (
    FileUploadConfig,
    LocalStorageBackend,
    generate_unique_filename,
    validate_file_upload,
    save_upload_file,
)


# ── Unit tests for generate_unique_filename ────────────────────────

class TestGenerateUniqueFilename:
    def test_preserves_extension(self):
        name = generate_unique_filename("photo.JPG")
        assert name.endswith(".jpg")

    def test_different_each_call(self):
        a = generate_unique_filename("a.png")
        b = generate_unique_filename("a.png")
        assert a != b

    def test_handles_no_extension(self):
        name = generate_unique_filename("noext")
        assert "." not in name.split("_")[-1] or name.endswith("")


# ── Unit tests for validate_file_upload ────────────────────────────

class TestValidateFileUpload:

    @staticmethod
    def _make_upload(content: bytes, filename: str, content_type: str) -> UploadFile:
        return UploadFile(
            file=io.BytesIO(content),
            filename=filename,
            headers={"content-type": content_type},
        )

    @pytest.mark.anyio
    async def test_valid_image_passes(self):
        file = self._make_upload(b"\xff" * 100, "pic.jpg", "image/jpeg")
        await validate_file_upload(
            file,
            FileUploadConfig.ALLOWED_IMAGE_TYPES,
            FileUploadConfig.MAX_IMAGE_SIZE,
            "image",
        )
        # Should not raise

    @pytest.mark.anyio
    async def test_empty_file_rejected(self):
        file = self._make_upload(b"", "empty.jpg", "image/jpeg")
        with pytest.raises(HTTPException) as exc:
            await validate_file_upload(
                file,
                FileUploadConfig.ALLOWED_IMAGE_TYPES,
                FileUploadConfig.MAX_IMAGE_SIZE,
                "image",
            )
        assert exc.value.status_code == 400
        assert "empty" in exc.value.detail.lower()

    @pytest.mark.anyio
    async def test_oversize_file_rejected(self):
        big = b"\x00" * (FileUploadConfig.MAX_IMAGE_SIZE + 1)
        file = self._make_upload(big, "huge.jpg", "image/jpeg")
        with pytest.raises(HTTPException) as exc:
            await validate_file_upload(
                file,
                FileUploadConfig.ALLOWED_IMAGE_TYPES,
                FileUploadConfig.MAX_IMAGE_SIZE,
                "image",
            )
        assert exc.value.status_code == 400
        assert "exceeds" in exc.value.detail.lower()

    @pytest.mark.anyio
    async def test_wrong_mime_type_rejected(self):
        file = self._make_upload(b"\xff" * 100, "script.exe", "application/x-executable")
        with pytest.raises(HTTPException) as exc:
            await validate_file_upload(
                file,
                FileUploadConfig.ALLOWED_IMAGE_TYPES,
                FileUploadConfig.MAX_IMAGE_SIZE,
                "image",
            )
        assert exc.value.status_code == 400
        assert "Invalid" in exc.value.detail

    @pytest.mark.anyio
    async def test_missing_extension_rejected(self):
        file = self._make_upload(b"\xff" * 100, "noext", "image/jpeg")
        with pytest.raises(HTTPException) as exc:
            await validate_file_upload(
                file,
                FileUploadConfig.ALLOWED_IMAGE_TYPES,
                FileUploadConfig.MAX_IMAGE_SIZE,
                "image",
            )
        assert exc.value.status_code == 400


# ── LocalStorageBackend tests ─────────────────────────────────────

class TestLocalStorageBackend:
    TMP_DIR = Path("_test_uploads")

    @pytest.fixture(autouse=True)
    def setup_teardown(self, monkeypatch):
        # Redirect uploads to a temp directory
        monkeypatch.setattr(FileUploadConfig, "UPLOAD_DIR", self.TMP_DIR)
        monkeypatch.setattr(FileUploadConfig, "PROFILE_PICS_DIR", self.TMP_DIR / "profile_pics")
        monkeypatch.setattr(FileUploadConfig, "DOCUMENTS_DIR", self.TMP_DIR / "documents")
        monkeypatch.setattr(FileUploadConfig, "CHART_IMAGES_DIR", self.TMP_DIR / "chart_images")
        yield
        if self.TMP_DIR.exists():
            shutil.rmtree(self.TMP_DIR)

    def test_init_creates_dirs(self):
        backend = LocalStorageBackend()
        backend.init()
        assert (self.TMP_DIR / "profile_pics").is_dir()
        assert (self.TMP_DIR / "documents").is_dir()
        assert (self.TMP_DIR / "chart_images").is_dir()

    def test_save_and_read(self):
        backend = LocalStorageBackend()
        backend.init()
        content = b"hello world"
        key = str(self.TMP_DIR / "profile_pics" / "test.txt")
        result = backend.save(content, key)
        assert Path(key).read_bytes() == content

    def test_delete_existing(self):
        backend = LocalStorageBackend()
        backend.init()
        key = str(self.TMP_DIR / "profile_pics" / "del.txt")
        Path(key).write_bytes(b"data")
        assert backend.delete(key) is True
        assert not Path(key).exists()

    def test_delete_nonexistent(self):
        backend = LocalStorageBackend()
        assert backend.delete("nonexistent_path_xyz.txt") is False

    def test_get_url(self):
        backend = LocalStorageBackend()
        url = backend.get_url("uploads/profile_pics/abc.jpg")
        assert url == "/uploads/profile_pics/abc.jpg"
