"""
Security Dashboard and Monitoring API Endpoints

This module provides API endpoints for security monitoring, dashboard data,
and security event management for the YatinVeda platform.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

from modules.admin_auth import require_admin
from middleware.security_monitor import (
    get_security_monitor,
    SecurityEvent,
    SecurityEventType,
    SecuritySeverity,
    ThreatAlert
)
from models.database import User
from logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/security/dashboard")
async def get_security_dashboard(
    request: Request,
    current_admin: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get comprehensive security dashboard data
    
    Requires admin authentication. Returns real-time security metrics,
    event summaries, active alerts, and system health information.
    """
    try:
        monitor = get_security_monitor()
        dashboard_data = await monitor.get_security_dashboard_data()
        
        # Log admin access to security dashboard
        await monitor.log_security_event(
            event_type=SecurityEventType.ADMIN_ACTION,
            details={
                "action": "security_dashboard_access",
                "admin_user": current_admin.email
            },
            severity=SecuritySeverity.LOW,
            request_id=request.headers.get("X-Request-ID", str(uuid.uuid4())),
            client_ip=request.client.host if request.client else "unknown",
            user_id=str(current_admin.id),
            endpoint="/api/v1/security/dashboard"
        )
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get security dashboard data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve security dashboard data"
        )


@router.get("/security/events")
async def get_security_events(
    request: Request,
    client_ip: Optional[str] = Query(None, description="Filter by client IP address"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve (1-168)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    current_admin: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get filtered security events
    
    Requires admin authentication. Supports filtering by IP, user, event type,
    severity, and time range. Returns paginated results.
    """
    try:
        monitor = get_security_monitor()
        
        # Get events based on filters
        if client_ip:
            events = await monitor.get_events_by_ip(client_ip, hours)
        elif user_id:
            events = await monitor.get_events_by_user(user_id, hours)
        else:
            # Get recent events from memory
            now = datetime.utcnow()
            cutoff = now - timedelta(hours=hours)
            events = [
                e for e in monitor.recent_events
                if e.timestamp > cutoff
            ]
        
        # Apply additional filters
        if event_type:
            try:
                event_type_enum = SecurityEventType(event_type)
                events = [e for e in events if e.event_type == event_type_enum]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event type: {event_type}"
                )
        
        if severity:
            try:
                severity_enum = SecuritySeverity(severity)
                events = [e for e in events if e.severity == severity_enum]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid severity level: {severity}"
                )
        
        # Sort by timestamp (newest first) and limit
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
        
        # Convert to serializable format
        events_data = []
        for event in events:
            event_dict = event.dict()
            event_dict["timestamp"] = event.timestamp.isoformat()
            event_dict["event_type"] = event.event_type.value
            event_dict["severity"] = event.severity.value
            events_data.append(event_dict)
        
        # Log admin access to security events
        await monitor.log_security_event(
            event_type=SecurityEventType.ADMIN_ACTION,
            details={
                "action": "security_events_query",
                "admin_user": current_admin.email,
                "filters": {
                    "client_ip": client_ip,
                    "user_id": user_id,
                    "event_type": event_type,
                    "severity": severity,
                    "hours": hours
                },
                "results_count": len(events_data)
            },
            severity=SecuritySeverity.LOW,
            request_id=request.headers.get("X-Request-ID", str(uuid.uuid4())),
            client_ip=request.client.host if request.client else "unknown",
            user_id=str(current_admin.id),
            endpoint="/api/v1/security/events"
        )
        
        return {
            "events": events_data,
            "total_count": len(events_data),
            "filters_applied": {
                "client_ip": client_ip,
                "user_id": user_id,
                "event_type": event_type,
                "severity": severity,
                "hours": hours
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get security events: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve security events"
        )


@router.get("/security/alerts")
async def get_active_alerts(
    request: Request,
    current_admin: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get active security alerts
    
    Requires admin authentication. Returns all currently active security alerts
    with details about detected threats and recommended actions.
    """
    try:
        monitor = get_security_monitor()
        
        # Get active alerts
        active_alerts = []
        for alert in monitor.active_alerts.values():
            alert_dict = {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value,
                "description": alert.description,
                "affected_ips": alert.affected_ips,
                "event_count": alert.event_count,
                "time_window_seconds": alert.time_window.total_seconds(),
                "first_seen": alert.first_seen.isoformat(),
                "last_seen": alert.last_seen.isoformat(),
                "recommended_action": alert.recommended_action
            }
            active_alerts.append(alert_dict)
        
        # Sort by severity and last seen
        severity_order = {
            SecuritySeverity.CRITICAL: 4,
            SecuritySeverity.HIGH: 3,
            SecuritySeverity.MEDIUM: 2,
            SecuritySeverity.LOW: 1
        }
        
        active_alerts.sort(
            key=lambda a: (severity_order.get(SecuritySeverity(a["severity"]), 0), a["last_seen"]),
            reverse=True
        )
        
        # Log admin access to security alerts
        await monitor.log_security_event(
            event_type=SecurityEventType.ADMIN_ACTION,
            details={
                "action": "security_alerts_access",
                "admin_user": current_admin.email,
                "active_alerts_count": len(active_alerts)
            },
            severity=SecuritySeverity.LOW,
            request_id=request.headers.get("X-Request-ID", str(uuid.uuid4())),
            client_ip=request.client.host if request.client else "unknown",
            user_id=str(current_admin.id),
            endpoint="/api/v1/security/alerts"
        )
        
        return {
            "alerts": active_alerts,
            "total_count": len(active_alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get security alerts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve security alerts"
        )


@router.get("/security/events/correlation/{request_id}")
async def get_correlated_events(
    request_id: str,
    request: Request,
    current_admin: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get all security events for a specific correlation ID
    
    Requires admin authentication. Returns all security events that share
    the same correlation/request ID for tracking related security incidents.
    """
    try:
        monitor = get_security_monitor()
        
        # Get correlated events
        events = await monitor.get_events_by_correlation_id(request_id)
        
        # Convert to serializable format
        events_data = []
        for event in events:
            event_dict = event.dict()
            event_dict["timestamp"] = event.timestamp.isoformat()
            event_dict["event_type"] = event.event_type.value
            event_dict["severity"] = event.severity.value
            events_data.append(event_dict)
        
        # Log admin access to correlated events
        await monitor.log_security_event(
            event_type=SecurityEventType.ADMIN_ACTION,
            details={
                "action": "correlated_events_access",
                "admin_user": current_admin.email,
                "correlation_id": request_id,
                "events_found": len(events_data)
            },
            severity=SecuritySeverity.LOW,
            request_id=request.headers.get("X-Request-ID", str(uuid.uuid4())),
            client_ip=request.client.host if request.client else "unknown",
            user_id=str(current_admin.id),
            endpoint=f"/api/v1/security/events/correlation/{request_id}"
        )
        
        return {
            "correlation_id": request_id,
            "events": events_data,
            "total_count": len(events_data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get correlated events: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve correlated events"
        )


@router.get("/security/health")
async def security_health_check(
    request: Request,
    current_admin: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Security system health check
    
    Requires admin authentication. Returns health status of all security
    components including monitoring, rate limiting, and certificate management.
    """
    try:
        monitor = get_security_monitor()
        
        # Basic security monitor health
        health_status = {
            "security_monitor": {
                "status": "healthy",
                "events_in_memory": len(monitor.recent_events),
                "tracked_ips": len(monitor.events_by_ip),
                "tracked_users": len(monitor.events_by_user),
                "active_alerts": len(monitor.active_alerts),
                "correlation_tracking": monitor.correlation_tracking
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check webhook configuration
        if monitor.alert_webhook:
            health_status["alert_webhook"] = {
                "configured": True,
                "url": monitor.alert_webhook
            }
        else:
            health_status["alert_webhook"] = {
                "configured": False,
                "status": "No webhook configured"
            }
        
        # Check certificate management (if available)
        try:
            from modules.certificate_manager import get_certificate_status
            cert_status = await get_certificate_status()
            health_status["certificate_management"] = cert_status
        except ImportError:
            health_status["certificate_management"] = {
                "status": "not_available",
                "message": "Certificate management module not available"
            }
        except Exception as e:
            health_status["certificate_management"] = {
                "status": "error",
                "message": str(e)
            }
        
        # Check rate limiting (if available)
        try:
            from middleware.rate_limiter import get_rate_limiter_status
            rate_limit_status = await get_rate_limiter_status()
            health_status["rate_limiting"] = rate_limit_status
        except ImportError:
            health_status["rate_limiting"] = {
                "status": "not_available",
                "message": "Advanced rate limiting not available"
            }
        except Exception as e:
            health_status["rate_limiting"] = {
                "status": "error",
                "message": str(e)
            }
        
        # Overall health assessment
        component_statuses = []
        for component, status in health_status.items():
            if isinstance(status, dict) and "status" in status:
                component_statuses.append(status["status"])
        
        if "error" in component_statuses:
            overall_status = "degraded"
        elif "not_available" in component_statuses:
            overall_status = "partial"
        else:
            overall_status = "healthy"
        
        health_status["overall_status"] = overall_status
        
        # Log health check access
        await monitor.log_security_event(
            event_type=SecurityEventType.ADMIN_ACTION,
            details={
                "action": "security_health_check",
                "admin_user": current_admin.email,
                "overall_status": overall_status
            },
            severity=SecuritySeverity.LOW,
            request_id=request.headers.get("X-Request-ID", str(uuid.uuid4())),
            client_ip=request.client.host if request.client else "unknown",
            user_id=str(current_admin.id),
            endpoint="/api/v1/security/health"
        )
        
        return health_status
        
    except Exception as e:
        logger.error(f"Security health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Security health check failed"
        )


@router.post("/security/test-alert")
async def test_security_alert(
    request: Request,
    current_admin: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Test security alert system
    
    Requires admin authentication. Generates a test security event and alert
    to verify the monitoring and alerting system is working correctly.
    """
    try:
        monitor = get_security_monitor()
        
        # Generate test security event
        test_event = await monitor.log_security_event(
            event_type=SecurityEventType.ADMIN_ACTION,
            details={
                "action": "security_alert_test",
                "admin_user": current_admin.email,
                "test_timestamp": datetime.utcnow().isoformat(),
                "description": "This is a test security alert to verify system functionality"
            },
            severity=SecuritySeverity.MEDIUM,
            request_id=request.headers.get("X-Request-ID", str(uuid.uuid4())),
            client_ip=request.client.host if request.client else "unknown",
            user_id=str(current_admin.id),
            endpoint="/api/v1/security/test-alert"
        )
        
        return {
            "message": "Test security alert generated successfully",
            "test_event": {
                "id": test_event.id,
                "event_type": test_event.event_type.value,
                "severity": test_event.severity.value,
                "timestamp": test_event.timestamp.isoformat()
            },
            "webhook_configured": bool(monitor.alert_webhook),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate test security alert: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate test security alert"
        )


# CSRF Token Management Endpoints
@router.get("/security/csrf-token")
async def get_csrf_token(
    request: Request,
    current_user: User = Depends(require_admin)  # Can be extended to regular users
) -> Dict[str, Any]:
    """
    Get a CSRF token for the current session
    
    Returns a CSRF token that can be used for state-changing operations.
    The token is tied to the current session and has a limited lifetime.
    """
    try:
        from middleware.csrf_protection import get_csrf_token_for_request
        
        # Generate CSRF token for current request
        csrf_token = await get_csrf_token_for_request(request)
        
        if not csrf_token:
            raise HTTPException(
                status_code=400,
                detail="Unable to generate CSRF token - no valid session found"
            )
        
        # Log CSRF token generation
        monitor = get_security_monitor()
        await monitor.log_security_event(
            event_type=SecurityEventType.ADMIN_ACTION,
            details={
                "action": "csrf_token_generation",
                "user": current_user.email,
                "token_length": len(csrf_token)
            },
            severity=SecuritySeverity.LOW,
            request_id=request.headers.get("X-Request-ID", str(uuid.uuid4())),
            client_ip=request.client.host if request.client else "unknown",
            user_id=str(current_user.id),
            endpoint="/api/v1/security/csrf-token"
        )
        
        return {
            "csrf_token": csrf_token,
            "expires_in": 3600,  # 1 hour
            "usage": "Include this token in X-CSRF-Token header or csrf_token form field",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate CSRF token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate CSRF token"
        )


@router.post("/security/csrf-test")
async def test_csrf_protection(
    request: Request,
    current_admin: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Test CSRF protection functionality
    
    This endpoint requires a valid CSRF token and can be used to test
    that CSRF protection is working correctly.
    """
    try:
        # This endpoint will be protected by CSRF middleware
        # If we reach here, CSRF validation passed
        
        monitor = get_security_monitor()
        await monitor.log_security_event(
            event_type=SecurityEventType.ADMIN_ACTION,
            details={
                "action": "csrf_protection_test",
                "admin_user": current_admin.email,
                "test_result": "success"
            },
            severity=SecuritySeverity.LOW,
            request_id=request.headers.get("X-Request-ID", str(uuid.uuid4())),
            client_ip=request.client.host if request.client else "unknown",
            user_id=str(current_admin.id),
            endpoint="/api/v1/security/csrf-test"
        )
        
        return {
            "message": "CSRF protection test successful",
            "csrf_validation": "passed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"CSRF protection test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="CSRF protection test failed"
        )


# Event type and severity enums for API documentation
@router.get("/security/enums")
async def get_security_enums(
    current_admin: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get available security event types and severity levels
    
    Requires admin authentication. Returns enumeration values for filtering
    and understanding security events and alerts.
    """
    return {
        "event_types": [event_type.value for event_type in SecurityEventType],
        "severity_levels": [severity.value for severity in SecuritySeverity],
        "timestamp": datetime.utcnow().isoformat()
    }