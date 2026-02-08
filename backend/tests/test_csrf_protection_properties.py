"""
Property-Based Tests for CSRF Protection System

This module contains property-based tests that validate the universal correctness
properties of the CSRF protection system for the YatinVeda platform.

**Feature: https-security-enhancements, Property 11**: CSRF Token Validation
**Feature: https-security-enhancements, Property 12**: CSRF Attack Detection

These tests use Hypothesis to generate random inputs and verify that CSRF
protection properties hold across all valid scenarios.
"""

import pytest
import asyncio
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
from fastapi import Request
from fastapi.testclient import TestClient
from starlette.datastructures import Headers
from unittest.mock import Mock, AsyncMock

from middleware.csrf_protection import (
    CSRFProtection,
    CSRFMiddleware,
    CSRFTokenType,
    CSRFToken,
    get_csrf_protection,
    initialize_csrf_protection,
    generate_csrf_token_for_session,
    validate_csrf_token_for_session
)
from middleware.security_monitor import (
    get_security_monitor,
    SecurityEventType,
    SecuritySeverity
)


# Hypothesis strategies for generating test data
@composite
def session_id_strategy(draw):
    """Generate valid session IDs"""
    return draw(st.one_of(
        # UUID-like session IDs
        st.builds(str, st.uuids()),
        # Hash-like session IDs
        st.builds(
            lambda: hashlib.sha256(secrets.token_bytes(32)).hexdigest()[:32]
        ),
        # Simple alphanumeric session IDs
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=16, max_size=64)
    ))


@composite
def csrf_secret_key_strategy(draw):
    """Generate valid CSRF secret keys"""
    return draw(st.one_of(
        # Random bytes
        st.builds(lambda: secrets.token_bytes(32)),
        # String keys
        st.text(min_size=32, max_size=128)
    ))


@composite
def http_method_strategy(draw):
    """Generate HTTP methods"""
    return draw(st.sampled_from(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]))


@composite
def endpoint_path_strategy(draw):
    """Generate API endpoint paths"""
    return draw(st.one_of(
        st.sampled_from([
            "/api/v1/profile/update",
            "/api/v1/auth/logout",
            "/api/v1/admin/users",
            "/api/v1/prescriptions",
            "/api/v1/charts/create",
            "/api/v1/payments/process"
        ]),
        st.builds(
            lambda path: f"/api/v1/{path}",
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz/", min_size=1, max_size=30)
        )
    ))


@composite
def request_headers_strategy(draw):
    """Generate HTTP request headers"""
    base_headers = {
        "User-Agent": draw(st.text(min_size=10, max_size=100)),
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Optionally add authorization header
    if draw(st.booleans()):
        base_headers["Authorization"] = f"Bearer {secrets.token_urlsafe(32)}"
    
    # Optionally add referer
    if draw(st.booleans()):
        base_headers["Referer"] = draw(st.text(min_size=10, max_size=50))
    
    # Optionally add custom session header
    if draw(st.booleans()):
        base_headers["X-Session-ID"] = draw(session_id_strategy())
    
    return base_headers


@composite
def mock_request_strategy(draw):
    """Generate mock FastAPI Request objects"""
    method = draw(http_method_strategy())
    path = draw(endpoint_path_strategy())
    headers = draw(request_headers_strategy())
    
    # Create mock request
    request = Mock(spec=Request)
    request.method = method
    request.url.path = path
    request.headers = Headers(headers)
    request.client.host = draw(st.ip_addresses(v=4).map(str))
    request.cookies = {}
    
    # Mock async methods
    request.form = AsyncMock(return_value={})
    request.json = AsyncMock(return_value={})
    
    return request


class TestCSRFTokenValidation:
    """
    Property-based tests for CSRF token validation functionality
    
    **Validates: Requirements 5.3, 5.4, 5.5**
    """
    
    @given(
        secret_key=csrf_secret_key_strategy(),
        session_ids=st.lists(session_id_strategy(), min_size=1, max_size=10),
        token_lifetime=st.integers(min_value=300, max_value=7200)  # 5 minutes to 2 hours
    )
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_property_csrf_token_generation_and_validation(
        self, 
        secret_key: str, 
        session_ids: List[str], 
        token_lifetime: int
    ):
        """
        **Property 11: CSRF Token Validation**
        
        *For any* state-changing operation, the CSP_Engine should generate and validate 
        CSRF tokens, implement double-submit cookie pattern for sensitive operations, 
        and reject invalid tokens with 403 status and security event logging
        
        **Validates: Requirements 5.3, 5.4, 5.5**
        """
        # Create CSRF protection instance
        csrf_protection = CSRFProtection(
            secret_key=secret_key,
            token_lifetime=token_lifetime,
            double_submit=True
        )
        
        # Test token generation and validation for each session
        generated_tokens = {}
        
        for session_id in session_ids:
            # Property: Token generation should always succeed
            token = await csrf_protection.generate_csrf_token(session_id)
            assert token is not None, "Token generation should never fail"
            assert len(token) > 0, "Generated token should not be empty"
            assert isinstance(token, str), "Token should be a string"
            
            generated_tokens[session_id] = token
            
            # Property: Valid token should validate successfully
            is_valid = await csrf_protection.validate_csrf_token(token, session_id)
            assert is_valid, f"Freshly generated token should be valid for session {session_id}"
            
            # Property: Token should not validate for different session
            for other_session_id in session_ids:
                if other_session_id != session_id:
                    is_valid_other = await csrf_protection.validate_csrf_token(token, other_session_id)
                    assert not is_valid_other, f"Token should not be valid for different session {other_session_id}"
        
        # Property: Each session should have unique tokens
        unique_tokens = set(generated_tokens.values())
        assert len(unique_tokens) == len(generated_tokens), "Each session should have unique tokens"
        
        # Property: Invalid tokens should not validate
        invalid_tokens = [
            "",  # Empty token
            "invalid_token",  # Random string
            secrets.token_urlsafe(32),  # Random valid-looking token
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid"  # JWT-like but invalid
        ]
        
        for session_id in session_ids:
            for invalid_token in invalid_tokens:
                is_valid = await csrf_protection.validate_csrf_token(invalid_token, session_id)
                assert not is_valid, f"Invalid token '{invalid_token}' should not validate"
    
    @given(
        secret_key=csrf_secret_key_strategy(),
        session_id=session_id_strategy(),
        token_type=st.sampled_from([CSRFTokenType.SYNCHRONIZER, CSRFTokenType.DOUBLE_SUBMIT])
    )
    @settings(max_examples=100, deadline=3000)
    @pytest.mark.asyncio
    async def test_property_csrf_token_types(
        self, 
        secret_key: str, 
        session_id: str, 
        token_type: CSRFTokenType
    ):
        """
        **Property 11: CSRF Token Validation (Token Types)**
        
        *For any* token type (synchronizer or double-submit), the CSRF protection
        should generate valid tokens that can be properly validated
        
        **Validates: Requirements 5.3, 5.4, 5.5**
        """
        # Create CSRF protection instance
        csrf_protection = CSRFProtection(
            secret_key=secret_key,
            double_submit=(token_type == CSRFTokenType.DOUBLE_SUBMIT)
        )
        
        # Generate token of specific type
        token = await csrf_protection.generate_csrf_token(session_id, token_type)
        
        # Property: Token should be valid regardless of type
        is_valid = await csrf_protection.validate_csrf_token(token, session_id)
        assert is_valid, f"Token of type {token_type} should be valid"
        
        # Property: Token should be stored correctly
        stored_token = csrf_protection.token_storage.get(token)
        assert stored_token is not None, "Token should be stored"
        assert stored_token.token_type == token_type, "Stored token should have correct type"
        assert stored_token.session_id == session_id, "Stored token should have correct session ID"
        assert not stored_token.used, "Fresh token should not be marked as used"
    
    @given(
        secret_key=csrf_secret_key_strategy(),
        session_id=session_id_strategy(),
        token_lifetime=st.integers(min_value=1, max_value=10)  # Short lifetime for expiration testing
    )
    @settings(max_examples=50, deadline=15000)  # Longer deadline for sleep
    @pytest.mark.asyncio
    async def test_property_csrf_token_expiration(
        self, 
        secret_key: str, 
        session_id: str, 
        token_lifetime: int
    ):
        """
        **Property 11: CSRF Token Validation (Expiration)**
        
        *For any* expired CSRF token, the validation should fail and the token
        should be cleaned up from storage
        
        **Validates: Requirements 5.3, 5.4, 5.5**
        """
        # Create CSRF protection with short token lifetime
        csrf_protection = CSRFProtection(
            secret_key=secret_key,
            token_lifetime=token_lifetime
        )
        
        # Generate token
        token = await csrf_protection.generate_csrf_token(session_id)
        
        # Property: Fresh token should be valid
        is_valid = await csrf_protection.validate_csrf_token(token, session_id)
        assert is_valid, "Fresh token should be valid"
        
        # Wait for token to expire
        await asyncio.sleep(token_lifetime + 1)
        
        # Property: Expired token should not be valid
        is_valid_after_expiry = await csrf_protection.validate_csrf_token(token, session_id)
        assert not is_valid_after_expiry, "Expired token should not be valid"
        
        # Property: Expired token should be cleaned up
        # Trigger cleanup by generating a new token
        await csrf_protection.generate_csrf_token(session_id)
        assert token not in csrf_protection.token_storage, "Expired token should be cleaned up"
    
    @given(
        secret_key=csrf_secret_key_strategy(),
        session_id=session_id_strategy(),
        exempt_methods=st.sets(st.sampled_from(["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]), min_size=1, max_size=4),
        exempt_paths=st.sets(st.text(min_size=1, max_size=20), min_size=1, max_size=5)
    )
    @settings(max_examples=100, deadline=3000)
    @pytest.mark.asyncio
    async def test_property_csrf_exemptions(
        self, 
        secret_key: str, 
        session_id: str, 
        exempt_methods: Set[str], 
        exempt_paths: Set[str]
    ):
        """
        **Property 11: CSRF Token Validation (Exemptions)**
        
        *For any* exempt method or path, CSRF validation should be bypassed
        
        **Validates: Requirements 5.3, 5.4, 5.5**
        """
        # Create CSRF protection with custom exemptions
        csrf_protection = CSRFProtection(
            secret_key=secret_key,
            exempt_methods=exempt_methods,
            exempt_paths=exempt_paths
        )
        
        # Test exempt methods
        for method in exempt_methods:
            request = Mock(spec=Request)
            request.method = method
            request.url.path = "/api/v1/test"
            
            # Property: Exempt methods should be exempt
            is_exempt = csrf_protection._is_exempt(request)
            assert is_exempt, f"Method {method} should be exempt"
        
        # Test exempt paths
        for path in exempt_paths:
            request = Mock(spec=Request)
            request.method = "POST"  # Non-exempt method
            request.url.path = path
            
            # Property: Exempt paths should be exempt
            is_exempt = csrf_protection._is_exempt(request)
            assert is_exempt, f"Path {path} should be exempt"
        
        # Test non-exempt combinations
        non_exempt_methods = {"POST", "PUT", "PATCH", "DELETE"} - exempt_methods
        if non_exempt_methods:
            method = list(non_exempt_methods)[0]
            request = Mock(spec=Request)
            request.method = method
            request.url.path = "/api/v1/non-exempt-path"
            
            # Property: Non-exempt combinations should not be exempt
            is_exempt = csrf_protection._is_exempt(request)
            assert not is_exempt, f"Non-exempt method {method} on non-exempt path should not be exempt"


class TestCSRFAttackDetection:
    """
    Property-based tests for CSRF attack detection functionality
    
    **Validates: Requirements 5.6**
    """
    
    @given(
        client_ip=st.ip_addresses(v=4).map(str),
        csrf_failure_count=st.integers(min_value=5, max_value=15),
        time_window_minutes=st.integers(min_value=1, max_value=10)
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
        **Property 12: CSRF Attack Detection**
        
        *For any* repeated CSRF token validation failures from the same IP, 
        the Security_Monitor should track patterns and generate security alerts 
        for potential attack detection
        
        **Validates: Requirements 5.6**
        """
        # Initialize security monitor
        from middleware.security_monitor import initialize_security_monitor
        monitor = initialize_security_monitor(correlation_tracking=True)
        
        # Create CSRF protection
        csrf_protection = CSRFProtection(
            secret_key=secrets.token_urlsafe(32),
            token_lifetime=3600
        )
        
        # Simulate multiple CSRF failures from same IP
        base_time = datetime.utcnow()
        
        for i in range(csrf_failure_count):
            request_id = str(uuid.uuid4())
            
            # Log CSRF failure event
            await monitor.log_security_event(
                event_type=SecurityEventType.CSRF_TOKEN_FAILURE,
                details={
                    "attempted_token": f"invalid_token_{i}",
                    "endpoint": f"/api/v1/endpoint{i % 3}",
                    "method": "POST",
                    "user_agent": "TestAgent/1.0",
                    "failure_sequence": i + 1
                },
                severity=SecuritySeverity.MEDIUM,
                request_id=request_id,
                client_ip=client_ip,
                user_id=f"session_{i % 2}",  # Multiple sessions from same IP
                endpoint=f"/api/v1/endpoint{i % 3}"
            )
        
        # Property: Multiple CSRF failures should be tracked by IP
        ip_events = await monitor.get_events_by_ip(client_ip, hours=1)
        csrf_events = [e for e in ip_events if e.event_type == SecurityEventType.CSRF_TOKEN_FAILURE]
        assert len(csrf_events) == csrf_failure_count, f"Should track all {csrf_failure_count} CSRF failures"
        
        # Property: CSRF failures should have appropriate threat scores
        for event in csrf_events:
            assert event.threat_score > 0, "CSRF failures should have positive threat scores"
            assert event.severity == SecuritySeverity.MEDIUM, "CSRF failures should be MEDIUM severity"
        
        # Property: High frequency of CSRF failures should trigger alerts
        if csrf_failure_count >= 5:  # Threshold from security monitor implementation
            # Trigger threat analysis on last event
            await monitor._analyze_for_threats(csrf_events[-1])
            
            # Check for CSRF attack alerts
            csrf_alerts = [
                alert for alert in monitor.active_alerts.values()
                if alert.alert_type == "csrf_attack" and client_ip in alert.affected_ips
            ]
            
            if csrf_failure_count >= 5:  # Implementation threshold
                assert len(csrf_alerts) >= 1, f"Should generate CSRF attack alert for {csrf_failure_count} failures"
                
                alert = csrf_alerts[0]
                assert alert.severity == SecuritySeverity.MEDIUM, "CSRF attack alert should be MEDIUM severity"
                assert client_ip in alert.affected_ips, "Alert should include attacking IP"
                assert "csrf" in alert.description.lower(), "Alert should mention CSRF"
    
    @given(
        client_ips=st.lists(st.ip_addresses(v=4).map(str), min_size=2, max_size=5),
        failures_per_ip=st.integers(min_value=3, max_value=8)
    )
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_property_csrf_attack_isolation_by_ip(
        self, 
        client_ips: List[str], 
        failures_per_ip: int
    ):
        """
        **Property 12: CSRF Attack Detection (IP Isolation)**
        
        *For any* CSRF attack detection, alerts should be properly isolated by IP
        and not trigger false positives for other IPs
        
        **Validates: Requirements 5.6**
        """
        # Initialize security monitor
        from middleware.security_monitor import initialize_security_monitor
        monitor = initialize_security_monitor(correlation_tracking=True)
        
        # Simulate CSRF failures from multiple IPs
        for ip_index, client_ip in enumerate(client_ips):
            for failure_index in range(failures_per_ip):
                request_id = str(uuid.uuid4())
                
                await monitor.log_security_event(
                    event_type=SecurityEventType.CSRF_TOKEN_FAILURE,
                    details={
                        "attempted_token": f"invalid_token_{ip_index}_{failure_index}",
                        "endpoint": "/api/v1/profile/update",
                        "method": "POST",
                        "ip_group": ip_index
                    },
                    severity=SecuritySeverity.MEDIUM,
                    request_id=request_id,
                    client_ip=client_ip,
                    user_id=f"session_{ip_index}",
                    endpoint="/api/v1/profile/update"
                )
        
        # Property: Each IP should have correct number of events
        for client_ip in client_ips:
            ip_events = await monitor.get_events_by_ip(client_ip, hours=1)
            csrf_events = [e for e in ip_events if e.event_type == SecurityEventType.CSRF_TOKEN_FAILURE]
            assert len(csrf_events) == failures_per_ip, f"IP {client_ip} should have {failures_per_ip} CSRF events"
        
        # Property: Events should be properly isolated by IP
        all_events = list(monitor.recent_events)
        csrf_events = [e for e in all_events if e.event_type == SecurityEventType.CSRF_TOKEN_FAILURE]
        
        for client_ip in client_ips:
            ip_csrf_events = [e for e in csrf_events if e.client_ip == client_ip]
            assert len(ip_csrf_events) == failures_per_ip, f"Should have exactly {failures_per_ip} events for {client_ip}"
            
            # Verify no cross-contamination
            for event in ip_csrf_events:
                assert event.client_ip == client_ip, "Event should belong to correct IP"


class TestCSRFMiddlewareIntegration:
    """
    Property-based tests for CSRF middleware integration
    """
    
    @given(
        secret_key=csrf_secret_key_strategy(),
        enabled=st.booleans(),
        testing_mode=st.booleans(),
        requests=st.lists(mock_request_strategy(), min_size=1, max_size=10)
    )
    @settings(max_examples=50, deadline=5000)
    @pytest.mark.asyncio
    async def test_property_csrf_middleware_behavior(
        self, 
        secret_key: str, 
        enabled: bool, 
        testing_mode: bool, 
        requests: List[Mock]
    ):
        """
        Test CSRF middleware behavior under different configurations
        """
        # Create CSRF protection and middleware
        csrf_protection = CSRFProtection(secret_key=secret_key)
        
        # Mock app
        async def mock_app(request):
            return {"status": "success"}
        
        middleware = CSRFMiddleware(
            app=mock_app,
            csrf_protection=csrf_protection,
            enabled=enabled,
            testing_mode=testing_mode
        )
        
        # Test each request
        for request in requests:
            # Property: Middleware should handle all requests without crashing
            try:
                # Mock call_next function
                async def call_next(req):
                    return Mock(status_code=200)
                
                response = await middleware.dispatch(request, call_next)
                
                # Property: Response should always be returned
                assert response is not None, "Middleware should always return a response"
                
                # Property: When disabled or in testing mode, requests should pass through
                if not enabled or testing_mode:
                    assert response.status_code != 403, "Disabled/testing middleware should not block requests"
                
            except Exception as e:
                # Property: Middleware should not raise unhandled exceptions
                pytest.fail(f"Middleware raised unhandled exception: {str(e)}")


# Convenience functions property tests
class TestCSRFConvenienceFunctions:
    """
    Property-based tests for CSRF convenience functions
    """
    
    @given(
        session_ids=st.lists(session_id_strategy(), min_size=1, max_size=5),
        secret_key=csrf_secret_key_strategy()
    )
    @settings(max_examples=100, deadline=3000)
    @pytest.mark.asyncio
    async def test_property_convenience_functions(
        self, 
        session_ids: List[str], 
        secret_key: str
    ):
        """
        Test CSRF convenience functions work correctly
        """
        # Initialize CSRF protection
        csrf_protection = initialize_csrf_protection(secret_key=secret_key)
        
        for session_id in session_ids:
            # Property: Token generation convenience function should work
            token = await generate_csrf_token_for_session(session_id)
            assert token is not None, "Convenience function should generate token"
            assert len(token) > 0, "Generated token should not be empty"
            
            # Property: Token validation convenience function should work
            is_valid = await validate_csrf_token_for_session(token, session_id)
            assert is_valid, "Convenience function should validate correct token"
            
            # Property: Invalid token should not validate
            is_invalid = await validate_csrf_token_for_session("invalid_token", session_id)
            assert not is_invalid, "Convenience function should reject invalid token"


if __name__ == "__main__":
    # Run property-based tests
    pytest.main([__file__, "-v", "--tb=short"])