"""Audit trail middleware for tracking and logging all database operations.

Provides comprehensive audit logging for compliance, security, and debugging.
Tracks CRUD operations with user context, request details, and change history.
Persists entries to the database via the AuditLogEntry model.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Audit action types."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ACCESS_DENIED = "ACCESS_DENIED"


class AuditLog:
    """Database-backed audit log storage.
    
    Persists audit entries to the audit_log_entries table via SQLAlchemy.
    Falls back to file logger if DB write fails.
    """
    
    def add(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
    ):
        """Add audit log entry to the database."""
        # Always emit to application logger
        log_message = f"AUDIT: {action.value} {resource_type}"
        if resource_id:
            log_message += f" #{resource_id}"
        if user_email:
            log_message += f" by {user_email}"
        logger.info(log_message)

        # Persist to database
        try:
            from database import SessionLocal
            from models.database import AuditLogEntry

            db = SessionLocal()
            try:
                entry = AuditLogEntry(
                    action=action.value,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    user_id=user_id,
                    user_email=user_email,
                    ip_address=ip_address,
                    request_id=request_id,
                    changes=changes,
                    metadata_=metadata,
                    status=status,
                    error_message=error_message,
                )
                db.add(entry)
                db.commit()
            except Exception:
                db.rollback()
                logger.warning("Failed to persist audit log entry to DB", exc_info=True)
            finally:
                db.close()
        except Exception:
            logger.warning("Failed to obtain DB session for audit log", exc_info=True)
    
    def get_logs(
        self,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query audit logs from the database."""
        try:
            from database import SessionLocal
            from models.database import AuditLogEntry

            db = SessionLocal()
            try:
                query = db.query(AuditLogEntry)
                if user_id is not None:
                    query = query.filter(AuditLogEntry.user_id == user_id)
                if resource_type is not None:
                    query = query.filter(AuditLogEntry.resource_type == resource_type)
                if action is not None:
                    query = query.filter(AuditLogEntry.action == action.value)
                if start_date is not None:
                    query = query.filter(AuditLogEntry.timestamp >= start_date)
                if end_date is not None:
                    query = query.filter(AuditLogEntry.timestamp <= end_date)

                rows = query.order_by(AuditLogEntry.timestamp.desc()).limit(limit).all()
                return [
                    {
                        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                        "action": r.action,
                        "resource_type": r.resource_type,
                        "resource_id": r.resource_id,
                        "user_id": r.user_id,
                        "user_email": r.user_email,
                        "ip_address": r.ip_address,
                        "request_id": r.request_id,
                        "changes": r.changes,
                        "metadata": r.metadata_,
                        "status": r.status,
                        "error_message": r.error_message,
                    }
                    for r in rows
                ]
            finally:
                db.close()
        except Exception:
            logger.warning("Failed to query audit logs from DB", exc_info=True)
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics from the database."""
        try:
            from database import SessionLocal
            from models.database import AuditLogEntry
            from sqlalchemy import func

            db = SessionLocal()
            try:
                total = db.query(func.count(AuditLogEntry.id)).scalar() or 0
                actions = dict(
                    db.query(AuditLogEntry.action, func.count(AuditLogEntry.id))
                    .group_by(AuditLogEntry.action)
                    .all()
                )
                resources = dict(
                    db.query(AuditLogEntry.resource_type, func.count(AuditLogEntry.id))
                    .group_by(AuditLogEntry.resource_type)
                    .all()
                )
                unique_users = (
                    db.query(func.count(func.distinct(AuditLogEntry.user_id)))
                    .filter(AuditLogEntry.user_id.isnot(None))
                    .scalar()
                    or 0
                )
                return {
                    "total_logs": total,
                    "by_action": actions,
                    "by_resource": resources,
                    "unique_users": unique_users,
                }
            finally:
                db.close()
        except Exception:
            logger.warning("Failed to get audit stats from DB", exc_info=True)
            return {"total_logs": 0, "by_action": {}, "by_resource": {}, "unique_users": 0}


# Global audit log instance
_audit_log = AuditLog()


def get_audit_log() -> AuditLog:
    """Get global audit log instance."""
    return _audit_log


class AuditTrailMiddleware(BaseHTTPMiddleware):
    """Middleware for audit trail logging.
    
    Captures user context from requests and tracks authenticated operations.
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request and track audit trail.
        
        Args:
            request: Incoming request
            call_next: Next middleware in chain
            
        Returns:
            Response from downstream
        """
        # Extract user context from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        user_email = getattr(request.state, "user_email", None)
        
        # Get IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None
        
        # Get request ID
        request_id = request.headers.get("X-Request-ID")
        
        # Store context in request state for use in route handlers
        request.state.audit_context = {
            "user_id": user_id,
            "user_email": user_email,
            "ip_address": ip_address,
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        }
        
        # Track login/logout events
        if "/auth/login" in request.url.path and request.method == "POST":
            # Will be logged after successful login in auth endpoint
            pass
        elif "/auth/logout" in request.url.path and request.method == "POST":
            _audit_log.add(
                action=AuditAction.LOGOUT,
                resource_type="Auth",
                user_id=user_id,
                user_email=user_email,
                ip_address=ip_address,
                request_id=request_id,
            )
        
        # Process request
        response = await call_next(request)
        
        # Track access denied events
        if response.status_code == 403:
            _audit_log.add(
                action=AuditAction.ACCESS_DENIED,
                resource_type=request.url.path,
                user_id=user_id,
                user_email=user_email,
                ip_address=ip_address,
                request_id=request_id,
                status="FAILED",
                error_message="Access denied",
            )
        
        return response


def audit_database_operation(
    action: AuditAction,
    resource_type: str,
    resource_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    ip_address: Optional[str] = None,
    request_id: Optional[str] = None,
):
    """Log a database operation to the audit trail.
    
    Call this from route handlers to track CRUD operations.
    
    Args:
        action: Type of action (CREATE, READ, UPDATE, DELETE)
        resource_type: Type of resource (e.g., "User", "Prescription")
        resource_id: ID of resource
        changes: Dict of changes made
        metadata: Additional context
        user_id: ID of user (from request.state)
        user_email: Email of user (from request.state)
        ip_address: IP address (from request.state)
        request_id: Request correlation ID
        
    Example:
        # In a route handler
        audit_database_operation(
            action=AuditAction.UPDATE,
            resource_type="Prescription",
            resource_id=str(prescription.id),
            changes={
                "status": {"old": "pending", "new": "active"}
            },
            user_id=request.state.user_id,
            user_email=request.state.user_email,
            ip_address=request.state.audit_context["ip_address"],
            request_id=request.state.audit_context["request_id"],
        )
    """
    _audit_log.add(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        user_email=user_email,
        ip_address=ip_address,
        request_id=request_id,
        changes=changes,
        metadata=metadata,
    )


def track_model_changes(instance: Any) -> Dict[str, Any]:
    """Track changes to a SQLAlchemy model instance.
    
    Args:
        instance: SQLAlchemy model instance
        
    Returns:
        Dict mapping field names to {"old": ..., "new": ...}
    """
    changes = {}
    
    # Get SQLAlchemy inspection state
    state = inspect(instance)
    
    # Iterate through modified attributes
    for attr in state.attrs:
        hist = attr.load_history()
        
        # Check if attribute was modified
        if hist.has_changes():
            old_value = hist.deleted[0] if hist.deleted else None
            new_value = hist.added[0] if hist.added else None
            
            # Skip if both are None
            if old_value is None and new_value is None:
                continue
            
            # Convert to JSON-serializable format
            try:
                old_str = str(old_value) if old_value is not None else None
                new_str = str(new_value) if new_value is not None else None
                
                changes[attr.key] = {
                    "old": old_str,
                    "new": new_str,
                }
            except:
                # Skip non-serializable attributes
                pass
    
    return changes


# SQLAlchemy event listeners for automatic audit logging
# Uncomment to enable automatic tracking (requires session-level user context)

# @event.listens_for(Session, "after_insert")
# def receive_after_insert(mapper, connection, target):
#     """Automatically log INSERT operations."""
#     audit_log.add(
#         action=AuditAction.CREATE,
#         resource_type=target.__class__.__name__,
#         resource_id=str(getattr(target, "id", None)),
#     )

# @event.listens_for(Session, "after_update")
# def receive_after_update(mapper, connection, target):
#     """Automatically log UPDATE operations."""
#     changes = track_model_changes(target)
#     audit_log.add(
#         action=AuditAction.UPDATE,
#         resource_type=target.__class__.__name__,
#         resource_id=str(getattr(target, "id", None)),
#         changes=changes,
#     )

# @event.listens_for(Session, "after_delete")
# def receive_after_delete(mapper, connection, target):
#     """Automatically log DELETE operations."""
#     audit_log.add(
#         action=AuditAction.DELETE,
#         resource_type=target.__class__.__name__,
#         resource_id=str(getattr(target, "id", None)),
#     )


__all__ = [
    "AuditAction",
    "AuditLog",
    "AuditTrailMiddleware",
    "get_audit_log",
    "audit_database_operation",
    "track_model_changes",
]
