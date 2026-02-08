"""
Metrics and monitoring utilities for YatinVeda backend.

Implements basic metrics collection for monitoring and observability.
"""

import time
import logging
from collections import defaultdict, deque
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import psutil
import threading
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Define mock classes when prometheus_client is not available
    class MockMetric:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
        def inc(self, amount=1):
            pass
        def observe(self, value):
            pass
        def set(self, value):
            pass
    
    Counter = Histogram = Gauge = lambda *args, **kwargs: MockMetric()

logger = logging.getLogger(__name__)

# Prometheus metrics (will be no-op if prometheus_client not available)
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
) if PROMETHEUS_AVAILABLE else None

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
) if PROMETHEUS_AVAILABLE else None

ACTIVE_REQUESTS = Gauge(
    'http_active_requests',
    'Number of active HTTP requests'
) if PROMETHEUS_AVAILABLE else None

DB_CONNECTIONS = Gauge(
    'db_connections',
    'Number of database connections'
) if PROMETHEUS_AVAILABLE else None

USER_COUNT = Gauge(
    'app_users_total',
    'Total number of users'
) if PROMETHEUS_AVAILABLE else None

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'status']
) if PROMETHEUS_AVAILABLE else None

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits'
) if PROMETHEUS_AVAILABLE else None

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses'
) if PROMETHEUS_AVAILABLE else None


# Thread-safe metrics storage
class MetricsStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.reset_metrics()
    
    def reset_metrics(self):
        with self.lock:
            self.request_counts = defaultdict(int)
            self.request_durations = defaultdict(list)
            self.active_requests = 0
            self.total_requests = 0
            self.error_counts = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.db_connections = 0
            self.user_count = 0
    
    def increment_request(self, method: str, endpoint: str, status: int):
        with self.lock:
            self.request_counts[(method, endpoint, str(status))] += 1
            self.total_requests += 1
            if status >= 400:
                self.error_counts += 1
        
        # Record Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status)).inc()
            if status >= 400:
                ERROR_COUNT.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    
    def record_duration(self, method: str, endpoint: str, duration: float):
        with self.lock:
            self.request_durations[f"{method}:{endpoint}"].append(duration)
            # Keep only last 1000 samples
            if len(self.request_durations[f"{method}:{endpoint}"]) > 1000:
                self.request_durations[f"{method}:{endpoint}"] = self.request_durations[f"{method}:{endpoint}"][-1000:]
        
        # Record Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
    
    def increment_active_requests(self):
        with self.lock:
            self.active_requests += 1
        
        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE:
            ACTIVE_REQUESTS.inc()
    
    def decrement_active_requests(self):
        with self.lock:
            self.active_requests = max(0, self.active_requests - 1)
        
        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE:
            ACTIVE_REQUESTS.dec()
    
    def increment_cache_hit(self):
        with self.lock:
            self.cache_hits += 1
        
        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE:
            CACHE_HITS.inc()
    
    def increment_cache_miss(self):
        with self.lock:
            self.cache_misses += 1
        
        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE:
            CACHE_MISSES.inc()
    
    def set_db_connections(self, count: int):
        with self.lock:
            self.db_connections = count
        
        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE:
            DB_CONNECTIONS.set(count)
    
    def set_user_count(self, count: int):
        with self.lock:
            self.user_count = count
        
        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE:
            USER_COUNT.set(count)
    
    def get_metrics(self) -> Dict[str, Any]:
        with self.lock:
            # Calculate averages and percentiles
            avg_durations = {}
            for key, durations in self.request_durations.items():
                if durations:
                    avg_durations[key] = sum(durations) / len(durations)
            
            # Calculate p95 response time
            all_durations = []
            for durations in self.request_durations.values():
                all_durations.extend(durations)
            all_durations.sort()
            
            p95_duration = 0
            if all_durations:
                p95_idx = int(len(all_durations) * 0.95)
                p95_duration = all_durations[min(p95_idx, len(all_durations)-1)]
            
            error_rate = (self.error_counts / self.total_requests * 100) if self.total_requests > 0 else 0
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0,
                },
                "http": {
                    "total_requests": self.total_requests,
                    "active_requests": self.active_requests,
                    "error_count": self.error_counts,
                    "error_rate_percent": round(error_rate, 2),
                    "average_response_times": {k: round(v, 3) for k, v in avg_durations.items()},
                    "p95_response_time": round(p95_duration, 3),
                    "request_counts_by_endpoint": dict(self.request_counts),
                },
                "cache": {
                    "hits": self.cache_hits,
                    "misses": self.cache_misses,
                    "hit_rate": round((self.cache_hits / (self.cache_hits + self.cache_misses) * 100) if (self.cache_hits + self.cache_misses) > 0 else 0, 2)
                },
                "database": {
                    "connections": self.db_connections
                },
                "users": {
                    "total_users": self.user_count
                }
            }

# Global metrics store instance
METRICS_STORE = MetricsStore()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics."""
    
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        
        # Increment active requests
        METRICS_STORE.increment_active_requests()
        
        start_time = time.time()
        
        status_code = 500  # Default to 500 in case of exception
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Handle exceptions in the request
            raise
        finally:
            # Decrement active requests
            METRICS_STORE.decrement_active_requests()
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            METRICS_STORE.increment_request(method, path, status_code)
            METRICS_STORE.record_duration(method, path, duration)
        
        # Add response time header
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        return response


def get_metrics() -> Dict[str, Any]:
    """Get current metrics."""
    return METRICS_STORE.get_metrics()


def reset_metrics():
    """Reset all metrics to zero."""
    METRICS_STORE.reset_metrics()


def increment_cache_hit():
    """Increment cache hit counter."""
    METRICS_STORE.increment_cache_hit()


def increment_cache_miss():
    """Increment cache miss counter."""
    METRICS_STORE.increment_cache_miss()


def update_db_connections(count: int):
    """Update database connections count."""
    METRICS_STORE.set_db_connections(count)


def update_user_count(count: int):
    """Update user count."""
    METRICS_STORE.set_user_count(count)