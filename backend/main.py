"""
🌌 YatinVeda Backend - FastAPI Application
A hybrid, AI-assisted Vedic Astrology Intelligence Platform
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uuid
import asyncio
from datetime import datetime
from sqlalchemy import delete
from sqlalchemy.orm import Session
from database_config import engine
from models.database import RefreshToken
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import uvicorn
import os

# Advanced rate limiting support - disabled for now due to import issues
ADVANCED_RATE_LIMITER_AVAILABLE = False
# try:
#     from middleware.rate_limiter import (
#         AdvancedRateLimiter, 
#         RateLimitMiddleware, 
#         create_rate_limiter,
#         RateLimitRule,
#         RateLimitAction
#     )
#     ADVANCED_RATE_LIMITER_AVAILABLE = True
# except ImportError as e:
#     ADVANCED_RATE_LIMITER_AVAILABLE = False

# Optional slowapi support (rate limiting). In test environments or when the
# dependency is not installed, we gracefully degrade to no-op rate limiting so
# that imports and tests still work.
try:
    from slowapi.errors import RateLimitExceeded
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    SLOWAPI_AVAILABLE = True
except ModuleNotFoundError:
    RateLimitExceeded = Exception  # Fallback type for handler registration
    Limiter = None
    _rate_limit_exceeded_handler = None
    get_remote_address = None
    SLOWAPI_AVAILABLE = False

from config import settings
from database_config import init_db
from middleware.error_handlers import (
    validation_exception_handler,
    database_exception_handler,
    general_exception_handler
)
from middleware.request_logging import RequestLoggingMiddleware
from middleware.metrics import MetricsMiddleware
from middleware.prometheus_metrics import PrometheusMetricsMiddleware, register_metrics_with_app
from middleware.compression import CompressionMiddleware
from middleware.audit_trail import AuditTrailMiddleware
from middleware.security_headers import SecurityHeadersMiddleware, get_csp_report_endpoint
from logging_config import get_logger
from modules.bootstrap_admin import ensure_default_admin

# Get logger for main app
logger = get_logger(__name__)

# Initialize database
init_db()
# Ensure default admin user exists
ensure_default_admin()

# Set up OpenTelemetry tracing (optional)
try:
    from middleware.tracing import setup_tracing, instrument_app, instrument_sqlalchemy
    from database_config import engine
    
    tracing_enabled = setup_tracing()
    if tracing_enabled:
        instrument_sqlalchemy(engine)
        logger.info("OpenTelemetry tracing enabled")
except ImportError:
    logger.info("OpenTelemetry not available - tracing disabled")
except Exception as e:
    logger.warning(f"Failed to set up tracing: {e}")

# Rate limiter - create a mock in test mode or when rate limiting is unavailable
_testing = os.getenv("PYTEST_CURRENT_TEST") is not None or os.getenv("DISABLE_RATELIMIT") == "1"

# Initialize advanced rate limiter
advanced_rate_limiter = None
if not _testing and ADVANCED_RATE_LIMITER_AVAILABLE:
    try:
        # Create advanced rate limiter with Redis backend
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        whitelist_ips = []
        
        # Add localhost and common development IPs to whitelist in development
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "development":
            whitelist_ips = ["127.0.0.1", "::1", "localhost"]
        
        # Create custom rules for different endpoints
        custom_rules = {
            "login_attempts": RateLimitRule(
                name="login_attempts",
                limit=5,
                window=3600,  # 5 attempts per hour
                action=RateLimitAction.PROGRESSIVE_DELAY,
                progressive_multiplier=2.0,
                max_delay=300,  # Max 5 minutes delay
                block_duration=3600  # Block for 1 hour after limit
            ),
            "anonymous_global": RateLimitRule(
                name="anonymous_global",
                limit=100,
                window=60,  # 100 requests per minute
                action=RateLimitAction.THROTTLE
            ),
            "authenticated_global": RateLimitRule(
                name="authenticated_global",
                limit=1000,
                window=60,  # 1000 requests per minute
                action=RateLimitAction.THROTTLE
            ),
            "api_endpoint": RateLimitRule(
                name="api_endpoint",
                limit=100,
                window=60,  # 100 requests per minute per endpoint
                action=RateLimitAction.THROTTLE
            )
        }
        
        advanced_rate_limiter = create_rate_limiter(
            redis_url=redis_url,
            whitelist_ips=whitelist_ips,
            custom_rules=custom_rules
        )
        logger.info("Advanced rate limiter initialized with Redis backend")
        
    except Exception as e:
        logger.warning(f"Failed to initialize advanced rate limiter: {str(e)}")
        advanced_rate_limiter = None

# Fallback to slowapi if advanced rate limiter is not available
if _testing or not SLOWAPI_AVAILABLE:
    # Mock limiter that does nothing
    class MockLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

        def shared_limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

    limiter = MockLimiter()
elif not advanced_rate_limiter and SLOWAPI_AVAILABLE:
    # Use slowapi as fallback
    limiter = Limiter(key_func=get_remote_address)
    logger.info("Using slowapi rate limiter as fallback")
else:
    # Create mock limiter when using advanced rate limiter
    class MockLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

        def shared_limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

    limiter = MockLimiter()

# Import API routers
from api.v1 import guru_booking, payments, admin, auth, user_charts, profile, prescriptions, chat, community, health, mfa, security, security_testing

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A hybrid, AI-assisted Vedic Astrology Intelligence Platform",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter state (only when slowapi is installed and not testing)
if not _testing and SLOWAPI_AVAILABLE and _rate_limit_exceeded_handler is not None and not advanced_rate_limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add global exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Instrument FastAPI for tracing (if enabled)
try:
    from middleware.tracing import instrument_app
    instrument_app(app)
    logger.info("FastAPI instrumented for tracing")
except:
    pass

# Add compression middleware (should be early in the chain)
app.add_middleware(CompressionMiddleware, minimum_size=500, compression_level=6)

# Register Prometheus metrics with the app
try:
    register_metrics_with_app(app)
    logger.info("Prometheus metrics registered successfully")
except Exception as e:
    logger.error(f"Failed to register Prometheus metrics: {e}")

# Add advanced rate limiting middleware (should be early to catch abuse)
if advanced_rate_limiter and not _testing:
    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=advanced_rate_limiter,
        enabled=True,
        skip_paths=["/health", "/metrics", "/docs", "/openapi.json", "/", "/api/v1/health"]
    )
    logger.info("Advanced rate limiting middleware enabled")

# Add security headers middleware (should be early to ensure all responses have security headers)
environment = os.getenv("ENVIRONMENT", "development")
app.add_middleware(
    SecurityHeadersMiddleware,
    environment=environment,
    hsts_max_age=31536000,  # 1 year
    hsts_include_subdomains=True,
    hsts_preload=True,
    cookie_secure=environment != "development",
    cookie_samesite="strict" if environment == "production" else "lax",
    enable_testing_mode=environment == "staging"
)

# Add CSRF protection middleware (should be after security headers but before auth)
csrf_protection_enabled = os.getenv("CSRF_PROTECTION_ENABLED", "true").lower() == "true"
if csrf_protection_enabled and not _testing:
    try:
        from middleware.csrf_protection import CSRFMiddleware, initialize_csrf_protection
        
        # Initialize CSRF protection
        csrf_secret_key = os.getenv("CSRF_SECRET_KEY", os.getenv("SECRET_KEY", "default-csrf-secret"))
        csrf_token_lifetime = int(os.getenv("CSRF_TOKEN_LIFETIME", "3600"))
        csrf_double_submit = os.getenv("CSRF_DOUBLE_SUBMIT", "true").lower() == "true"
        
        # Define exempt paths (paths that don't need CSRF protection)
        csrf_exempt_paths = {
            "/health", "/docs", "/openapi.json", "/redoc", "/",
            "/api/v1/health", "/api/v1/auth/login", "/api/v1/auth/register",
            "/api/v1/security/csrf-token", "/uploads"
        }
        
        csrf_protection = initialize_csrf_protection(
            secret_key=csrf_secret_key,
            token_lifetime=csrf_token_lifetime,
            double_submit=csrf_double_submit,
            exempt_paths=csrf_exempt_paths
        )
        
        app.add_middleware(
            CSRFMiddleware,
            csrf_protection=csrf_protection,
            enabled=True,
            testing_mode=environment == "staging"
        )
        
        logger.info("CSRF protection middleware enabled")
        
    except Exception as e:
        logger.error(f"Failed to initialize CSRF protection: {str(e)}")
        if environment == "production":
            logger.error("CSRF protection is required in production")
            # In production, we might want to fail startup, but for now we'll continue
        else:
            logger.info("Continuing without CSRF protection in development mode")

# Add audit trail middleware (tracks user operations)
app.add_middleware(AuditTrailMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])  # Health checks (no auth required)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(mfa.router, tags=["Multi-Factor Authentication"])  # MFA endpoints
app.include_router(user_charts.router, prefix="/api/v1/charts", tags=["User Charts"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["Profile"])
app.include_router(prescriptions.router, prefix="/api/v1/prescriptions", tags=["Prescriptions"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Chat"])
app.include_router(community.router, prefix="/api/v1/community", tags=["Community"])
app.include_router(guru_booking.router, prefix="/api/v1", tags=["Guru Booking"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments & Wallet"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(security.router, prefix="/api/v1", tags=["Security Monitoring"])
app.include_router(security_testing.router, prefix="/api/v1", tags=["Security Testing"])

# Add CSP violation reporting endpoint
@app.post("/api/v1/security/csp-report")
async def csp_violation_report(request: Request):
    """Endpoint to receive Content Security Policy violation reports"""
    csp_endpoint = get_csp_report_endpoint()
    return await csp_endpoint(request)

# Serve uploaded files as static content
from fastapi.staticfiles import StaticFiles
uploads_dir = "uploads"
if os.path.exists(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# Middleware to trust X-Forwarded-* headers from reverse proxy
@app.middleware("http")
async def proxy_headers_middleware(request: Request, call_next):
    # Extract forwarded headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    forwarded_proto = request.headers.get("X-Forwarded-Proto")
    forwarded_host = request.headers.get("X-Forwarded-Host")
    
    # Update request scope if headers present
    if forwarded_for:
        # Take the first IP in the chain
        client_ip = forwarded_for.split(",")[0].strip()
        if request.client:
            request.scope["client"] = (client_ip, request.client.port)
    
    if forwarded_proto:
        request.scope["scheme"] = forwarded_proto
    
    if forwarded_host:
        request.scope["server"] = (forwarded_host, request.scope.get("server", ("localhost", 80))[1])
    
    response = await call_next(request)
    return response


# Simple correlation ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Background task: periodic cleanup of expired refresh tokens
# Enhanced with APScheduler for production readiness
_cleanup_scheduler = None

async def cleanup_expired_refresh_tokens_task():
    """Enhanced cleanup task with proper error handling and logging"""
    try:
        with Session(bind=engine) as session:
            now = datetime.utcnow()
            result = session.execute(
                delete(RefreshToken).where(RefreshToken.expires_at < now)
            )
            session.commit()
            if result.rowcount > 0:
                logger.info(f"Cleaned up {result.rowcount} expired refresh tokens")
    except Exception as e:
        logger.error(f"Error during token cleanup: {str(e)}")
        # Don't re-raise to prevent scheduler from stopping

async def initialize_cleanup_scheduler():
    """Initialize APScheduler for production-grade cleanup scheduling"""
    global _cleanup_scheduler
    
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        import os
        
        # Configure cleanup interval (default 1 hour)
        cleanup_interval = int(os.getenv("CLEANUP_INTERVAL_HOURS", "1"))
        cleanup_minutes = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "0"))
        
        # Use AsyncIOScheduler for proper async integration
        _cleanup_scheduler = AsyncIOScheduler()
        
        # Add job with configurable interval
        if cleanup_minutes > 0:
            # Use minutes for development/testing
            _cleanup_scheduler.add_job(
                cleanup_expired_refresh_tokens_task,
                IntervalTrigger(minutes=cleanup_minutes),
                id="refresh_token_cleanup",
                name="Expired Refresh Token Cleanup",
                misfire_grace_time=300,
                max_instances=1
            )
        else:
            # Use hours for production (default 1 hour)
            _cleanup_scheduler.add_job(
                cleanup_expired_refresh_tokens_task,
                IntervalTrigger(hours=cleanup_interval),
                id="refresh_token_cleanup",
                name="Expired Refresh Token Cleanup",
                misfire_grace_time=900,
                max_instances=1
            )
        
        # Add other cleanup tasks as needed
        _cleanup_scheduler.add_job(
            cleanup_database_orphans,
            IntervalTrigger(hours=24),
            id="database_cleanup",
            name="Database Orphan Record Cleanup",
            misfire_grace_time=3600,
            max_instances=1
        )
        
        _cleanup_scheduler.start()
        logger.info(f"Cleanup scheduler started with {cleanup_interval}h interval")
        
    except ImportError:
        logger.warning("APScheduler not installed, using fallback asyncio task")
        # Fallback to original asyncio task
        asyncio.create_task(cleanup_expired_refresh_tokens_fallback())
    except Exception as e:
        logger.error(f"Failed to initialize cleanup scheduler: {str(e)}")
        # Fallback to original asyncio task
        asyncio.create_task(cleanup_expired_refresh_tokens_fallback())

async def cleanup_expired_refresh_tokens_fallback():
    """Fallback cleanup task using asyncio (original implementation)"""
    while True:
        try:
            await cleanup_expired_refresh_tokens_task()
        except Exception as e:
            logger.error(f"Fallback cleanup error: {str(e)}")
        # Configurable sleep interval
        import os
        sleep_interval = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "3600"))
        await asyncio.sleep(sleep_interval)

async def cleanup_database_orphans():
    """Clean up orphaned database records"""
    try:
        with Session(bind=engine) as session:
            # Clean up orphaned session records
            from models.database import SessionModel
            result = session.execute(
                delete(SessionModel).where(SessionModel.expires_at < datetime.utcnow())
            )
            session.commit()
            if result.rowcount > 0:
                logger.info(f"Cleaned up {result.rowcount} expired sessions")
    except Exception as e:
        logger.error(f"Database cleanup error: {str(e)}")


@app.on_event("startup")
async def startup_tasks():
    """Initialize application on startup"""
    # Initialize security monitoring
    security_monitor = None
    try:
        from middleware.security_monitor import initialize_security_monitor
        import os
        
        webhook_url = os.getenv("SECURITY_ALERT_WEBHOOK")
        log_level = os.getenv("SECURITY_LOG_LEVEL", "INFO")
        
        security_monitor = initialize_security_monitor(
            alert_webhook=webhook_url,
            log_level=log_level,
            correlation_tracking=True
        )
        
        logger.info("Security monitoring initialized")
        if webhook_url:
            logger.info(f"Security alert webhook configured: {webhook_url}")
        else:
            logger.info("Security alert webhook not configured")
            
    except Exception as e:
        logger.error(f"Failed to initialize security monitoring: {str(e)}")
        # Don't fail startup for security monitoring issues in development
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production":
            logger.error("Security monitoring is required in production")
            # In production, we might want to fail startup, but for now we'll continue
        else:
            logger.info("Continuing without security monitoring in development mode")
    
    # Initialize security testing with all security components
    try:
        from modules.security_testing import initialize_security_testing
        from modules.certificate_manager import get_certificate_manager
        from modules.production_security import get_production_security_config
        from middleware.csrf_protection import get_csrf_protection
        
        # Get security components
        certificate_manager = None
        try:
            certificate_manager = get_certificate_manager()
        except:
            logger.info("Certificate manager not available for security testing")
        
        csrf_protection = None
        try:
            csrf_protection = get_csrf_protection()
        except:
            logger.info("CSRF protection not available for security testing")
        
        production_security_config = None
        try:
            production_security_config = get_production_security_config()
        except:
            logger.info("Production security config not available for security testing")
        
        # Initialize security testing
        health_checker, testing_utilities = initialize_security_testing(
            certificate_manager=certificate_manager,
            rate_limiter=advanced_rate_limiter,
            csrf_protection=csrf_protection,
            security_monitor=security_monitor,
            production_security_config=production_security_config
        )
        
        logger.info("Security testing and health checks initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize security testing: {str(e)}")
        # Don't fail startup for security testing issues in development
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production":
            logger.error("Security testing is required in production")
        else:
            logger.info("Continuing without security testing in development mode")
    
    # Initialize enhanced cleanup scheduler
    await initialize_cleanup_scheduler()
    
    # Initialize SSL certificates if enabled
    try:
        from modules.certificate_manager import initialize_certificates, check_and_renew_certificates
        
        # Initialize certificates for configured domains
        await initialize_certificates()
        
        # Start certificate renewal task (check every 12 hours)
        async def certificate_renewal_task():
            while True:
                try:
                    await check_and_renew_certificates()
                except Exception as e:
                    logger.error(f"Certificate renewal task error: {str(e)}")
                await asyncio.sleep(43200)  # 12 hours
        
        asyncio.create_task(certificate_renewal_task())
        logger.info("Certificate management initialized")
        
    except Exception as e:
        logger.warning(f"Certificate management initialization failed: {str(e)}")
        # Don't fail startup for certificate issues in development
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production":
            logger.error("Certificate initialization is required in production")
            # In production, we might want to fail startup, but for now we'll continue
            # raise RuntimeError(f"Certificate initialization failed: {str(e)}")
        else:
            logger.info("Continuing without certificate management in development mode")

@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown handler"""
    global _cleanup_scheduler
    if _cleanup_scheduler:
        try:
            _cleanup_scheduler.shutdown(wait=True)
            logger.info("Cleanup scheduler shut down gracefully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {str(e)}")
    
    # Final cleanup run
    try:
        await cleanup_expired_refresh_tokens_task()
        logger.info("Final cleanup completed")
    except Exception as e:
        logger.error(f"Error during final cleanup: {str(e)}")

# Health check endpoint
@app.get("/")
@limiter.limit("10/minute")
async def root(request: Request):
    logger.info("Root endpoint accessed")
    return {
        "message": "🌌 Welcome to YatinVeda API",
        "version": settings.VERSION,
        "status": "active",
        "docs": "/docs"
    }

if __name__ == "__main__":
    logger.info(f"Starting YatinVeda Backend v{settings.VERSION}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info("Host: 0.0.0.0:8000")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.RELOAD,
        log_level="info"  # Use string directly for uvicorn
    )


