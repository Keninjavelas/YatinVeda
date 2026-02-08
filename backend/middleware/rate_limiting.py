"""Rate limiting middleware for API endpoints.

Uses slowapi for request throttling to prevent abuse and ensure fair usage.
Supports per-user and per-IP rate limits with different tiers.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from typing import Callable


def get_user_or_ip(request: Request) -> str:
    """Get user ID if authenticated, otherwise fall back to IP address.
    
    This allows authenticated users to have consistent rate limits
    across different IPs, while anonymous users are limited by IP.
    """
    # Check if user is authenticated
    user_id = None
    if hasattr(request.state, "user"):
        user_id = request.state.user.get("user_id")
    
    # Return user-based identifier if authenticated
    if user_id:
        return f"user:{user_id}"
    
    # Fall back to IP address for anonymous requests
    return f"ip:{get_remote_address(request)}"


# Initialize limiter with custom key function
limiter = Limiter(
    key_func=get_user_or_ip,
    default_limits=["200/hour"],  # Default limit for all endpoints
    storage_uri="memory://",  # Use in-memory storage (consider Redis for production)
)


# Rate limit tiers for different endpoint types
class RateLimits:
    """Rate limit configurations for different endpoint tiers."""
    
    # Authentication endpoints (prevent brute force)
    AUTH_LOGIN = "5/minute"
    AUTH_REFRESH = "10/minute"
    AUTH_REGISTER = "3/minute"
    AUTH_PASSWORD_RESET = "3/hour"
    
    # Data retrieval (generous limits)
    READ_HEAVY = "100/minute"
    READ_MODERATE = "60/minute"
    READ_LIGHT = "30/minute"
    
    # Write operations (more restrictive)
    WRITE_HEAVY = "30/minute"
    WRITE_MODERATE = "20/minute"
    WRITE_LIGHT = "10/minute"
    
    # AI/LLM endpoints (expensive operations)
    AI_CHAT = "20/minute"
    AI_CHART_ANALYSIS = "10/minute"
    AI_PRESCRIPTION = "5/minute"
    
    # Payment operations (critical, very restrictive)
    PAYMENT_CREATE = "5/minute"
    PAYMENT_VERIFY = "10/minute"
    
    # File uploads (bandwidth intensive)
    FILE_UPLOAD = "10/minute"
    
    # Admin operations (moderate)
    ADMIN_OPERATIONS = "50/minute"
    
    # Community interactions
    POST_CREATE = "10/minute"
    COMMENT_CREATE = "30/minute"
    LIKE_ACTION = "60/minute"


def create_rate_limit_response(request: Request, exc: RateLimitExceeded) -> HTTPException:
    """Create a custom response for rate limit exceeded errors."""
    return HTTPException(
        status_code=429,
        detail={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.detail,
        },
        headers={"Retry-After": str(exc.detail)}
    )


# Decorator for applying rate limits to specific endpoints
def rate_limit(limit: str):
    """Apply rate limit to an endpoint.
    
    Usage:
        @router.post("/create")
        @rate_limit(RateLimits.WRITE_MODERATE)
        async def create_item():
            ...
    """
    def decorator(func: Callable):
        return limiter.limit(limit)(func)
    return decorator


# Export commonly used components
__all__ = [
    "limiter",
    "RateLimits",
    "rate_limit",
    "create_rate_limit_response",
    "get_user_or_ip",
]
