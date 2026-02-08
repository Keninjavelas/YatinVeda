"""Enhanced global error handlers for FastAPI application with structured error responses."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from pydantic import ValidationError
import logging
import traceback
from typing import Union, Dict, Any
import time

logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    error_type: str,
    message: str,
    details: Union[Dict[str, Any], list, None] = None,
    request_id: str = None
) -> JSONResponse:
    """Create standardized error response.
    
    Args:
        status_code: HTTP status code
        error_type: Error type identifier
        message: Human-readable error message
        details: Additional error details (optional)
        request_id: Request ID for tracing (optional)
        
    Returns:
        JSONResponse with standardized error format
    """
    error_data = {
        "error": {
            "type": error_type,
            "message": message,
            "status_code": status_code,
            "timestamp": time.time(),
        }
    }
    
    if details:
        error_data["error"]["details"] = details
    
    if request_id:
        error_data["error"]["request_id"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI request validation errors with detailed field information.
    
    Provides clear feedback on validation failures for better client-side handling.
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Format validation errors for better readability
    formatted_errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(
        f"Validation error on {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "errors": formatted_errors,
            "path": request.url.path,
        }
    )
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type="validation_error",
        message="Request validation failed",
        details=formatted_errors,
        request_id=request_id
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions with consistent formatting."""
    request_id = getattr(request.state, "request_id", None)
    
    # Log different severities based on status code
    if exc.status_code >= 500:
        logger.error(
            f"HTTP {exc.status_code} on {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "status_code": exc.status_code,
                "detail": exc.detail,
            }
        )
    elif exc.status_code >= 400:
        logger.warning(
            f"HTTP {exc.status_code} on {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "status_code": exc.status_code,
                "detail": exc.detail,
            }
        )
    
    return create_error_response(
        status_code=exc.status_code,
        error_type="http_error",
        message=exc.detail if isinstance(exc.detail, str) else "HTTP error occurred",
        details=exc.detail if not isinstance(exc.detail, str) else None,
        request_id=request_id
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy-related errors with specific error types."""
    request_id = getattr(request.state, "request_id", None)
    
    # Determine specific database error type
    if isinstance(exc, IntegrityError):
        error_type = "database_integrity_error"
        message = "Database constraint violation. The data conflicts with existing records."
        status_code = status.HTTP_409_CONFLICT
        
        # Extract constraint name if available
        details = None
        if hasattr(exc, 'orig') and exc.orig:
            details = {"constraint": str(exc.orig)}
    
    elif isinstance(exc, OperationalError):
        error_type = "database_operational_error"
        message = "Database operation failed. Please try again."
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        details = None
    
    else:
        error_type = "database_error"
        message = "A database error occurred. Please try again later."
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        details = None
    
    logger.error(
        f"Database error on {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "error_type": type(exc).__name__,
            "path": request.url.path,
        },
        exc_info=True
    )
    
    return create_error_response(
        status_code=status_code,
        error_type=error_type,
        message=message,
        details=details,
        request_id=request_id
    )


async def pydantic_validation_error_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors from manual schema validation."""
    request_id = getattr(request.state, "request_id", None)
    
    # Format Pydantic errors similar to FastAPI validation errors
    formatted_errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(
        f"Pydantic validation error on {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "errors": formatted_errors,
        }
    )
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type="schema_validation_error",
        message="Data validation failed",
        details=formatted_errors,
        request_id=request_id
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Fallback handler for uncaught exceptions with full error tracking."""
    request_id = getattr(request.state, "request_id", None)
    
    # Get full traceback for logging
    tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    
    logger.critical(
        f"Unhandled exception on {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": request.url.path,
            "traceback": tb_str,
        },
        exc_info=True
    )
    
    # Don't expose internal error details in production
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="internal_server_error",
        message="An unexpected error occurred. Please try again later.",
        details=None,  # Don't expose traceback to clients
        request_id=request_id
    )


__all__ = [
    "validation_exception_handler",
    "http_exception_handler",
    "database_exception_handler",
    "pydantic_validation_error_handler",
    "general_exception_handler",
    "create_error_response",
]
