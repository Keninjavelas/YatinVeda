"""
Prometheus metrics integration for YatinVeda backend.

Implements Prometheus-compatible metrics collection and export for monitoring.
"""

import time
import logging
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import psutil
import threading

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
    logger = logging.getLogger(__name__)
except ImportError:
    PROMETHEUS_AVAILABLE = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("prometheus_client not available - metrics will be collected but not exported in Prometheus format")

# Global Prometheus metrics (will be no-ops if prometheus_client not available)
if PROMETHEUS_AVAILABLE:
    # HTTP request metrics
    REQUEST_COUNT = Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status']
    )

    REQUEST_DURATION = Histogram(
        'http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['method', 'endpoint']
    )

    ACTIVE_REQUESTS = Gauge(
        'http_active_requests',
        'Number of active HTTP requests'
    )

    # Database metrics
    DB_CONNECTIONS = Gauge(
        'db_connections',
        'Number of database connections'
    )

    # User metrics
    USER_COUNT = Gauge(
        'app_users_total',
        'Total number of users'
    )

    # Error metrics
    ERROR_COUNT = Counter(
        'http_errors_total',
        'Total HTTP errors',
        ['method', 'endpoint', 'status']
    )

    # Cache metrics
    CACHE_HITS = Counter(
        'cache_hits_total',
        'Total cache hits'
    )

    CACHE_MISSES = Counter(
        'cache_misses_total',
        'Total cache misses'
    )
else:
    # Define no-op versions when prometheus is not available
    class NoOpMetric:
        def labels(self, **kwargs):
            return self
        
        def inc(self, amount=1):
            pass
        
        def dec(self, amount=1):
            pass
        
        def observe(self, value):
            pass
        
        def set(self, value):
            pass

    REQUEST_COUNT = NoOpMetric()
    REQUEST_DURATION = NoOpMetric()
    ACTIVE_REQUESTS = NoOpMetric()
    DB_CONNECTIONS = NoOpMetric()
    USER_COUNT = NoOpMetric()
    ERROR_COUNT = NoOpMetric()
    CACHE_HITS = NoOpMetric()
    CACHE_MISSES = NoOpMetric()


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect and expose Prometheus metrics."""
    
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        
        # Increment active requests
        ACTIVE_REQUESTS.inc()
        
        start_time = time.time()
        
        status_code = 500  # Default to 500 in case of exception
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Handle exceptions in the request
            status_code = 500
            raise
        finally:
            # Decrement active requests
            ACTIVE_REQUESTS.dec()
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            REQUEST_COUNT.labels(method=method, endpoint=path, status=str(status_code)).inc()
            REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)
            
            if status_code >= 400:
                ERROR_COUNT.labels(method=method, endpoint=path, status=str(status_code)).inc()
        
        # Add response time header
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        return response


def get_prometheus_metrics():
    """Get metrics in Prometheus format."""
    if PROMETHEUS_AVAILABLE:
        return generate_latest().decode('utf-8')
    else:
        # Return a simple text representation when prometheus is not available
        # This is just a placeholder since the actual metrics aren't collected without prometheus
        return "# No Prometheus metrics available (prometheus-client not installed)\n"


def increment_cache_hit():
    """Increment cache hit counter."""
    CACHE_HITS.inc()


def increment_cache_miss():
    """Increment cache miss counter."""
    CACHE_MISSES.inc()


def update_db_connections(count: int):
    """Update database connections count."""
    DB_CONNECTIONS.set(count)


def update_user_count(count: int):
    """Update user count."""
    USER_COUNT.set(count)


def register_metrics_with_app(app):
    """Register metrics endpoint with FastAPI app."""
    if PROMETHEUS_AVAILABLE:
        from fastapi import APIRouter
        
        router = APIRouter()
        
        @router.get("/metrics", tags=["monitoring"])
        async def metrics():
            """Prometheus metrics endpoint."""
            return Response(
                content=get_prometheus_metrics(),
                media_type=CONTENT_TYPE_LATEST
            )
        
        app.include_router(router)
        logger.info("Prometheus metrics endpoint registered at /metrics")
    else:
        logger.warning("Prometheus metrics not available - prometheus-client package not installed")


# Initialize metrics
def init_metrics():
    """Initialize Prometheus metrics."""
    if PROMETHEUS_AVAILABLE:
        logger.info("Prometheus metrics initialized")
    else:
        logger.info("Prometheus metrics not available - prometheus-client package not installed")


# Call init on import
init_metrics()