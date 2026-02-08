"""Health check endpoints for monitoring and orchestration.

Provides comprehensive health, readiness, and liveness endpoints
for monitoring tools, load balancers, and Kubernetes.
"""

from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import time
import psutil
import logging

from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])

# Track application start time
APP_START_TIME = time.time()


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall health status: healthy, degraded, unhealthy")
    timestamp: float = Field(..., description="Unix timestamp of health check")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    version: str = Field(default="1.0.0", description="Application version")
    checks: Dict[str, Any] = Field(..., description="Individual component health checks")


class ReadinessStatus(BaseModel):
    """Readiness check response model."""
    ready: bool = Field(..., description="Whether the application is ready to serve traffic")
    timestamp: float = Field(..., description="Unix timestamp of readiness check")
    checks: Dict[str, bool] = Field(..., description="Individual readiness checks")
    message: Optional[str] = Field(None, description="Additional information")


class LivenessStatus(BaseModel):
    """Liveness check response model."""
    alive: bool = Field(default=True, description="Whether the application is alive")
    timestamp: float = Field(..., description="Unix timestamp of liveness check")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")


def check_database_health(db: Session) -> Dict[str, Any]:
    """Check database connectivity and performance.
    
    Args:
        db: Database session
        
    Returns:
        Dict with database health information
    """
    try:
        start_time = time.time()
        # Simple query to check database responsiveness
        db.execute(text("SELECT 1"))
        query_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "status": "healthy",
            "response_time_ms": round(query_time, 2),
            "connected": True,
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
        }


def check_system_resources() -> Dict[str, Any]:
    """Check system resource usage.
    
    Returns:
        Dict with CPU, memory, and disk usage
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy" if cpu_percent < 90 and memory.percent < 90 else "degraded",
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "memory_available_mb": round(memory.available / (1024 * 1024), 2),
            "disk_percent": round(disk.percent, 2),
            "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        }
    except Exception as e:
        logger.error(f"System resource check failed: {e}", exc_info=True)
        return {
            "status": "unknown",
            "error": str(e),
        }


def check_cache_health() -> Dict[str, Any]:
    """Check caching system health.
    
    Returns:
        Dict with cache statistics
    """
    try:
        # Try Redis cache first
        try:
            from middleware.redis_cache import get_redis_cache
            cache = get_redis_cache()
            health = cache.health_check()
            stats = cache.get_stats()
            
            return {
                "status": "healthy" if health["healthy"] else "degraded",
                "backend": stats["backend"],
                "redis_available": stats.get("redis_available", False),
                "hit_rate": stats["hit_rate"],
                "total_entries": stats.get("entries", 0),
                "total_requests": stats["total_requests"],
            }
        except ImportError:
            # Fall back to in-memory cache
            from middleware.caching import get_cache
            cache = get_cache()
            stats = cache.get_stats()
            
            return {
                "status": "healthy",
                "backend": "in-memory",
                "redis_available": False,
                "hit_rate": stats["hit_rate"],
                "total_entries": stats["entries"],
                "total_requests": stats["total_requests"],
            }
    except Exception as e:
        logger.error(f"Cache health check failed: {e}", exc_info=True)
        return {
            "status": "degraded",
            "error": str(e),
        }


@router.get("/health", response_model=HealthStatus, status_code=status.HTTP_200_OK)
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check endpoint.
    
    Returns detailed health status of all system components.
    Used by monitoring tools for alerting and dashboards.
    
    Returns:
        HealthStatus with detailed component health
    """
    uptime = time.time() - APP_START_TIME
    
    # Perform component health checks
    checks = {
        "database": check_database_health(db),
        "system": check_system_resources(),
        "cache": check_cache_health(),
    }
    
    # Determine overall health status
    statuses = [check.get("status", "unknown") for check in checks.values()]
    
    if all(s == "healthy" for s in statuses):
        overall_status = "healthy"
        response_status = status.HTTP_200_OK
    elif any(s == "unhealthy" for s in statuses):
        overall_status = "unhealthy"
        response_status = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        overall_status = "degraded"
        response_status = status.HTTP_200_OK
    
    health_response = HealthStatus(
        status=overall_status,
        timestamp=time.time(),
        uptime_seconds=round(uptime, 2),
        version="1.0.0",
        checks=checks,
    )
    
    # Log unhealthy status
    if overall_status != "healthy":
        logger.warning(f"Health check returned {overall_status} status", extra={"checks": checks})
    
    return health_response


@router.get("/readiness", response_model=ReadinessStatus)
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check endpoint.
    
    Indicates whether the application is ready to serve traffic.
    Used by load balancers and orchestrators (Kubernetes) to route traffic.
    
    Returns 200 if ready, 503 if not ready.
    
    Returns:
        ReadinessStatus indicating if app is ready
    """
    checks = {}
    
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database readiness check failed: {e}")
        checks["database"] = False
    
    # Check if application has been running for minimum warmup time (5 seconds)
    uptime = time.time() - APP_START_TIME
    checks["warmup"] = uptime > 5
    
    # Check system resources
    try:
        memory = psutil.virtual_memory()
        checks["memory"] = memory.percent < 95  # Not critically low on memory
    except:
        checks["memory"] = True  # Assume OK if check fails
    
    # Determine readiness
    ready = all(checks.values())
    
    response = ReadinessStatus(
        ready=ready,
        timestamp=time.time(),
        checks=checks,
        message="Ready to serve traffic" if ready else "Not ready - some checks failed"
    )
    
    # Return 503 if not ready
    if not ready:
        logger.warning("Readiness check failed", extra={"checks": checks})
        return response
    
    return response


@router.get("/liveness", response_model=LivenessStatus, status_code=status.HTTP_200_OK)
async def liveness_check():
    """Liveness check endpoint.
    
    Simple check to verify the application is alive and responsive.
    Used by orchestrators (Kubernetes) to detect hung processes.
    
    This should always return 200 unless the application is completely frozen.
    
    Returns:
        LivenessStatus indicating app is alive
    """
    uptime = time.time() - APP_START_TIME
    
    return LivenessStatus(
        alive=True,
        timestamp=time.time(),
        uptime_seconds=round(uptime, 2),
    )


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def metrics_endpoint():
    """Expose application metrics for monitoring systems.
    
    Returns metrics in a simple JSON format.
    For production, consider using Prometheus format.
    
    Returns:
        Dict with application metrics
    """
    from middleware.request_logging import get_request_metrics
    from middleware.metrics import get_metrics as get_prometheus_metrics
    
    # Use the new metrics system
    metrics = get_prometheus_metrics()
    
    # Add uptime to the metrics
    uptime = time.time() - APP_START_TIME
    metrics["uptime_seconds"] = round(uptime, 2)
    
    return metrics


__all__ = [
    "router",
    "HealthStatus",
    "ReadinessStatus",
    "LivenessStatus",
]
