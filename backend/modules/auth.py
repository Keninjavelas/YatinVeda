"""
🔐 Authentication System for YatinVeda
JWT-based authentication with user registration, login, and profile management
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt  # Direct bcrypt import instead of passlib wrapper for compat with bcrypt 5.x
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status as starlette_status
import os
import logging
import hashlib

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "development-secret-please-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "14"))

# Bearer token scheme
class LenientHTTPBearer(HTTPBearer):
    """HTTPBearer that returns 403 on missing credentials (default FastAPI behavior)."""
    async def __call__(self, request: Request):  # type: ignore[override]
        return await super().__call__(request)

class Strict401HTTPBearer(HTTPBearer):
    """HTTPBearer variant that returns 401 instead of 403 when Authorization header is missing or malformed.
    Used for endpoints whose tests expect HTTP 401 for missing credentials (e.g., user_charts routes).
    """
    async def __call__(self, request: Request):  # type: ignore[override]
        auth = request.headers.get("Authorization")
        if not auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Delegate normal parsing (will still raise if scheme invalid)
        credentials = await super().__call__(request)
        return credentials

security = LenientHTTPBearer(auto_error=True)
security_401 = Strict401HTTPBearer(auto_error=True)

def _truncate_for_bcrypt(password: str) -> bytes:
    """Truncate a UTF-8 string to <= 71 bytes for bcrypt (safe margin under the 72-byte limit).
    Bcrypt limits secrets to 72 bytes; passlib+bcrypt 5.x may throw at exactly 72.
    Handles multi-byte character edge cases. Returns bytes to pass directly to bcrypt.
    """
    try:
        raw = password.encode("utf-8")
    except Exception:
        # Fallback: treat as plain if encoding fails unexpectedly
        raw = password[:71].encode("utf-8", errors="ignore")
    if len(raw) <= 71:
        return raw
    # Trim to 71 bytes and drop any trailing partial multi-byte sequence
    trimmed = raw[:71]
    # decode then re-encode to ensure no partial characters
    safe_password = trimmed.decode("utf-8", errors="ignore")
    return safe_password.encode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly.
    Returns False if verification fails or encounters an error.
    """
    try:
        safe_password = _truncate_for_bcrypt(plain_password)
        # hashed_password is stored as string in DB but bcrypt needs bytes
        return bcrypt.checkpw(safe_password, hashed_password.encode("utf-8"))
    except Exception as e:
        # Log error but return False to prevent exposing internal errors
        logging.getLogger(__name__).error(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly; returns hash as string for DB storage.
    Truncates password to 71 bytes (safe for bcrypt).
    Raises ValueError if hashing fails.
    """
    try:
        safe_password = _truncate_for_bcrypt(password)
        # bcrypt.hashpw returns bytes; decode to string for SQLAlchemy storage
        return bcrypt.hashpw(safe_password, bcrypt.gensalt()).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Password hashing failed: {str(e)}")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token with consistent expiry and issued-at claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": expire,
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a refresh token with longer expiry and unique jti."""
    import uuid
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    # Use UUID for unique jti
    jti = f"rt-{uuid.uuid4().hex}"
    to_encode.update({
        "typ": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": expire,
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return payload if username is not None else None
    except JWTError as e:
        logging.getLogger(__name__).warning(f"JWT verification error: {e}")
        return None

def verify_refresh_token(token: str) -> Optional[dict]:
    """Verify refresh JWT and ensure type is refresh."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("typ") != "refresh":
            return None
        username: str = payload.get("sub")
        return payload if username is not None else None
    except JWTError as e:
        logging.getLogger(__name__).warning(f"Refresh token verification error: {e}")
        return None

def hash_token_sha256(token: str) -> str:
    """Hash a token using SHA-256 for DB storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current authenticated user from JWT token
    
    Returns a dict-like object with user attributes from the JWT payload.
    Supports both dictionary access (user['id']) and attribute access (user.id).
    Enhanced to include role and verification status claims.
    """
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create a dict-like object that supports both dict and attribute access
    class UserInfo:
        """User information object that supports both dict and attribute access"""
        def __init__(self, user_id, username, is_admin=False, role=None, verification_status=None):
            self._data = {
                'id': user_id,
                'user_id': user_id,
                'username': username,
                'is_admin': is_admin,
                'role': role,
                'verification_status': verification_status
            }
            self.id = user_id
            self.username = username
            self.is_admin = is_admin
            self.role = role
            self.verification_status = verification_status
        
        def __getitem__(self, key):
            """Support dictionary access: user['id']"""
            return self._data[key]
        
        def get(self, key, default=None):
            """Support dict.get() method: user.get('id', None)"""
            return self._data.get(key, default)
    
    return UserInfo(
        user_id=payload.get("user_id"),
        username=username,
        is_admin=payload.get("is_admin", False),
        role=payload.get("role"),
        verification_status=payload.get("verification_status")
    )

async def get_current_user_401(
    credentials: HTTPAuthorizationCredentials = Depends(security_401)
):
    """Same as get_current_user but uses security_401 returning 401 on missing credentials.
    Enhanced to include role and verification status claims.
    """
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None or payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    class UserInfo:
        def __init__(self, user_id, username, is_admin=False, role=None, verification_status=None):
            self._data = {
                'id': user_id,
                'user_id': user_id,
                'username': username,
                'is_admin': is_admin,
                'role': role,
                'verification_status': verification_status
            }
            self.id = user_id
            self.username = username
            self.is_admin = is_admin
            self.role = role
            self.verification_status = verification_status
        def __getitem__(self, key):
            return self._data[key]
        def get(self, key, default=None):
            return self._data.get(key, default)
    return UserInfo(
        user_id=payload.get("user_id"),
        username=payload.get("sub"),
        is_admin=payload.get("is_admin", False),
        role=payload.get("role"),
        verification_status=payload.get("verification_status")
    )


async def get_current_user_optional(
    request: Request
) -> Optional['UserInfo']:
    """Get current user if authenticated, otherwise return None.
    
    This is useful for endpoints that work for both authenticated and anonymous users.
    Does not raise an exception if no credentials are provided.
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    
    try:
        token = auth.replace("Bearer ", "")
        payload = verify_token(token)
        if payload is None or payload.get("sub") is None:
            return None
        
        class UserInfo:
            def __init__(self, user_id, username, is_admin=False, role=None, verification_status=None):
                self._data = {
                    'id': user_id,
                    'user_id': user_id,
                    'username': username,
                    'is_admin': is_admin,
                    'role': role,
                    'verification_status': verification_status
                }
                self.id = user_id
                self.username = username
                self.is_admin = is_admin
                self.role = role
                self.verification_status = verification_status
            def __getitem__(self, key):
                return self._data[key]
            def get(self, key, default=None):
                return self._data.get(key, default)
        
        return UserInfo(
            user_id=payload.get("user_id"),
            username=payload.get("sub"),
            is_admin=payload.get("is_admin", False),
            role=payload.get("role"),
            verification_status=payload.get("verification_status")
        )
    except Exception:
        # If token verification fails, just return None instead of raising
        return None

def authenticate_user(username: str, password: str, db):
    """Authenticate user with username and password"""
    user = db.get_user(username=username)
    if not user or not verify_password(password, user["password_hash"]):
        return False
    return user
