"""
Advanced Rate Limiting Middleware for YatinVeda
"""

import os
import logging
import asyncio
from typing import Optional, Dict, List, Tuple, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RateLimitAction(Enum):
    """Actions to take when rate limit is exceeded"""
    THROTTLE = "throttle"
    BLOCK = "block"
    PROGRESSIVE_DELAY = "progressive_delay"
    LOG_ONLY = "log_only"


@dataclass
class RateLimitRule:
    """Configuration for a rate limiting rule"""
    name: str
    limit: int
    window: int
    action: RateLimitAction
    delay_seconds: Optional[int] = None
    block_duration: Optional[int] = None
    progressive_multiplier: float = 2.0
    max_delay: int = 300


@dataclass
class RateLimitStatus:
    """Current rate limit status for a key"""
    key: str
    rule_name: str
    current_count: int
    limit: int
    window_start: datetime
    window_end: datetime
    is_blocked: bool = False
    block_expires: Optional[datetime] = None


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    status: RateLimitStatus
    delay_seconds: int = 0
    retry_after: Optional[int] = None
    message: Optional[str] = None


class InMemoryRateLimitStorage:
    """In-memory storage for rate limiting"""
    
    def __init__(self):
        self.counts: Dict[str, Dict[str, Any]] = {}
        self.blocks: Dict[str, datetime] = {}
        self.failures: Dict[str, Dict[str, Any]] = {}
        
    async def get_count(self, key: str, window: int) -> Tuple[int, datetime]:
        """Get current count and window start for a key"""
        now = datetime.utcnow()
        
        if key not in self.counts:
            return 0, now
            
        data = self.counts[key]
        window_start = data.get("window_start", now)
        count = data.get("count", 0)
        
        # Check if window has expired
        if now - window_start > timedelta(seconds=window):
            count = 0
            window_start = now
            
        return count, window_start
    
    async def increment_count(self, key: str, window: int) -> int:
        """Increment count for a key and return new count"""
        now = datetime.utcnow()
        
        if key not in self.counts:
            self.counts[key] = {"count": 0, "window_start": now}
            
        data = self.counts[key]
        window_start = data["window_start"]
        
        # Check if window has expired
        if now - window_start > timedelta(seconds=window):
            data["count"] = 0
            data["window_start"] = now
            
        data["count"] += 1
        return data["count"]
    
    async def set_block(self, key: str, duration: int) -> None:
        """Block a key for specified duration"""
        expires_at = datetime.utcnow() + timedelta(seconds=duration)
        self.blocks[key] = expires_at
    
    async def is_blocked(self, key: str) -> Tuple[bool, Optional[datetime]]:
        """Check if key is blocked and when block expires"""
        if key not in self.blocks:
            return False, None
            
        expires_at = self.blocks[key]
        if datetime.utcnow() < expires_at:
            return True, expires_at
        else:
            # Block has expired, clean up
            del self.blocks[key]
            return False, None
    
    async def get_failure_count(self, key: str) -> int:
        """Get progressive failure count for a key"""
        if key not in self.failures:
            return 0
            
        data = self.failures[key]
        # Check if failures have expired (1 hour)
        if datetime.utcnow() - data.get("last_failure", datetime.utcnow()) > timedelta(hours=1):
            del self.failures[key]
            return 0
            
        return data.get("count", 0)
    
    async def increment_failure_count(self, key: str) -> int:
        """Increment failure count and return new count"""
        now = datetime.utcnow()
        
        if key not in self.failures:
            self.failures[key] = {"count": 0, "last_failure": now}
            
        data = self.failures[key]
        
        # Check if failures have expired (1 hour)
        if now - data.get("last_failure", now) > timedelta(hours=1):
            data["count"] = 0
            
        data["count"] += 1
        data["last_failure"] = now
        
        return data["count"]
    
    async def reset_failure_count(self, key: str) -> None:
        """Reset failure count for a key"""
        if key in self.failures:
            del self.failures[key]


class AdvancedRateLimiter:
    """Advanced rate limiter with progressive delays"""
    
    def __init__(
        self,
        storage: Optional[InMemoryRateLimitStorage] = None,
        whitelist_ips: Optional[List[str]] = None,
        default_rules: Optional[Dict[str, RateLimitRule]] = None
    ):
        # Initialize storage
        if storage:
            self.storage = storage
        else:
            logger.info("Using in-memory storage for rate limiting")
            self.storage = InMemoryRateLimitStorage()
        
        # Whitelist configuration
        self.whitelist_ips = set(whitelist_ips or [])
        
        # Default rate limiting rules
        self.rules = default_rules or self._get_default_rules()
        
        logger.info(f"AdvancedRateLimiter initialized with {type(self.storage).__name__}")
    
    def _get_default_rules(self) -> Dict[str, RateLimitRule]:
        """Get default rate limiting rules"""
        return {
            "anonymous_global": RateLimitRule(
                name="anonymous_global",
                limit=100,
                window=60,
                action=RateLimitAction.THROTTLE
            ),
            "authenticated_global": RateLimitRule(
                name="authenticated_global", 
                limit=1000,
                window=60,
                action=RateLimitAction.THROTTLE
            ),
            "login_attempts": RateLimitRule(
                name="login_attempts",
                limit=5,
                window=3600,  # 1 hour window
                action=RateLimitAction.PROGRESSIVE_DELAY,
                progressive_multiplier=2.0,
                max_delay=300,  # Max 5 minutes delay
                block_duration=3600  # Block for 1 hour after too many attempts
            ),
            "register_attempts": RateLimitRule(
                name="register_attempts",
                limit=3,
                window=300,  # 5 minutes window
                action=RateLimitAction.THROTTLE
            ),
            "password_reset_attempts": RateLimitRule(
                name="password_reset_attempts",
                limit=3,
                window=3600,  # 1 hour window
                action=RateLimitAction.THROTTLE
            ),
            "api_endpoint": RateLimitRule(
                name="api_endpoint",
                limit=100,
                window=60,
                action=RateLimitAction.THROTTLE
            )
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection IP
        if request.client and hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def _is_whitelisted(self, client_ip: str) -> bool:
        """Check if client IP is whitelisted"""
        return client_ip in self.whitelist_ips
    
    async def check_rate_limit(
        self,
        request: Request,
        rule_name: str,
        custom_rule: Optional[RateLimitRule] = None
    ) -> RateLimitResult:
        """Check if request should be rate limited"""
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Skip rate limiting for whitelisted IPs
        if self._is_whitelisted(client_ip):
            logger.debug(f"Skipping rate limit for whitelisted IP: {client_ip}")
            return RateLimitResult(
                allowed=True,
                status=RateLimitStatus(
                    key="whitelisted",
                    rule_name=rule_name,
                    current_count=0,
                    limit=999999,
                    window_start=datetime.utcnow(),
                    window_end=datetime.utcnow() + timedelta(hours=1)
                )
            )
        
        # Get rule
        rule = custom_rule or self.rules.get(rule_name)
        if not rule:
            logger.warning(f"Rate limit rule '{rule_name}' not found")
            empty_status = RateLimitStatus(
                key="no-rule",
                rule_name=rule_name,
                current_count=0,
                limit=0,
                window_start=datetime.utcnow(),
                window_end=datetime.utcnow()
            )
            return RateLimitResult(allowed=True, status=empty_status)
        
        # Generate key
        key = f"ip:{client_ip}:{rule_name}"
        
        # Check if blocked
        is_blocked, block_expires = await self.storage.is_blocked(key)
        if is_blocked:
            if block_expires:
                retry_after = int((block_expires - datetime.utcnow()).total_seconds())
                message = f"IP blocked until {block_expires.isoformat()}"
            else:
                retry_after = 0
                message = "IP blocked"
            
            return RateLimitResult(
                allowed=False,
                status=RateLimitStatus(
                    key=key,
                    rule_name=rule_name,
                    current_count=rule.limit,
                    limit=rule.limit,
                    window_start=datetime.utcnow(),
                    window_end=datetime.utcnow() + timedelta(seconds=rule.window),
                    is_blocked=True,
                    block_expires=block_expires
                ),
                retry_after=retry_after,
                message=message
            )
        
        # Get current count
        current_count, window_start = await self.storage.get_count(key, rule.window)
        window_end = window_start + timedelta(seconds=rule.window)
        
        # Create status
        status = RateLimitStatus(
            key=key,
            rule_name=rule_name,
            current_count=current_count,
            limit=rule.limit,
            window_start=window_start,
            window_end=window_end
        )
        
        # Check if limit exceeded
        if current_count >= rule.limit:
            if rule.action == RateLimitAction.PROGRESSIVE_DELAY:
                # Get failure count for progressive delay
                failure_count = await self.storage.get_failure_count(key)
                delay = min(
                    int(rule.progressive_multiplier ** failure_count),
                    rule.max_delay
                )
                
                # Increment failure count
                await self.storage.increment_failure_count(key)
                
                # Block if configured
                if rule.block_duration and failure_count >= rule.limit:
                    await self.storage.set_block(key, rule.block_duration)
                    status.is_blocked = True
                    status.block_expires = datetime.utcnow() + timedelta(seconds=rule.block_duration)
                
                return RateLimitResult(
                    allowed=False,
                    status=status,
                    delay_seconds=delay,
                    retry_after=delay,
                    message=f"Rate limit exceeded. Progressive delay: {delay}s"
                )
            
            else:
                # Return throttle response
                retry_after = int((window_end - datetime.utcnow()).total_seconds())
                return RateLimitResult(
                    allowed=False,
                    status=status,
                    retry_after=retry_after,
                    message="Rate limit exceeded"
                )
        
        # Request allowed, increment count
        new_count = await self.storage.increment_count(key, rule.window)
        status.current_count = new_count
        
        # Reset failure count on successful request (for progressive delay)
        if rule.action == RateLimitAction.PROGRESSIVE_DELAY:
            await self.storage.reset_failure_count(key)
        
        return RateLimitResult(allowed=True, status=status)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: AdvancedRateLimiter,
        enabled: bool = True,
        skip_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.enabled = enabled
        self.skip_paths = set(skip_paths or ["/health", "/metrics", "/docs", "/openapi.json"])
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through rate limiter"""
        
        # Skip rate limiting if disabled or path is in skip list
        if not self.enabled or request.url.path in self.skip_paths:
            return await call_next(request)
        
        # Determine rate limit rule based on endpoint
        rule_name = self._get_rule_for_endpoint(request)
        
        # Check rate limit
        result = await self.rate_limiter.check_rate_limit(request, rule_name)
        
        if not result.allowed:
            # Log security event for rate limit exceeded
            try:
                from middleware.security_monitor import log_rate_limit_event
                import uuid
                
                request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
                client_ip = self.rate_limiter._get_client_ip(request)
                
                await log_rate_limit_event(
                    request_id=request_id,
                    client_ip=client_ip,
                    endpoint=request.url.path,
                    rule_name=rule_name,
                    current_count=result.status.current_count,
                    limit=result.status.limit,
                    user_id=getattr(request.state, "user_id", None) if hasattr(request.state, "user_id") else None
                )
            except Exception as e:
                logger.warning(f"Failed to log rate limit security event: {str(e)}")
            
            # Add rate limit headers
            headers = {
                "X-RateLimit-Limit": str(result.status.limit),
                "X-RateLimit-Remaining": str(max(0, result.status.limit - result.status.current_count)),
                "X-RateLimit-Reset": str(int(result.status.window_end.timestamp())),
            }
            
            if result.retry_after:
                headers["Retry-After"] = str(result.retry_after)
            
            # Apply delay if specified
            if result.delay_seconds > 0:
                await asyncio.sleep(result.delay_seconds)
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": result.message or "Rate limit exceeded",
                    "retry_after": result.retry_after
                },
                headers=headers
            )
        
        # Add rate limit info headers to successful responses
        response = await call_next(request)
        
        if result.status:
            response.headers["X-RateLimit-Limit"] = str(result.status.limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, result.status.limit - result.status.current_count))
            response.headers["X-RateLimit-Reset"] = str(int(result.status.window_end.timestamp()))
        
        return response
    
    def _get_rule_for_endpoint(self, request: Request) -> str:
        """Determine which rate limit rule to apply based on endpoint"""
        path = request.url.path
        
        # Authentication endpoints - more specific handling
        if "/auth/login" in path:
            return "login_attempts"
        elif "/auth/register" in path:
            return "register_attempts"
        elif "/auth/reset-password" in path:
            return "password_reset_attempts"
        elif "/auth/" in path:
            return "authenticated_global" if self._is_authenticated(request) else "anonymous_global"
        elif "/api/" in path:
            return "api_endpoint"
        
        # Default rule based on authentication status
        return "authenticated_global" if self._is_authenticated(request) else "anonymous_global"
    
    def _is_authenticated(self, request: Request) -> bool:
        """Check if request is from authenticated user"""
        return hasattr(request.state, "user") and request.state.user is not None


def create_rate_limiter(
    storage: Optional[InMemoryRateLimitStorage] = None,
    whitelist_ips: Optional[List[str]] = None,
    custom_rules: Optional[Dict[str, RateLimitRule]] = None
) -> AdvancedRateLimiter:
    """Create and configure an AdvancedRateLimiter instance"""
    
    # Get whitelist IPs from environment
    if whitelist_ips is None:
        whitelist_env = os.getenv("RATE_LIMIT_WHITELIST_IPS", "")
        whitelist_ips = [ip.strip() for ip in whitelist_env.split(",") if ip.strip()]
    
    return AdvancedRateLimiter(
        storage=storage,
        whitelist_ips=whitelist_ips,
        default_rules=custom_rules
    )