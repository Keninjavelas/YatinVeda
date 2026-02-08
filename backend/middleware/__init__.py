"""Middleware package for YatinVeda backend.

This package provides comprehensive middleware for:
- Request/response logging with performance tracking
- Error handling with structured responses
- Caching for expensive operations
- Rate limiting to prevent abuse
- File upload handling and validation
- Response compression (gzip/brotli)
- Audit trail for compliance and security

Usage:
    from middleware import RequestLoggingMiddleware, get_request_metrics
    from middleware.error_handlers import (
        validation_exception_handler,
        database_exception_handler,
        general_exception_handler,
    )
    from middleware.caching import cached, CacheTTL
    from middleware.rate_limiting import limiter, RateLimits
    from middleware.compression import CompressionMiddleware
    from middleware.audit_trail import AuditTrailMiddleware, audit_database_operation
"""

from .request_logging import (
    RequestLoggingMiddleware,
    get_request_metrics,
    reset_request_metrics,
)
from .error_handlers import (
    validation_exception_handler,
    http_exception_handler,
    database_exception_handler,
    pydantic_validation_error_handler,
    general_exception_handler,
    create_error_response,
)
from .caching import (
    SimpleCache,
    get_cache,
    cached,
    CacheTTL,
    invalidate_cache,
    cache_guru_list,
    cache_popular_posts,
    cache_user_profile,
    cache_chart_calculation,
    cleanup_expired_cache,
)
from .rate_limiting import (
    limiter,
    RateLimits,
    rate_limit,
    create_rate_limit_response,
    get_user_or_ip,
)
from .file_upload import (
    FileUploadConfig,
    save_profile_picture,
    save_chart_image,
    save_document,
    delete_file,
    get_file_url,
    ensure_upload_directories,
)
from .compression import (
    CompressionMiddleware,
)
from .audit_trail import (
    AuditTrailMiddleware,
    AuditAction,
    get_audit_log,
    audit_database_operation,
    track_model_changes,
)

# Optional Redis cache (falls back to in-memory if unavailable)
try:
    from .redis_cache import (
        RedisCache,
        get_redis_cache,
        redis_cached,
    )
    REDIS_CACHE_AVAILABLE = True
except ImportError:
    REDIS_CACHE_AVAILABLE = False

# Optional OpenTelemetry tracing
try:
    from .tracing import (
        TracingConfig,
        setup_tracing,
        instrument_app,
        instrument_sqlalchemy,
        instrument_redis,
        create_span,
        add_span_attribute,
        add_span_event,
        record_exception,
    )
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

__all__ = [
    # Request Logging
    "RequestLoggingMiddleware",
    "get_request_metrics",
    "reset_request_metrics",
    
    # Error Handlers
    "validation_exception_handler",
    "http_exception_handler",
    "database_exception_handler",
    "pydantic_validation_error_handler",
    "general_exception_handler",
    "create_error_response",
    
    # Caching
    "SimpleCache",
    "get_cache",
    "cached",
    "CacheTTL",
    "invalidate_cache",
    "cache_guru_list",
    "cache_popular_posts",
    "cache_user_profile",
    "cache_chart_calculation",
    "cleanup_expired_cache",
    
    # Rate Limiting
    "limiter",
    "RateLimits",
    "rate_limit",
    "create_rate_limit_response",
    "get_user_or_ip",
    
    # File Upload
    "FileUploadConfig",
    "save_profile_picture",
    "save_chart_image",
    "save_document",
    "delete_file",
    "get_file_url",
    "ensure_upload_directories",
    
    # Compression
    "CompressionMiddleware",
    
    # Audit Trail
    "AuditTrailMiddleware",
    "AuditAction",
    "get_audit_log",
    "audit_database_operation",
    "track_model_changes",
]

# Add optional exports if available
if REDIS_CACHE_AVAILABLE:
    __all__.extend([
        "RedisCache",
        "get_redis_cache",
        "redis_cached",
    ])

if TRACING_AVAILABLE:
    __all__.extend([
        "TracingConfig",
        "setup_tracing",
        "instrument_app",
        "instrument_sqlalchemy",
        "instrument_redis",
        "create_span",
        "add_span_attribute",
        "add_span_event",
        "record_exception",
    ])
