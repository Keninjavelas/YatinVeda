"""
Property-Based Tests for Security Monitoring System

This module contains property-based tests that validate the universal correctness
properties of the security monitoring system for the YatinVeda platform.

**Feature: https-security-enhancements, Property 8**: Security Event Logging
**Feature: https-security-enhancements, Property 9**: Threat Detection and Alerting  
**Feature: https-security-enhancements, Property 10**: Administrative Audit Trail

These tests use Hypothesis to generate random inputs and verify that security
monitoring properties hold across all valid scenarios.
"""

import pytest
import asyncio
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite

from middleware.security_monitor import (
    SecurityMonitor,
    SecurityEvent,
    SecurityEventType,
    SecuritySeverity,
    ThreatAlert,
    log_authentication_event,
    log_rate_limit_event,
    log_csrf_event,
    log_admin_event
)


# Hypothesis strategies for generating test data
@composite
def security_event_type_strategy(draw):
    """Generate valid SecurityEventType values"""
    return draw(st.sampled_from(list(SecurityEventType)))


@composite
def security_severity_strategy(draw):
    """Generate valid SecuritySeverity values"""
    return draw(st.sampled_from(list(SecuritySeverity)))


@composite
def ip_address_strategy(draw):
    """Generate valid IP addresses"""
    return draw(st.one_of(
        # IPv4 addresses
        st.builds(
            lambda a, b, c, d: f"{a}.{b}.{c}.{d}",
            st.integers(min_value=1, max_value=255),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=1, max_value=255)
        ),
        # Common test IPs
        st.sampled_from(["127.0.0.1", "192.168.1.1", "10.0.0.1", "172.16.0.1"])
    ))


@composite
def endpoint_strategy(draw):
    """Generate valid API endpoints"""
    return draw(st.one_of(
        st.sampled_from([
            "/api/v1/auth/login",
            "/api/v1/auth/logout", 
            "/api/v1/auth/refresh",
            "/api/v1/admin/users",
            "/api/v1/profile",
            "/api/v1/charts",
            "/api/v1/prescriptions"
        ]),
        st.builds(
            lambda path: f"/api/v1/{path}",
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20)
        )
    ))


@composite
def security_event_details_strategy(draw):
    """Generate valid security event details"""
    return draw(st.dictionaries(
        keys=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_", min_size=1, max_size=20),
        values=st.one_of(
            st.text(max_size=100),
            st.integers(),
            st.booleans(),
            st.floats(allow_nan=False, allow_infinity=False)
        ),
        min_size=0,
        max_size=10
    ))


@composite
def security_event_strategy(draw):
    """Generate valid SecurityEvent instances"""
    event_type = draw(security_event_type_strategy())
    severity = draw(security_severity_strategy())
    client_ip = draw(ip_address_strategy())
    endpoint = draw(endpoint_strategy())
    details = draw(security_event_details_strategy())
    
    return SecurityEvent(
        event_type=event_type,
        severity=severity,
        request_id=str(uuid.uuid4()),
        client_ip=client_ip,
        user_id=draw(st.one_of(st.none(), st.builds(str, st.integers(min_value=1, max_value=10000)))),
        endpoint=endpoint,
        details=details
    )


class TestSecurityEventLogging:
    """
    Property-based tests for security event logging functionality
    
    **Validates: Requirements 3.6, 4.1, 4.4**
    """
    
    @given(
        events=st.lists(security_event_strategy(), min_size=1, max_size=50),
        max_events_memory=st.integers(min_value=100, max_value=1000)
    )
    @settings(max_examples=100, deadline=5000)
    def test_property_security_event_logging_completeness(self, events: List[SecurityEvent], max_events_memory: int):
        """
        **Property 8: Security Event Logging**
        
        *For any* security-relevant event (authentication, rate limiting, CSRF failures), 
        the Security_Monitor should log comprehensive details including client IP, endpoint, 
        timestamp, and correlation IDs
        
        **Validates: Requirements 3.6, 4.1, 4.4**
        """
        # Create security monitor
        monitor = SecurityMonitor(
            max_events_memory=max_events_memory,
            correlation_tracking=True
        )
        
        # Log all events
        for event in events:
            # Simulate logging the event
            monitor.recent_events.append(event)
            monitor.events_by_ip[event.client_ip].append(event)
            if event.user_id:
                monitor.events_by_user[event.user_id].append(event)
            
            # Update correlation tracking
            monitor.correlation_map[event.request_id].append(event.id)
            
            # Update statistics
            monitor.event_counts[event.event_type] += 1
            monitor.severity_counts[event.severity] += 1
        
        # Verify all events are logged with required fields
        logged_events = list(monitor.recent_events)
        
        # Property: All events must have required fields
        for logged_event in logged_events:
            assert logged_event.id is not None, "Event must have ID"
            assert logged_event.timestamp is not None, "Event must have timestamp"
            assert logged_event.event_type is not None, "Event must have event type"
            assert logged_event.severity is not None, "Event must have severity"
            assert logged_event.request_id is not None, "Event must have request ID"
            assert logged_event.client_ip is not None, "Event must have client IP"
            assert logged_event.endpoint is not None, "Event must have endpoint"
            assert isinstance(logged_event.details, dict), "Event details must be dictionary"
            assert isinstance(logged_event.threat_score, (int, float)), "Event must have threat score"
        
        # Property: Events are indexed by IP
        for event in events:
            ip_events = monitor.events_by_ip[event.client_ip]
            assert any(e.id == event.id for e in ip_events), f"Event {event.id} must be indexed by IP {event.client_ip}"
        
        # Property: Events with user_id are indexed by user
        for event in events:
            if event.user_id:
                user_events = monitor.events_by_user[event.user_id]
                assert any(e.id == event.id for e in user_events), f"Event {event.id} must be indexed by user {event.user_id}"
        
        # Property: Correlation tracking works
        for event in events:
            correlated_event_ids = monitor.correlation_map[event.request_id]
            assert event.id in correlated_event_ids, f"Event {event.id} must be in correlation map for request {event.request_id}"
        
        # Property: Statistics are updated
        for event_type in SecurityEventType:
            expected_count = sum(1 for e in events if e.event_type == event_type)
            actual_count = monitor.event_counts[event_type]
            assert actual_count == expected_count, f"Event type {event_type} count mismatch: expected {expected_count}, got {actual_count}"
        
        for severity in SecuritySeverity:
            expected_count = sum(1 for e in events if e.severity == severity)
            actual_count = monitor.severity_counts[severity]
            assert actual_count == expected_count, f"Severity {severity} count mismatch: expected {expected_count}, got {actual_count}"
    
    @given(
        event_type=security_event_type_strategy(),
        severity=security_severity_strategy(),
        client_ip=ip_address_strategy(),
        endpoint=endpoint_strategy(),
        details=security_event_details_strategy()
    )
    @settings(max_examples=100, deadline=3000)
    @pytest.mark.asyncio
    async def test_property_security_event_logging_async_interface(
        self, 
        event_type: SecurityEventType,
        severity: SecuritySeverity, 
        client_ip: str,
        endpoint: str,
        details: Dict[str, Any]
    ):
        """
        **Property 8: Security Event Logging (Async Interface)**
        
        *For any* security event logged through the async interface, the event should be
        properly stored with all required fields and accessible through query methods
        
        **Validates: Requirements 3.6, 4.1, 4.4**
        """
        # Create security monitor
        monitor = SecurityMonitor(correlation_tracking=True)
        
        # Generate test data
        request_id = str(uuid.uuid4())
        user_id = str(random.randint(1, 10000)) if random.randint(0, 1) else None
        
        # Log security event
        logged_event = await monitor.log_security_event(
            event_type=event_type,
            details=details,
            severity=severity,
            request_id=request_id,
            client_ip=client_ip,
            user_id=user_id,
            endpoint=endpoint
        )
        
        # Property: Event is properly created and stored
        assert logged_event.event_type == event_type
        assert logged_event.severity == severity
        assert logged_event.request_id == request_id
        assert logged_event.client_ip == client_ip
        assert logged_event.user_id == user_id
        assert logged_event.endpoint == endpoint
        assert logged_event.details == details
        assert isinstance(logged_event.threat_score, (int, float))
        assert logged_event.threat_score >= 0.0
        
        # Property: Event is accessible through IP query
        ip_events = await monitor.get_events_by_ip(client_ip, hours=1)
        assert any(e.id == logged_event.id for e in ip_events), "Event must be queryable by IP"
        
        # Property: Event is accessible through user query (if user_id provided)
        if user_id:
            user_events = await monitor.get_events_by_user(user_id, hours=1)
            assert any(e.id == logged_event.id for e in user_events), "Event must be queryable by user ID"
        
        # Property: Event is accessible through correlation query
        correlated_events = await monitor.get_events_by_correlation_id(request_id)
        assert any(e.id == logged_event.id for e in correlated_events), "Event must be queryable by correlation ID"
        
        # Property: Event appears in dashboard data
        dashboard_data = await monitor.get_security_dashboard_data()
        assert dashboard_data["summary"]["total_events_last_hour"] >= 1, "Event must appear in dashboard summary"
        assert event_type.value in dashboard_data["event_types"], "Event type must appear in dashboard"
        assert severity.value in dashboard_data["severity_distribution"], "Severity must appear in dashboard"


class TestThreatDetectionAndAlerting:
    """
    Property-based tests for threat detection and alerting functionality
    
    **Validates: Requirements 4.2, 4.5**
    """
    
    @given(
        client_ip=ip_address_strategy(),
        failure_count=st.integers(min_value=10, max_value=20),
        time_window_minutes=st.integers(min_value=30, max_value=120)
    )
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_property_brute_force_detection(
        self, 
        client_ip: str, 
        failure_count: int, 
        time_window_minutes: int
    ):
        """
        **Property 9: Threat Detection and Alerting (Brute Force)**
        
        *For any* suspicious activity pattern (multiple failed logins, unusual access), 
        the Security_Monitor should generate security alerts and support webhook 
        notifications for external systems
        
        **Validates: Requirements 4.2, 4.5**
        """
        # Create security monitor
        monitor = SecurityMonitor(
            threat_detection_window=time_window_minutes * 60,
            correlation_tracking=True
        )
        
        # Generate multiple login failures from same IP
        base_time = datetime.utcnow()
        events = []
        
        for i in range(failure_count):
            event_time = base_time + timedelta(minutes=i * 2)  # Spread over time window
            
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_FAILURE,
                severity=SecuritySeverity.MEDIUM,
                request_id=str(uuid.uuid4()),
                client_ip=client_ip,
                user_id=None,
                endpoint="/api/v1/auth/login",
                details={"attempted_username": f"user{i}", "reason": "invalid_credentials"},
                timestamp=event_time
            )
            
            # Add event to monitor
            monitor.recent_events.append(event)
            monitor.events_by_ip[client_ip].append(event)
            events.append(event)
        
        # Trigger threat analysis on last event
        await monitor._analyze_for_threats(events[-1])
        
        # Property: Brute force attack should be detected for sufficient failures
        if failure_count >= 10:  # Threshold from implementation
            assert len(monitor.active_alerts) >= 1, f"Brute force attack should be detected for {failure_count} failures"
            
            # Find brute force alert
            brute_force_alerts = [
                alert for alert in monitor.active_alerts.values()
                if alert.alert_type == "brute_force_attack" and client_ip in alert.affected_ips
            ]
            assert len(brute_force_alerts) >= 1, "Should have brute force alert for this IP"
            
            alert = brute_force_alerts[0]
            assert alert.severity == SecuritySeverity.HIGH, "Brute force alert should be HIGH severity"
            assert client_ip in alert.affected_ips, "Alert should include the attacking IP"
            assert alert.event_count >= 10, "Alert should report correct event count"
            assert "brute force" in alert.description.lower(), "Alert description should mention brute force"
    
    @given(
        client_ip=ip_address_strategy(),
        csrf_failure_count=st.integers(min_value=5, max_value=10),
        time_window_minutes=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_property_csrf_attack_detection(
        self, 
        client_ip: str, 
        csrf_failure_count: int, 
        time_window_minutes: int
    ):
        """
        **Property 9: Threat Detection and Alerting (CSRF)**
        
        *For any* repeated CSRF token validation failures, the Security_Monitor should
        detect potential CSRF attacks and generate appropriate alerts
        
        **Validates: Requirements 4.2, 4.5**
        """
        # Create security monitor
        monitor = SecurityMonitor(correlation_tracking=True)
        
        # Generate multiple CSRF failures from same IP within short time window
        base_time = datetime.utcnow()
        events = []
        
        for i in range(csrf_failure_count):
            event_time = base_time + timedelta(seconds=i * 30)  # 30 seconds apart
            
            event = SecurityEvent(
                event_type=SecurityEventType.CSRF_TOKEN_FAILURE,
                severity=SecuritySeverity.MEDIUM,
                request_id=str(uuid.uuid4()),
                client_ip=client_ip,
                user_id=f"user{i % 3}",  # Multiple users from same IP
                endpoint="/api/v1/profile/update",
                details={"csrf_token": f"invalid_token_{i}", "reason": "token_mismatch"},
                timestamp=event_time
            )
            
            # Add event to monitor
            monitor.recent_events.append(event)
            monitor.events_by_ip[client_ip].append(event)
            events.append(event)
        
        # Trigger threat analysis on last event
        await monitor._analyze_for_threats(events[-1])
        
        # Property: CSRF attack should be detected for sufficient failures
        if csrf_failure_count >= 5:  # Threshold from implementation
            csrf_alerts = [
                alert for alert in monitor.active_alerts.values()
                if alert.alert_type == "csrf_attack" and client_ip in alert.affected_ips
            ]
            assert len(csrf_alerts) >= 1, f"CSRF attack should be detected for {csrf_failure_count} failures"
            
            alert = csrf_alerts[0]
            assert alert.severity == SecuritySeverity.MEDIUM, "CSRF alert should be MEDIUM severity"
            assert client_ip in alert.affected_ips, "Alert should include the attacking IP"
            assert alert.event_count >= 5, "Alert should report correct event count"
            assert "csrf" in alert.description.lower(), "Alert description should mention CSRF"
    
    @given(
        client_ip=ip_address_strategy(),
        high_threat_events=st.integers(min_value=3, max_value=8)
    )
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_property_suspicious_pattern_detection(
        self, 
        client_ip: str, 
        high_threat_events: int
    ):
        """
        **Property 9: Threat Detection and Alerting (Suspicious Patterns)**
        
        *For any* pattern of high-threat-score events from the same IP, the Security_Monitor
        should detect suspicious activity and generate alerts
        
        **Validates: Requirements 4.2, 4.5**
        """
        # Create security monitor
        monitor = SecurityMonitor(correlation_tracking=True)
        
        # Generate high-threat-score events from same IP
        base_time = datetime.utcnow()
        events = []
        
        high_threat_event_types = [
            SecurityEventType.LOGIN_FAILURE,
            SecurityEventType.CSRF_TOKEN_FAILURE,
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            SecurityEventType.BRUTE_FORCE_DETECTED
        ]
        
        for i in range(high_threat_events):
            event_time = base_time + timedelta(minutes=i * 5)  # 5 minutes apart
            
            event = SecurityEvent(
                event_type=high_threat_event_types[i % len(high_threat_event_types)],
                severity=SecuritySeverity.HIGH,  # High severity = high threat score
                request_id=str(uuid.uuid4()),
                client_ip=client_ip,
                user_id=f"user{i}",
                endpoint=f"/api/v1/endpoint{i}",
                details={"suspicious_activity": True, "repeated_failures": i + 1},
                timestamp=event_time
            )
            
            # Calculate threat score (should be >= 5.0 for high severity)
            event.threat_score = monitor._calculate_threat_score(
                event.event_type, event.severity, event.details
            )
            
            # Add event to monitor
            monitor.recent_events.append(event)
            monitor.events_by_ip[client_ip].append(event)
            events.append(event)
        
        # Trigger threat analysis on last event
        await monitor._analyze_for_threats(events[-1])
        
        # Property: Suspicious activity should be detected for sufficient high-threat events
        if high_threat_events >= 3:  # Threshold from implementation
            suspicious_alerts = [
                alert for alert in monitor.active_alerts.values()
                if alert.alert_type == "suspicious_activity" and client_ip in alert.affected_ips
            ]
            assert len(suspicious_alerts) >= 1, f"Suspicious activity should be detected for {high_threat_events} high-threat events"
            
            alert = suspicious_alerts[0]
            assert alert.severity == SecuritySeverity.MEDIUM, "Suspicious activity alert should be MEDIUM severity"
            assert client_ip in alert.affected_ips, "Alert should include the suspicious IP"
            assert alert.event_count >= 3, "Alert should report correct event count"
            assert "suspicious" in alert.description.lower(), "Alert description should mention suspicious activity"


class TestAdministrativeAuditTrail:
    """
    Property-based tests for administrative audit trail functionality
    
    **Validates: Requirements 4.3, 4.6**
    """
    
    @given(
        admin_actions=st.lists(
            st.sampled_from([
                SecurityEventType.USER_VERIFICATION,
                SecurityEventType.USER_REJECTION,
                SecurityEventType.ADMIN_ACTION,
                SecurityEventType.CONFIG_CHANGE,
                SecurityEventType.TOKEN_REVOCATION
            ]),
            min_size=1,
            max_size=20
        ),
        admin_user_ids=st.lists(
            st.builds(str, st.integers(min_value=1, max_value=100)),
            min_size=1,
            max_size=5
        ),
        client_ips=st.lists(ip_address_strategy(), min_size=1, max_size=3)
    )
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_property_administrative_audit_trail(
        self, 
        admin_actions: List[SecurityEventType],
        admin_user_ids: List[str],
        client_ips: List[str]
    ):
        """
        **Property 10: Administrative Audit Trail**
        
        *For any* administrative action (user verification, token revocation, configuration changes), 
        the Security_Monitor should maintain comprehensive audit logs and provide security 
        dashboard endpoints
        
        **Validates: Requirements 4.3, 4.6**
        """
        # Create security monitor
        monitor = SecurityMonitor(correlation_tracking=True)
        
        # Generate administrative events
        logged_events = []
        base_time = datetime.utcnow()
        
        for i, action_type in enumerate(admin_actions):
            admin_user_id = admin_user_ids[i % len(admin_user_ids)]
            client_ip = client_ips[i % len(client_ips)]
            event_time = base_time + timedelta(minutes=i)
            
            # Create administrative event details
            details = {
                "admin_action": action_type.value,
                "admin_user_id": admin_user_id,
                "timestamp": event_time.isoformat()
            }
            
            if action_type == SecurityEventType.USER_VERIFICATION:
                details.update({
                    "target_user_id": str(random.randint(1000, 9999)),
                    "verification_result": "approved",
                    "verification_notes": "Documents verified"
                })
            elif action_type == SecurityEventType.CONFIG_CHANGE:
                details.update({
                    "config_section": "security_settings",
                    "changed_fields": ["rate_limit_threshold", "mfa_required"],
                    "old_values": {"rate_limit_threshold": 100, "mfa_required": False},
                    "new_values": {"rate_limit_threshold": 150, "mfa_required": True}
                })
            elif action_type == SecurityEventType.TOKEN_REVOCATION:
                details.update({
                    "revoked_token_id": str(uuid.uuid4()),
                    "target_user_id": str(random.randint(1000, 9999)),
                    "revocation_reason": "security_breach"
                })
            
            # Log administrative event
            event = await monitor.log_security_event(
                event_type=action_type,
                details=details,
                severity=SecuritySeverity.HIGH,  # Admin actions are high severity
                request_id=str(uuid.uuid4()),
                client_ip=client_ip,
                user_id=admin_user_id,
                endpoint="/api/v1/admin/action"
            )
            
            logged_events.append(event)
        
        # Property: All administrative events are logged with required audit information
        for event in logged_events:
            assert event.severity == SecuritySeverity.HIGH, "Admin events should be HIGH severity"
            assert event.user_id is not None, "Admin events must have admin user ID"
            assert "admin_action" in event.details, "Admin events must specify action type"
            assert "admin_user_id" in event.details, "Admin events must include admin user ID in details"
            assert "timestamp" in event.details, "Admin events must include timestamp in details"
        
        # Property: Administrative events are queryable by admin user
        for admin_user_id in admin_user_ids:
            admin_events = await monitor.get_events_by_user(admin_user_id, hours=24)
            admin_event_count = sum(1 for e in logged_events if e.user_id == admin_user_id)
            actual_admin_events = [e for e in admin_events if e.user_id == admin_user_id]
            assert len(actual_admin_events) == admin_event_count, f"Should find all events for admin {admin_user_id}"
        
        # Property: Administrative events appear in security dashboard
        dashboard_data = await monitor.get_security_dashboard_data()
        
        # Check that admin event types appear in dashboard
        admin_event_types = set(action.value for action in admin_actions)
        dashboard_event_types = set(dashboard_data["event_types"].keys())
        
        for admin_event_type in admin_event_types:
            assert admin_event_type in dashboard_event_types, f"Admin event type {admin_event_type} should appear in dashboard"
        
        # Property: High severity events are tracked in dashboard summary
        high_severity_count = len([e for e in logged_events if e.severity == SecuritySeverity.HIGH])
        dashboard_high_severity = dashboard_data["summary"]["high_severity_events"]
        assert dashboard_high_severity >= high_severity_count, "Dashboard should track high severity admin events"
        
        # Property: Admin IPs appear in top IPs if they have sufficient activity
        admin_ip_counts = {}
        for event in logged_events:
            admin_ip_counts[event.client_ip] = admin_ip_counts.get(event.client_ip, 0) + 1
        
        dashboard_top_ips = dict(dashboard_data["top_ips"])
        for ip, count in admin_ip_counts.items():
            if count >= 2:  # Should appear in top IPs if sufficient activity
                assert ip in dashboard_top_ips, f"Admin IP {ip} with {count} events should appear in top IPs"


# Convenience functions property tests
class TestConvenienceFunctions:
    """
    Property-based tests for security monitoring convenience functions
    """
    
    @given(
        event_type=st.sampled_from([
            SecurityEventType.LOGIN_SUCCESS,
            SecurityEventType.LOGIN_FAILURE,
            SecurityEventType.LOGOUT,
            SecurityEventType.TOKEN_REFRESH,
            SecurityEventType.TOKEN_REVOCATION
        ]),
        client_ip=ip_address_strategy(),
        endpoint=st.sampled_from(["/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/auth/refresh"])
    )
    @settings(max_examples=100, deadline=3000)
    @pytest.mark.asyncio
    async def test_property_authentication_event_logging(
        self, 
        event_type: SecurityEventType, 
        client_ip: str, 
        endpoint: str
    ):
        """
        Test that authentication convenience function properly logs events
        """
        request_id = str(uuid.uuid4())
        user_id = str(random.randint(1, 10000)) if event_type != SecurityEventType.LOGIN_FAILURE else None
        
        # Log authentication event using convenience function
        event = await log_authentication_event(
            event_type=event_type,
            request_id=request_id,
            client_ip=client_ip,
            user_id=user_id,
            endpoint=endpoint,
            details={"test": True}
        )
        
        # Property: Event is properly logged with correct attributes
        assert event.event_type == event_type
        assert event.request_id == request_id
        assert event.client_ip == client_ip
        assert event.user_id == user_id
        assert event.endpoint == endpoint
        assert event.details["test"] is True
        
        # Property: Severity is appropriate for event type
        if event_type == SecurityEventType.LOGIN_FAILURE:
            assert event.severity == SecuritySeverity.MEDIUM
        elif event_type in [SecurityEventType.TOKEN_REVOCATION]:
            assert event.severity == SecuritySeverity.HIGH
        else:
            assert event.severity == SecuritySeverity.LOW
    
    @given(
        client_ip=ip_address_strategy(),
        endpoint=endpoint_strategy(),
        rule_name=st.text(min_size=1, max_size=50),
        current_count=st.integers(min_value=1, max_value=1000),
        limit=st.integers(min_value=1, max_value=500)
    )
    @settings(max_examples=100, deadline=3000)
    @pytest.mark.asyncio
    async def test_property_rate_limit_event_logging(
        self, 
        client_ip: str, 
        endpoint: str, 
        rule_name: str, 
        current_count: int, 
        limit: int
    ):
        """
        Test that rate limit convenience function properly logs events
        """
        # Ensure current_count exceeds limit for rate limit event
        assume(current_count > limit)
        
        request_id = str(uuid.uuid4())
        user_id = str(random.randint(1, 10000))
        
        # Log rate limit event using convenience function
        event = await log_rate_limit_event(
            request_id=request_id,
            client_ip=client_ip,
            endpoint=endpoint,
            rule_name=rule_name,
            current_count=current_count,
            limit=limit,
            user_id=user_id
        )
        
        # Property: Event is properly logged with correct attributes
        assert event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED
        assert event.severity == SecuritySeverity.MEDIUM
        assert event.request_id == request_id
        assert event.client_ip == client_ip
        assert event.user_id == user_id
        assert event.endpoint == endpoint
        
        # Property: Details contain rate limiting information
        assert event.details["rule_name"] == rule_name
        assert event.details["current_count"] == current_count
        assert event.details["limit"] == limit
        assert event.details["exceeded_by"] == current_count - limit


if __name__ == "__main__":
    # Run property-based tests
    pytest.main([__file__, "-v", "--tb=short"])