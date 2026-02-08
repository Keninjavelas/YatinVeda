"""
Enhanced CSRF Protection Middleware for YatinVeda

This module implements comprehensive CSRF protection beyond the current refresh token
implementation, including double-submit cookie pattern, synchronizer token pattern,
and integration with security monitoring.
"""

import os
import hmac
import hashlib
import secrets
import base64
import uuid
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from middleware.security_monitor import (
    get_security_monitor,
    SecurityEventType,
    SecuritySeverity,
    log_csrf_event
)

logger = logging.getLogger(__name__)


class CSRFTokenType(Enum):
    """Types of CSRF tokens"""
    SYNCHRONIZER = "synchronizer"
    DOUBLE_SUBMIT = "double_submit"


@dataclass
class CSRFToken:
    """CSRF token data structure"""
    token: str
    token_type: CSRFTokenType
    session_id: str
    created_at: datetime
    expires_at: datetime
    used: bool = False


class CSRFProtection:
    """
    Comprehensive CSRF protection system
    
    Implements both synchronizer token pattern and double-submit cookie pattern
    for maximum security against cross-site request forgery attacks.
    """
    
    def __init__(
        self,
        secret_key: str,
        token_lifetime: int = 3600,  # 1 hour
        double_submit: bool = True,
        exempt_methods: Optional[Set[str]] = None,
        exempt_paths: Optional[Set[str]] = None,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        form_field_name: str = "csrf_token"
    ):
        self.secret_key = secret_key.encode() if isinstance(secret_key, str) else secret_key
        self.token_lifetime = token_lifetime
        self.double_submit = double_submit
        self.exempt_methods = exempt_methods or {"GET", "HEAD", "OPTIONS", "TRACE"}
        self.exempt_paths = exempt_paths or {"/health", "/docs", "/openapi.json", "/api/v1/health"}
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.form_field_name = form_field_name
        
        # Token storage (in production, use Redis or database)
        self.token_storage: Dict[str, CSRFToken] = {}
        
        logger.info(f"CSRF Protection initialized with double_submit={double_submit}")
    
    def _generate_token(self, session_id: str, token_type: CSRFTokenType = CSRFTokenType.SYNCHRONIZER) -> str:
        """Generate a cryptographically secure CSRF token"""
        # Create token data
        timestamp = str(int(datetime.utcnow().timestamp()))
        nonce = secrets.token_urlsafe(32)
        
        # Create token payload
        payload = f"{session_id}:{timestamp}:{nonce}:{token_type.value}"
        
        # Sign the payload
        signature = hmac.new(
            self.secret_key,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Combine payload and signature
        token = base64.urlsafe_b64encode(f"{payload}:{signature}".encode()).decode()
        
        return token
    
    def _verify_token(self, token: str, session_id: str) -> bool:
        """Verify a CSRF token"""
        try:
            # Decode token
            decoded = base64.urlsafe_b64decode(token.encode()).decode()
            parts = decoded.split(":")
            
            if len(parts) != 5:
                return False
            
            token_session_id, timestamp, nonce, token_type, signature = parts
            
            # Verify session ID matches
            if token_session_id != session_id:
                return False
            
            # Verify signature
            payload = f"{token_session_id}:{timestamp}:{nonce}:{token_type}"
            expected_signature = hmac.new(
                self.secret_key,
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return False
            
            # Check token expiration
            token_time = datetime.fromtimestamp(int(timestamp))
            if datetime.utcnow() - token_time > timedelta(seconds=self.token_lifetime):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"CSRF token verification failed: {str(e)}")
            return False
    
    async def generate_csrf_token(self, session_id: str, token_type: CSRFTokenType = CSRFTokenType.SYNCHRONIZER) -> str:
        """Generate and store a new CSRF token"""
        token = self._generate_token(session_id, token_type)
        
        # Store token
        csrf_token = CSRFToken(
            token=token,
            token_type=token_type,
            session_id=session_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=self.token_lifetime)
        )
        
        self.token_storage[token] = csrf_token
        
        # Clean up expired tokens periodically
        await self._cleanup_expired_tokens()
        
        return token
    
    async def validate_csrf_token(self, token: str, session_id: str) -> bool:
        """Validate a CSRF token"""
        if not token or not session_id:
            return False
        
        # Check if token exists in storage
        stored_token = self.token_storage.get(token)
        if not stored_token:
            # Try to verify token cryptographically (for stateless validation)
            return self._verify_token(token, session_id)
        
        # Check if token is expired
        if datetime.utcnow() > stored_token.expires_at:
            del self.token_storage[token]
            return False
        
        # Check if token has been used (for single-use tokens)
        if stored_token.used:
            return False
        
        # Verify token matches session
        if stored_token.session_id != session_id:
            return False
        
        # Mark token as used for single-use scenarios
        stored_token.used = True
        
        return True
    
    async def _cleanup_expired_tokens(self):
        """Clean up expired tokens from storage"""
        now = datetime.utcnow()
        expired_tokens = [
            token for token, csrf_token in self.token_storage.items()
            if now > csrf_token.expires_at
        ]
        
        for token in expired_tokens:
            del self.token_storage[token]
        
        if expired_tokens:
            logger.debug(f"Cleaned up {len(expired_tokens)} expired CSRF tokens")
    
    def _get_session_id(self, request: Request) -> Optional[str]:
        """Extract session ID from request"""
        # Try to get session ID from various sources
        
        # 1. From Authorization header (JWT token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, you'd decode the JWT to get user/session ID
            # For now, we'll use a hash of the token as session ID
            token = auth_header[7:]  # Remove "Bearer "
            return hashlib.sha256(token.encode()).hexdigest()[:32]
        
        # 2. From session cookie
        session_cookie = request.cookies.get("session_id")
        if session_cookie:
            return session_cookie
        
        # 3. From custom header
        session_header = request.headers.get("X-Session-ID")
        if session_header:
            return session_header
        
        # 4. Generate temporary session ID based on IP and User-Agent
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        temp_session = f"{client_ip}:{user_agent}"
        return hashlib.sha256(temp_session.encode()).hexdigest()[:32]
    
    def _is_exempt(self, request: Request) -> bool:
        """Check if request is exempt from CSRF protection"""
        # Check method exemption
        if request.method in self.exempt_methods:
            return True
        
        # Check path exemption
        path = request.url.path
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        
        # Check for API endpoints that may be exempt based on auth token
        if path.startswith('/api/'):
            # If using Bearer token authentication, may be exempt from CSRF
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                # For API calls with JWT, CSRF may not be necessary
                # But we still recommend CSRF for cookie-based auth
                return False
        
        return False
    
    async def _extract_csrf_token(self, request: Request) -> Optional[str]:
        """Extract CSRF token from request"""
        # 1. Check header
        token = request.headers.get(self.header_name)
        if token:
            return token
        
        # 2. Check form data (for POST requests)
        if request.method == "POST":
            try:
                form_data = await request.form()
                token = form_data.get(self.form_field_name)
                if token and isinstance(token, str):
                    return token
            except Exception:
                pass  # Not form data or already consumed
        
        # 3. Check JSON body
        try:
            if hasattr(request, '_json'):
                json_data = request._json
            else:
                json_data = await request.json()
                request._json = json_data  # Cache for later use
            
            token = json_data.get(self.form_field_name)
            if token:
                return token
        except Exception:
            pass  # Not JSON or already consumed
        
        return None
    
    async def validate_request(self, request: Request) -> bool:
        """Validate CSRF protection for a request"""
        # Check if request is exempt
        if self._is_exempt(request):
            return True
        
        # Get session ID
        session_id = self._get_session_id(request)
        if not session_id:
            logger.warning("No session ID found for CSRF validation")
            return False
        
        # Extract CSRF token from request
        csrf_token = await self._extract_csrf_token(request)
        if not csrf_token:
            logger.warning(f"No CSRF token found in request to {request.url.path}")
            return False
        
        # Validate token
        is_valid = await self.validate_csrf_token(csrf_token, session_id)
        
        if not is_valid:
            logger.warning(f"Invalid CSRF token for session {session_id[:8]}... on {request.url.path}")
        
        return is_valid
    
    async def set_csrf_cookie(self, response: Response, session_id: str) -> str:
        """Set CSRF token cookie for double-submit pattern"""
        if not self.double_submit:
            return ""
        
        # Generate double-submit token
        token = await self.generate_csrf_token(session_id, CSRFTokenType.DOUBLE_SUBMIT)
        
        # Set cookie
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=self.token_lifetime,
            httponly=False,  # Must be accessible to JavaScript for double-submit
            secure=True,  # Only over HTTPS
            samesite="strict"
        )
        
        return token


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware
    
    Automatically validates CSRF tokens for state-changing requests and
    integrates with security monitoring for attack detection.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        csrf_protection: CSRFProtection,
        enabled: bool = True,
        testing_mode: bool = False
    ):
        super().__init__(app)
        self.csrf_protection = csrf_protection
        self.enabled = enabled
        self.testing_mode = testing_mode
        
        logger.info(f"CSRF Middleware initialized (enabled={enabled}, testing={testing_mode})")
    
    async def dispatch(self, request: Request, call_next):
        """Process request through CSRF protection"""
        
        # Skip CSRF protection if disabled or in testing mode
        if not self.enabled or self.testing_mode:
            return await call_next(request)
        
        # Validate CSRF protection
        is_valid = await self.csrf_protection.validate_request(request)
        
        if not is_valid and not self.csrf_protection._is_exempt(request):
            # Log CSRF failure
            request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
            client_ip = request.client.host if request.client else "unknown"
            session_id = self.csrf_protection._get_session_id(request)
            
            # Extract attempted token for logging
            attempted_token = await self.csrf_protection._extract_csrf_token(request)
            
            await log_csrf_event(
                request_id=request_id,
                client_ip=client_ip,
                endpoint=request.url.path,
                user_id=session_id,
                details={
                    "method": request.method,
                    "user_agent": request.headers.get("User-Agent", "unknown"),
                    "referer": request.headers.get("Referer", "unknown"),
                    "attempted_token": attempted_token[:20] + "..." if attempted_token else None,
                    "session_id": session_id[:8] + "..." if session_id else None
                }
            )
            
            # Return 403 Forbidden
            return JSONResponse(
                status_code=403,
                content={
                    "error": "CSRF token validation failed",
                    "message": "Invalid or missing CSRF token",
                    "code": "CSRF_TOKEN_INVALID"
                },
                headers={"X-Request-ID": request_id}
            )
        
        # Process request
        response = await call_next(request)
        
        # Set CSRF cookie for double-submit pattern (on successful responses)
        if (response.status_code < 400 and 
            self.csrf_protection.double_submit and 
            request.method in {"GET", "POST"}):
            
            session_id = self.csrf_protection._get_session_id(request)
            if session_id:
                await self.csrf_protection.set_csrf_cookie(response, session_id)
        
        return response


# Global CSRF protection instance
_csrf_protection: Optional[CSRFProtection] = None


def get_csrf_protection() -> CSRFProtection:
    """Get the global CSRF protection instance"""
    global _csrf_protection
    if _csrf_protection is None:
        secret_key = os.getenv("CSRF_SECRET_KEY", os.getenv("SECRET_KEY", "default-csrf-secret"))
        token_lifetime = int(os.getenv("CSRF_TOKEN_LIFETIME", "3600"))
        double_submit = os.getenv("CSRF_DOUBLE_SUBMIT", "true").lower() == "true"
        
        _csrf_protection = CSRFProtection(
            secret_key=secret_key,
            token_lifetime=token_lifetime,
            double_submit=double_submit
        )
    
    return _csrf_protection


def initialize_csrf_protection(
    secret_key: str,
    token_lifetime: int = 3600,
    double_submit: bool = True,
    exempt_methods: Optional[Set[str]] = None,
    exempt_paths: Optional[Set[str]] = None
) -> CSRFProtection:
    """Initialize the global CSRF protection"""
    global _csrf_protection
    _csrf_protection = CSRFProtection(
        secret_key=secret_key,
        token_lifetime=token_lifetime,
        double_submit=double_submit,
        exempt_methods=exempt_methods,
        exempt_paths=exempt_paths
    )
    return _csrf_protection


# Convenience functions for CSRF token management
async def generate_csrf_token_for_session(session_id: str) -> str:
    """Generate a CSRF token for a session"""
    csrf_protection = get_csrf_protection()
    return await csrf_protection.generate_csrf_token(session_id)


async def validate_csrf_token_for_session(token: str, session_id: str) -> bool:
    """Validate a CSRF token for a session"""
    csrf_protection = get_csrf_protection()
    return await csrf_protection.validate_csrf_token(token, session_id)


async def get_csrf_token_for_request(request: Request) -> Optional[str]:
    """Get a CSRF token for the current request session"""
    csrf_protection = get_csrf_protection()
    session_id = csrf_protection._get_session_id(request)
    
    if not session_id:
        return None
    
    return await csrf_protection.generate_csrf_token(session_id)