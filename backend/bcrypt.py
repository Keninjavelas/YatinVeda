"""Local bcrypt stub used when the real `bcrypt` package is unavailable.

This implements a tiny subset of the interface used in modules.auth
(hashpw, checkpw, gensalt) using SHA-256. It is **not** a drop-in
replacement for production security but is sufficient for tests where
only round‑trip verification of hashes is required.
"""

from __future__ import annotations

import base64
import hashlib
import os
from typing import Optional


def gensalt(rounds: int = 12) -> bytes:  # pragma: no cover - trivial
    """Return a random salt.

    The `rounds` parameter is accepted for API compatibility but ignored.
    """
    return os.urandom(16)


def hashpw(password: bytes, salt: bytes) -> bytes:
    """Hash a password with the given salt using SHA-256.

    Result format (base64-encoded): ``salt || sha256(salt + password)``.
    """
    digest = hashlib.sha256(salt + password).digest()
    return base64.b64encode(salt + digest)


def checkpw(password: bytes, hashed_password: bytes) -> bool:
    """Verify a password against a previously generated hash."""
    try:
        raw = base64.b64decode(hashed_password)
        salt, digest = raw[:16], raw[16:]
        expected = hashlib.sha256(salt + password).digest()
        return digest == expected
    except Exception:
        return False
