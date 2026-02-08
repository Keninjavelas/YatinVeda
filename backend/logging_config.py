"""Logging configuration for YatinVeda backend.

Provides structured logging with JSON format for production environments.
Supports correlation IDs and different log levels for scalability.
"""

import logging
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id
        
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        
        # Add any other extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "lineno", "funcName", "created", 
                          "msecs", "relativeCreated", "thread", "threadName", 
                          "processName", "process", "correlation_id", "user_id", "request_id"]:
                if value is not None:
                    log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger with structured logging.

    Uses JSON format in production, simple format in development.
    """
    logger = logging.getLogger(name)
    
    # Prevent adding multiple handlers
    if logger.handlers:
        return logger
    
    # Determine environment
    environment = os.getenv("ENVIRONMENT", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Set log level
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Create handler
    handler = logging.StreamHandler()
    
    if environment == "production":
        # Use JSON formatter for production
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        logger.info("Using structured JSON logging for production")
    else:
        # Use simple format for development
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.info("Using development logging format")
    
    logger.addHandler(handler)
    logger.propagate = False  # Prevent duplicate logs
    
    return logger


# Auth-specific logger
auth_logger = get_logger("auth")


def log_auth_event(event_type: str, username: Optional[str] = None, success: bool = True, details: Optional[str] = None):
    """Log authentication events for auditing with structured data"""
    level = logging.INFO if success else logging.WARNING
    
    # Create structured log data
    log_data = {
        "event_type": event_type,
        "success": success,
        "username": username,
        "details": details
    }
    
    # Remove None values
    log_data = {k: v for k, v in log_data.items() if v is not None}
    
    # Log with extra structured data
    auth_logger.log(level, f"Auth event: {event_type}", extra=log_data)
