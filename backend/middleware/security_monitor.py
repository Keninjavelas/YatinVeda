"""
Comprehensive Security Monitoring System for YatinVeda

This module implements security event tracking, threat detection, and real-time alerting
for the YatinVeda platform. It provides comprehensive monitoring capabilities including:
- Authentication event tracking
- Suspicious activity detection
- Administrative audit trails
- Correlation ID tracking
- Webhook notifications for external alerting systems
- Security dashboard endpoints
"""

import os
import json
import uuid
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """Types of security events"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOCATION = "token_revocation"
    
    # Rate limiting events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    IP_BLOCKED = "ip_blocked"
    PROGRESSIVE_DELAY_APPLIED = "progressive_delay_applied"
    
    # CSRF protection events
    CSRF_TOKEN_FAILURE = "csrf_token_failure"
    CSRF_ATTACK_DETECTED = "csrf_attack_detected"
    
    # Administrative events
    USER_VERIFICATION = "user_verification"
    USER_REJECTION = "user_rejection"
    ADMIN_ACTION = "admin_action"
    CONFIG_CHANGE = "config_change"
    
    # Certificate events
    CERT_RENEWAL_SUCCESS = "cert_renewal_success"
    CERT_RENEWAL_FAILURE = "cert_renewal_failure"
    CERT_EXPIRING = "cert_expiring"
    
    # Suspicious activity
    SUSPICIOUS_ACCESS_PATTERN = "suspicious_access_pattern"
    MULTIPLE_FAILED_LOGINS = "multiple_failed_logins"
    UNUSUAL_LOCATION = "unusual_location"
    BRUTE_FORCE_DETECTED = "brute_force_detected"


class SecuritySeverity(Enum):
    """Security event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEvent(BaseModel):
    """Security event data model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: SecurityEventType
    severity: SecuritySeverity
    request_id: str
    client_ip: str
    user_id: Optional[str] = None
    endpoint: str
    details: Dict[str, Any] = Field(default_factory=dict)
    threat_score: float = 0.0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            SecurityEventType: lambda v: v.value,
            SecuritySeverity: lambda v: v.value
        }


@dataclass
class ThreatAlert:
    """Threat detection alert"""
    id: str
    alert_type: str
    severity: SecuritySeverity
    description: str
    affected_ips: List[str]
    event_count: int
    time_window: timedelta
    first_seen: datetime
    last_seen: datetime
    recommended_action: str


class SecurityMonitor:
    """Comprehensive security monitoring and alerting system"""
    
    def __init__(
        self,
        alert_webhook: Optional[str] = None,
        log_level: str = "INFO",
        correlation_tracking: bool = True,
        max_events_memory: int = 10000,
        threat_detection_window: int = 3600  # 1 hour
    ):
        self.alert_webhook = alert_webhook
        self.log_level = log_level
        self.correlation_tracking = correlation_tracking
        self.max_events_memory = max_events_memory
        self.threat_detection_window = threat_detection_window
        
        # In-memory event storage (for real-time analysis)
        self.recent_events: deque = deque(maxlen=max_events_memory)
        self.events_by_ip: Dict[str, List[SecurityEvent]] = defaultdict(list)
        self.events_by_user: Dict[str, List[SecurityEvent]] = defaultdict(list)
        self.correlation_map: Dict[str, List[str]] = defaultdict(list)
        
        # Threat detection state
        self.active_alerts: Dict[str, ThreatAlert] = {}
        self.ip_failure_counts: Dict[str, int] = defaultdict(int)
        self.ip_last_failure: Dict[str, datetime] = {}
        
        # Statistics
        self.event_counts: Dict[SecurityEventType, int] = defaultdict(int)
        self.severity_counts: Dict[SecuritySeverity, int] = defaultdict(int)
        
        logger.info(f"SecurityMonitor initialized with webhook: {bool(alert_webhook)}")
    
    async def log_security_event(
        self,
        event_type: SecurityEventType,
        details: Dict[str, Any],
        severity: SecuritySeverity,
        request_id: str,
        client_ip: str = "unknown",
        user_id: Optional[str] = None,
        endpoint: str = "unknown"
    ) -> SecurityEvent:
        """Log a security event and perform threat analysis"""
        
        # Create security event
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            request_id=request_id,
            client_ip=client_ip,
            user_id=user_id,
            endpoint=endpoint,
            details=details,
            threat_score=self._calculate_threat_score(event_type, severity, details)
        )
        
        # Store event
        self.recent_events.append(event)
        self.events_by_ip[client_ip].append(event)
        if user_id:
            self.events_by_user[user_id].append(event)
        
        # Update correlation tracking
        if self.correlation_tracking:
            self.correlation_map[request_id].append(event.id)
        
        # Update statistics
        self.event_counts[event_type] += 1
        self.severity_counts[severity] += 1
        
        # Log the event
        log_message = f"Security Event: {event_type.value} | Severity: {severity.value} | IP: {client_ip} | User: {user_id} | Endpoint: {endpoint}"
        if severity == SecuritySeverity.CRITICAL:
            logger.critical(log_message)
        elif severity == SecuritySeverity.HIGH:
            logger.error(log_message)
        elif severity == SecuritySeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Perform threat detection
        await self._analyze_for_threats(event)
        
        # Clean up old events
        await self._cleanup_old_events()
        
        return event
    
    def _calculate_threat_score(
        self,
        event_type: SecurityEventType,
        severity: SecuritySeverity,
        details: Dict[str, Any]
    ) -> float:
        """Calculate threat score for an event"""
        base_scores = {
            SecuritySeverity.LOW: 1.0,
            SecuritySeverity.MEDIUM: 3.0,
            SecuritySeverity.HIGH: 7.0,
            SecuritySeverity.CRITICAL: 10.0
        }
        
        event_multipliers = {
            SecurityEventType.LOGIN_FAILURE: 2.0,
            SecurityEventType.CSRF_TOKEN_FAILURE: 3.0,
            SecurityEventType.RATE_LIMIT_EXCEEDED: 2.5,
            SecurityEventType.BRUTE_FORCE_DETECTED: 5.0,
            SecurityEventType.SUSPICIOUS_ACCESS_PATTERN: 4.0,
            SecurityEventType.MULTIPLE_FAILED_LOGINS: 4.5,
        }
        
        base_score = base_scores.get(severity, 1.0)
        multiplier = event_multipliers.get(event_type, 1.0)
        
        # Additional factors from details
        if details.get("repeated_failures", 0) > 5:
            multiplier *= 1.5
        if details.get("unusual_location", False):
            multiplier *= 1.3
        
        return min(base_score * multiplier, 10.0)
    
    async def _analyze_for_threats(self, event: SecurityEvent) -> None:
        """Analyze event for potential threats and generate alerts"""
        
        # Check for brute force attacks
        if event.event_type == SecurityEventType.LOGIN_FAILURE:
            await self._check_brute_force(event)
        
        # Check for CSRF attack patterns
        if event.event_type == SecurityEventType.CSRF_TOKEN_FAILURE:
            await self._check_csrf_attack(event)
        
        # Check for suspicious access patterns
        if event.threat_score >= 5.0:
            await self._check_suspicious_patterns(event)
        
        # Check for rate limit abuse
        if event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED:
            await self._check_rate_limit_abuse(event)
    
    async def _check_brute_force(self, event: SecurityEvent) -> None:
        """Check for brute force attack patterns"""
        client_ip = event.client_ip
        now = datetime.utcnow()
        
        # Count recent failures from this IP
        recent_failures = [
            e for e in self.events_by_ip[client_ip]
            if e.event_type == SecurityEventType.LOGIN_FAILURE
            and (now - e.timestamp).total_seconds() < self.threat_detection_window
        ]
        
        if len(recent_failures) >= 10:  # 10 failures in 1 hour
            alert = ThreatAlert(
                id=str(uuid.uuid4()),
                alert_type="brute_force_attack",
                severity=SecuritySeverity.HIGH,
                description=f"Brute force attack detected from IP {client_ip}",
                affected_ips=[client_ip],
                event_count=len(recent_failures),
                time_window=timedelta(seconds=self.threat_detection_window),
                first_seen=recent_failures[0].timestamp,
                last_seen=recent_failures[-1].timestamp,
                recommended_action="Block IP address and investigate"
            )
            
            await self._send_alert(alert)
    
    async def _check_csrf_attack(self, event: SecurityEvent) -> None:
        """Check for CSRF attack patterns"""
        client_ip = event.client_ip
        now = datetime.utcnow()
        
        # Count recent CSRF failures from this IP
        recent_csrf_failures = [
            e for e in self.events_by_ip[client_ip]
            if e.event_type == SecurityEventType.CSRF_TOKEN_FAILURE
            and (now - e.timestamp).total_seconds() < 300  # 5 minutes
        ]
        
        if len(recent_csrf_failures) >= 5:  # 5 CSRF failures in 5 minutes
            alert = ThreatAlert(
                id=str(uuid.uuid4()),
                alert_type="csrf_attack",
                severity=SecuritySeverity.MEDIUM,
                description=f"Potential CSRF attack from IP {client_ip}",
                affected_ips=[client_ip],
                event_count=len(recent_csrf_failures),
                time_window=timedelta(minutes=5),
                first_seen=recent_csrf_failures[0].timestamp,
                last_seen=recent_csrf_failures[-1].timestamp,
                recommended_action="Investigate and consider IP blocking"
            )
            
            await self._send_alert(alert)
    
    async def _check_suspicious_patterns(self, event: SecurityEvent) -> None:
        """Check for suspicious access patterns"""
        client_ip = event.client_ip
        now = datetime.utcnow()
        
        # Check for high-threat-score events from same IP
        high_threat_events = [
            e for e in self.events_by_ip[client_ip]
            if e.threat_score >= 5.0
            and (now - e.timestamp).total_seconds() < 1800  # 30 minutes
        ]
        
        if len(high_threat_events) >= 3:  # 3 high-threat events in 30 minutes
            alert = ThreatAlert(
                id=str(uuid.uuid4()),
                alert_type="suspicious_activity",
                severity=SecuritySeverity.MEDIUM,
                description=f"Suspicious activity pattern detected from IP {client_ip}",
                affected_ips=[client_ip],
                event_count=len(high_threat_events),
                time_window=timedelta(minutes=30),
                first_seen=high_threat_events[0].timestamp,
                last_seen=high_threat_events[-1].timestamp,
                recommended_action="Monitor closely and investigate if pattern continues"
            )
            
            await self._send_alert(alert)
    
    async def _check_rate_limit_abuse(self, event: SecurityEvent) -> None:
        """Check for rate limit abuse patterns"""
        client_ip = event.client_ip
        now = datetime.utcnow()
        
        # Count recent rate limit violations
        rate_limit_events = [
            e for e in self.events_by_ip[client_ip]
            if e.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED
            and (now - e.timestamp).total_seconds() < 600  # 10 minutes
        ]
        
        if len(rate_limit_events) >= 5:  # 5 rate limit violations in 10 minutes
            alert = ThreatAlert(
                id=str(uuid.uuid4()),
                alert_type="rate_limit_abuse",
                severity=SecuritySeverity.MEDIUM,
                description=f"Rate limit abuse detected from IP {client_ip}",
                affected_ips=[client_ip],
                event_count=len(rate_limit_events),
                time_window=timedelta(minutes=10),
                first_seen=rate_limit_events[0].timestamp,
                last_seen=rate_limit_events[-1].timestamp,
                recommended_action="Consider extending rate limit duration or blocking IP"
            )
            
            await self._send_alert(alert)
    
    async def _send_alert(self, alert: ThreatAlert) -> None:
        """Send alert via webhook and store in active alerts"""
        
        # Store alert
        self.active_alerts[alert.id] = alert
        
        # Log alert
        logger.warning(f"Security Alert: {alert.alert_type} | {alert.description}")
        
        # Send webhook notification if configured
        if self.alert_webhook:
            try:
                alert_data = {
                    "id": alert.id,
                    "type": alert.alert_type,
                    "severity": alert.severity.value,
                    "description": alert.description,
                    "affected_ips": alert.affected_ips,
                    "event_count": alert.event_count,
                    "time_window_seconds": alert.time_window.total_seconds(),
                    "first_seen": alert.first_seen.isoformat(),
                    "last_seen": alert.last_seen.isoformat(),
                    "recommended_action": alert.recommended_action,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.alert_webhook,
                        json=alert_data,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            logger.info(f"Alert webhook sent successfully: {alert.id}")
                        else:
                            logger.error(f"Alert webhook failed with status {response.status}: {alert.id}")
                            
            except Exception as e:
                logger.error(f"Failed to send alert webhook: {str(e)}")
    
    async def _cleanup_old_events(self) -> None:
        """Clean up old events from memory"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.threat_detection_window * 2)
        
        # Clean up IP-based events
        for ip, events in list(self.events_by_ip.items()):
            self.events_by_ip[ip] = [
                e for e in events
                if e.timestamp > cutoff
            ]
            if not self.events_by_ip[ip]:
                del self.events_by_ip[ip]
        
        # Clean up user-based events
        for user_id, events in list(self.events_by_user.items()):
            self.events_by_user[user_id] = [
                e for e in events
                if e.timestamp > cutoff
            ]
            if not self.events_by_user[user_id]:
                del self.events_by_user[user_id]
        
        # Clean up old alerts (keep for 24 hours)
        alert_cutoff = now - timedelta(hours=24)
        self.active_alerts = {
            alert_id: alert
            for alert_id, alert in self.active_alerts.items()
            if alert.last_seen > alert_cutoff
        }
    
    async def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get security dashboard data for monitoring"""
        now = datetime.utcnow()
        
        # Recent events (last hour)
        recent_events = [
            e for e in self.recent_events
            if (now - e.timestamp).total_seconds() < 3600
        ]
        
        # Event type distribution
        event_type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for event in recent_events:
            event_type_counts[event.event_type.value] += 1
            severity_counts[event.severity.value] += 1
        
        # Top IPs by event count
        ip_event_counts = defaultdict(int)
        for event in recent_events:
            ip_event_counts[event.client_ip] += 1
        
        top_ips = sorted(
            ip_event_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Active alerts
        active_alerts_data = [
            {
                "id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity.value,
                "description": alert.description,
                "affected_ips": alert.affected_ips,
                "event_count": alert.event_count,
                "first_seen": alert.first_seen.isoformat(),
                "last_seen": alert.last_seen.isoformat()
            }
            for alert in self.active_alerts.values()
        ]
        
        return {
            "timestamp": now.isoformat(),
            "summary": {
                "total_events_last_hour": len(recent_events),
                "active_alerts": len(self.active_alerts),
                "unique_ips_last_hour": len(set(e.client_ip for e in recent_events)),
                "high_severity_events": len([e for e in recent_events if e.severity in [SecuritySeverity.HIGH, SecuritySeverity.CRITICAL]])
            },
            "event_types": dict(event_type_counts),
            "severity_distribution": dict(severity_counts),
            "top_ips": top_ips,
            "active_alerts": active_alerts_data,
            "system_health": {
                "events_in_memory": len(self.recent_events),
                "tracked_ips": len(self.events_by_ip),
                "tracked_users": len(self.events_by_user),
                "correlation_entries": len(self.correlation_map)
            }
        }
    
    async def get_events_by_correlation_id(self, request_id: str) -> List[SecurityEvent]:
        """Get all security events for a correlation ID"""
        if not self.correlation_tracking:
            return []
        
        event_ids = self.correlation_map.get(request_id, [])
        events = []
        
        for event in self.recent_events:
            if event.id in event_ids:
                events.append(event)
        
        return sorted(events, key=lambda e: e.timestamp)
    
    async def get_events_by_ip(self, client_ip: str, hours: int = 24) -> List[SecurityEvent]:
        """Get security events for a specific IP address"""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=hours)
        
        return [
            e for e in self.events_by_ip.get(client_ip, [])
            if e.timestamp > cutoff
        ]
    
    async def get_events_by_user(self, user_id: str, hours: int = 24) -> List[SecurityEvent]:
        """Get security events for a specific user"""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=hours)
        
        return [
            e for e in self.events_by_user.get(user_id, [])
            if e.timestamp > cutoff
        ]


# Global security monitor instance
_security_monitor: Optional[SecurityMonitor] = None


def get_security_monitor() -> SecurityMonitor:
    """Get the global security monitor instance"""
    global _security_monitor
    if _security_monitor is None:
        webhook_url = os.getenv("SECURITY_ALERT_WEBHOOK")
        log_level = os.getenv("SECURITY_LOG_LEVEL", "INFO")
        
        _security_monitor = SecurityMonitor(
            alert_webhook=webhook_url,
            log_level=log_level,
            correlation_tracking=True
        )
    
    return _security_monitor


def initialize_security_monitor(
    alert_webhook: Optional[str] = None,
    log_level: str = "INFO",
    correlation_tracking: bool = True
) -> SecurityMonitor:
    """Initialize the global security monitor"""
    global _security_monitor
    _security_monitor = SecurityMonitor(
        alert_webhook=alert_webhook,
        log_level=log_level,
        correlation_tracking=correlation_tracking
    )
    return _security_monitor


# Convenience functions for logging common security events
async def log_authentication_event(
    event_type: SecurityEventType,
    request_id: str,
    client_ip: str,
    user_id: Optional[str] = None,
    endpoint: str = "/auth",
    details: Optional[Dict[str, Any]] = None
) -> SecurityEvent:
    """Log an authentication-related security event"""
    monitor = get_security_monitor()
    
    severity = SecuritySeverity.LOW
    if event_type == SecurityEventType.LOGIN_FAILURE:
        severity = SecuritySeverity.MEDIUM
    elif event_type in [SecurityEventType.TOKEN_REVOCATION, SecurityEventType.MULTIPLE_FAILED_LOGINS]:
        severity = SecuritySeverity.HIGH
    
    return await monitor.log_security_event(
        event_type=event_type,
        details=details or {},
        severity=severity,
        request_id=request_id,
        client_ip=client_ip,
        user_id=user_id,
        endpoint=endpoint
    )


async def log_rate_limit_event(
    request_id: str,
    client_ip: str,
    endpoint: str,
    rule_name: str,
    current_count: int,
    limit: int,
    user_id: Optional[str] = None
) -> SecurityEvent:
    """Log a rate limiting security event"""
    monitor = get_security_monitor()
    
    details = {
        "rule_name": rule_name,
        "current_count": current_count,
        "limit": limit,
        "exceeded_by": current_count - limit
    }
    
    return await monitor.log_security_event(
        event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
        details=details,
        severity=SecuritySeverity.MEDIUM,
        request_id=request_id,
        client_ip=client_ip,
        user_id=user_id,
        endpoint=endpoint
    )


async def log_csrf_event(
    request_id: str,
    client_ip: str,
    endpoint: str,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> SecurityEvent:
    """Log a CSRF-related security event"""
    monitor = get_security_monitor()
    
    return await monitor.log_security_event(
        event_type=SecurityEventType.CSRF_TOKEN_FAILURE,
        details=details or {},
        severity=SecuritySeverity.MEDIUM,
        request_id=request_id,
        client_ip=client_ip,
        user_id=user_id,
        endpoint=endpoint
    )


async def log_admin_event(
    event_type: SecurityEventType,
    request_id: str,
    client_ip: str,
    admin_user_id: str,
    endpoint: str,
    details: Dict[str, Any]
) -> SecurityEvent:
    """Log an administrative security event"""
    monitor = get_security_monitor()
    
    return await monitor.log_security_event(
        event_type=event_type,
        details=details,
        severity=SecuritySeverity.HIGH,
        request_id=request_id,
        client_ip=client_ip,
        user_id=admin_user_id,
        endpoint=endpoint
    )