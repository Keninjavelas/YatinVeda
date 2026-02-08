"""Enhanced request logging middleware with performance tracking and structured logging."""

import logging
import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
import json

logger = logging.getLogger(__name__)

# Request metrics tracking
request_metrics = {
    "total_requests": 0,
    "total_errors": 0,
    "by_method": {},
    "by_path": {},
    "by_status": {},
    "slow_requests": [],  # Track requests > 1s
}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced request logging with performance metrics and structured logging.

    Features:
    - Request/response timing
    - Unique request IDs for tracing
    - Structured logging with JSON support
    - Performance metrics tracking
    - Slow request detection
    - Error rate monitoring
    """

    def __init__(self, app: ASGIApp, log_json: bool = False, slow_threshold: float = 1.0):
        """Initialize logging middleware.
        
        Args:
            app: ASGI application
            log_json: Whether to log in JSON format
            slow_threshold: Threshold in seconds for slow request warnings (default: 1.0s)
        """
        super().__init__(app)
        self.log_json = log_json
        self.slow_threshold = slow_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details with timing."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Track request metrics
        request_metrics["total_requests"] += 1
        request_metrics["by_method"][method] = request_metrics["by_method"].get(method, 0) + 1
        request_metrics["by_path"][path] = request_metrics["by_path"].get(path, 0) + 1
        
        # Process request and handle errors
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            
            # Track error rate
            if status_code >= 400:
                request_metrics["total_errors"] += 1
            
        except Exception as exc:
            # Log exception and track error
            logger.error(
                "Request processing failed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "error": str(exc),
                },
                exc_info=True
            )
            request_metrics["total_errors"] += 1
            raise
        
        # Calculate processing time
        duration = time.time() - start_time
        duration_ms = round(duration * 1000, 2)
        
        # Track slow requests
        if duration > self.slow_threshold:
            slow_request = {
                "request_id": request_id,
                "method": method,
                "path": path,
                "duration": duration_ms,
                "timestamp": time.time(),
            }
            request_metrics["slow_requests"].append(slow_request)
            # Keep only last 100 slow requests
            if len(request_metrics["slow_requests"]) > 100:
                request_metrics["slow_requests"].pop(0)
        
        # Track status code metrics
        status_key = f"{status_code // 100}xx"
        request_metrics["by_status"][status_key] = request_metrics["by_status"].get(status_key, 0) + 1
        
        # Add timing and request ID headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        
        # Structured logging
        log_data = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "user_agent": user_agent,
        }
        
        # Log based on status code severity
        if status_code >= 500:
            log_level = logging.ERROR
            log_message = f"{method} {path} - 5xx Server Error"
        elif status_code >= 400:
            log_level = logging.WARNING
            log_message = f"{method} {path} - 4xx Client Error"
        elif duration > self.slow_threshold:
            log_level = logging.WARNING
            log_message = f"{method} {path} - Slow Request ({duration_ms}ms)"
        else:
            log_level = logging.INFO
            log_message = f"{method} {path} - {status_code}"
        
        # Log in JSON or standard format
        if self.log_json:
            logger.log(log_level, json.dumps(log_data))
        else:
            logger.log(
                log_level,
                f"{log_message} [{request_id}] {duration_ms}ms",
                extra=log_data
            )
        
        return response


def get_request_metrics() -> dict:
    """Get current request metrics for monitoring.
    
    Returns:
        Dictionary with request statistics
    """
    total = request_metrics["total_requests"]
    errors = request_metrics["total_errors"]
    error_rate = (errors / total * 100) if total > 0 else 0
    
    return {
        "total_requests": total,
        "total_errors": errors,
        "error_rate_percent": round(error_rate, 2),
        "requests_by_method": request_metrics["by_method"],
        "requests_by_path": dict(sorted(
            request_metrics["by_path"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]),  # Top 20 paths
        "requests_by_status": request_metrics["by_status"],
        "recent_slow_requests": request_metrics["slow_requests"][-10:],  # Last 10 slow requests
    }


def reset_request_metrics() -> None:
    """Reset request metrics (useful for testing or periodic resets)."""
    global request_metrics
    request_metrics = {
        "total_requests": 0,
        "total_errors": 0,
        "by_method": {},
        "by_path": {},
        "by_status": {},
        "slow_requests": [],
    }


__all__ = [
    "RequestLoggingMiddleware",
    "get_request_metrics",
    "reset_request_metrics",
]
