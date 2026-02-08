"""Audit trail middleware for tracking and logging all database operations.

Provides comprehensive audit logging for compliance, security, and debugging.
Tracks CRUD operations with user context, request details, and change history.
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
    """In-memory audit log storage.
    
    For production, store in database table or external logging service.
    """
    
    def __init__(self):
        """Initialize audit log storage."""
        self._logs: List[Dict[str, Any]] = []
        self._max_logs = 10000  # Keep last 10k logs in memory
    
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
        """Add audit log entry.
        
        Args:
            action: Type of action performed
            resource_type: Type of resource (e.g., "User", "Prescription")
            resource_id: ID of resource affected
            user_id: ID of user performing action
            user_email: Email of user performing action
            ip_address: IP address of request
            request_id: Correlation ID for request
            changes: Dict of field changes (old_value -> new_value)
            metadata: Additional contextual information
            status: Status of operation (SUCCESS, FAILED)
            error_message: Error message if operation failed
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action.value,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "user_email": user_email,
            "ip_address": ip_address,
            "request_id": request_id,
            "changes": changes,
            "metadata": metadata,
            "status": status,
            "error_message": error_message,
        }
        
        self._logs.append(log_entry)
        
        # Keep only last N logs
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs:]
        
        # Log to application logger
        log_message = f"AUDIT: {action.value} {resource_type}"
        if resource_id:
            log_message += f" #{resource_id}"
        if user_email:
            log_message += f" by {user_email}"
        
        logger.info(log_message, extra=log_entry)
    
    def get_logs(
        self,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query audit logs with filters.
        
        Args:
            user_id: Filter by user ID
            resource_type: Filter by resource type
            action: Filter by action type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of logs to return
            
        Returns:
            List of matching audit log entries
        """
        filtered_logs = self._logs
        
        # Apply filters
        if user_id is not None:
            filtered_logs = [log for log in filtered_logs if log["user_id"] == user_id]
        
        if resource_type is not None:
            filtered_logs = [log for log in filtered_logs if log["resource_type"] == resource_type]
        
        if action is not None:
            filtered_logs = [log for log in filtered_logs if log["action"] == action.value]
        
        if start_date is not None:
            start_iso = start_date.isoformat()
            filtered_logs = [log for log in filtered_logs if log["timestamp"] >= start_iso]
        
        if end_date is not None:
            end_iso = end_date.isoformat()
            filtered_logs = [log for log in filtered_logs if log["timestamp"] <= end_iso]
        
        # Return most recent first, limited
        return list(reversed(filtered_logs[-limit:]))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics.
        
        Returns:
            Dict with counts by action type, resource type, etc.
        """
        actions = {}
        resources = {}
        users = {}
        
        for log in self._logs:
            # Count by action
            action = log["action"]
            actions[action] = actions.get(action, 0) + 1
            
            # Count by resource type
            resource = log["resource_type"]
            resources[resource] = resources.get(resource, 0) + 1
            
            # Count by user
            user_id = log["user_id"]
            if user_id:
                users[user_id] = users.get(user_id, 0) + 1
        
        return {
            "total_logs": len(self._logs),
            "by_action": actions,
            "by_resource": resources,
            "unique_users": len(users),
            "most_active_users": sorted(users.items(), key=lambda x: x[1], reverse=True)[:10],
        }


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
