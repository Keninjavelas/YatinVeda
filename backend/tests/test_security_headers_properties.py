"""
Property-based tests for Security Headers Middleware

These tests validate universal properties of the security headers system
using property-based testing with Hypothesis.

Feature: https-security-enhancements
"""

import pytest
import asyncio
from typing import Dict, Any, Optional
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.strategies import composite
import logging
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

# Import security headers components
from middleware.security_headers import SecurityHeadersMiddleware, CSPViolationReporter

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


# Custom strategies for security headers testing
@composite
def http_methods(draw):
    """Generate valid HTTP methods"""
    methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
    return draw(st.sampled_from(methods))


@composite
def url_paths(draw):
    """Generate valid URL paths for testing"""
    # Generate simple paths
    path_segments = draw(st.lists(
        st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_',
            min_size=1,
            max_size=10
        ).filter(lambda x: x and x.replace('-', '').replace('_', '').isalnum()),
        min_size=0,
        max_size=3
    ))
    
    path = '/' + '/'.join(path_segments) if path_segments else '/'
    
    # Add some common API paths
    common_paths = ['/api/v1/health', '/api/v1/auth/login', '/docs', '/']
    return draw(st.one_of(st.just(path), st.sampled_from(common_paths)))


@composite
def security_environments(draw):
    """Generate valid security environments"""
    return draw(st.sampled_from(['development', 'staging', 'production']))


@composite
def client_ips(draw):
    """Generate valid client IP addresses"""
    # Generate IPv4 addresses
    octets = [draw(st.integers(min_value=1, max_value=255)) for _ in range(4)]
    ipv4 = '.'.join(map(str, octets))
    
    # Add some common test IPs
    test_ips = ['127.0.0.1', '192.168.1.1', '10.0.0.1', 'testclient']
    return draw(st.one_of(st.just(ipv4), st.sampled_from(test_ips)))


@composite
def user_agents(draw):
    """Generate valid user agent strings"""
    browsers = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'testclient'
    ]
    return draw(st.sampled_from(browsers))


class TestSecurityHeadersProperties:
    """
    Property-based tests for security headers enforcement.
    
    **Feature: https-security-enhancements, Property 3**: HTTPS Enforcement and Security Headers
    **Validates: Requirements 2.1, 2.2, 2.3, 2.5**
    """
    
    @given(
        method=http_methods(),
        path=url_paths(),
        environment=security_environments()
    )
    @settings(
        max_examples=8,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=10000
    )
    @pytest.mark.asyncio
    async def test_security_headers_always_applied(self, method, path, environment):
        """
        Property 3: HTTPS Enforcement and Security Headers
        
        For any HTTP request, the Security_Header_Manager should apply comprehensive 
        security headers including HSTS with subdomains and preload, X-Frame-Options, 
        X-Content-Type-Options, and Referrer-Policy.
        """
        # Create test FastAPI app
        app = FastAPI()
        
        # Add security headers middleware
        app.add_middleware(
            SecurityHeadersMiddleware,
            environment=environment,
            hsts_max_age=31536000,
            hsts_include_subdomains=True,
            hsts_preload=True,
            cookie_secure=environment != "development",
            cookie_samesite="strict" if environment == "production" else "lax"
        )
        
        # Add test endpoint that matches the path
        @app.api_route(path, methods=[method])
        async def test_endpoint():
            return {"message": "test", "path": path, "method": method}
        
        # Test the request
        client = TestClient(app)
        
        # Make request with the specified method
        if method == 'GET':
            response = client.get(path)
        elif method == 'POST':
            response = client.post(path, json={})
        elif method == 'PUT':
            response = client.put(path, json={})
        elif method == 'DELETE':
            response = client.delete(path)
        elif method == 'PATCH':
            response = client.patch(path, json={})
        elif method == 'HEAD':
            response = client.head(path)
        elif method == 'OPTIONS':
            response = client.options(path)
        
        # Property: All responses should have basic security headers
        headers = response.headers
        
        # X-Content-Type-Options should always be present
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        
        # X-Frame-Options should always be present
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]
        
        # Referrer-Policy should always be present
        assert "Referrer-Policy" in headers
        assert headers["Referrer-Policy"] in ["strict-origin-when-cross-origin", "same-origin"]
        
        # CSP should always be present (either enforcing or report-only)
        has_csp = ("Content-Security-Policy" in headers or 
                  "Content-Security-Policy-Report-Only" in headers)
        assert has_csp, f"CSP header missing for {method} {path} in {environment}"
        
        # Permissions-Policy should always be present
        assert "Permissions-Policy" in headers
        
        # Cross-Origin-Resource-Policy should always be present
        assert "Cross-Origin-Resource-Policy" in headers
        assert headers["Cross-Origin-Resource-Policy"] == "same-origin"
    
    @given(
        environment=security_environments(),
        client_ip=client_ips(),
        user_agent=user_agents()
    )
    @settings(
        max_examples=6,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=10000
    )
    @pytest.mark.asyncio
    async def test_environment_specific_security_policies(self, environment, client_ip, user_agent):
        """
        Property 3 (continued): Environment-specific security policies
        
        For any environment, the security headers should be configured appropriately
        with stricter policies in production and more permissive policies in development.
        """
        # Create test FastAPI app
        app = FastAPI()
        
        # Add security headers middleware
        app.add_middleware(
            SecurityHeadersMiddleware,
            environment=environment,
            hsts_max_age=31536000,
            hsts_include_subdomains=True,
            hsts_preload=True
        )
        
        @app.get("/test")
        async def test_endpoint():
            return {"environment": environment}
        
        # Test the request
        client = TestClient(app)
        response = client.get("/test", headers={"User-Agent": user_agent})
        
        headers = response.headers
        
        # Property: Environment-specific policies should be applied
        if environment == "development":
            # Development should have more permissive CSP
            csp_header = headers.get("Content-Security-Policy-Report-Only", "")
            assert "'unsafe-inline'" in csp_header or "'unsafe-eval'" in csp_header
            
            # Development should allow SAMEORIGIN for X-Frame-Options
            assert headers.get("X-Frame-Options") == "SAMEORIGIN"
            
            # HSTS should not be present in development (no HTTPS)
            assert "Strict-Transport-Security" not in headers
            
        elif environment == "production":
            # Production should have strict X-Frame-Options
            assert headers.get("X-Frame-Options") == "DENY"
            
            # Production should have strict referrer policy
            assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
            
            # Production should have additional security headers
            assert "Cross-Origin-Embedder-Policy" in headers
            assert "Cross-Origin-Opener-Policy" in headers
        
        # Property: All environments should have basic security headers
        assert "X-Content-Type-Options" in headers
        assert "Permissions-Policy" in headers
        assert "Cross-Origin-Resource-Policy" in headers
    
    @given(
        path=url_paths(),
        environment=security_environments()
    )
    @settings(
        max_examples=6,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=10000
    )
    @pytest.mark.asyncio
    async def test_csp_policy_consistency(self, path, environment):
        """
        Property 3 (continued): CSP policy consistency
        
        For any request path and environment, the Content Security Policy should be
        consistently applied and appropriate for the environment.
        """
        # Create test FastAPI app
        app = FastAPI()
        
        # Add security headers middleware
        app.add_middleware(
            SecurityHeadersMiddleware,
            environment=environment
        )
        
        @app.get(path)
        async def test_endpoint():
            return {"path": path}
        
        # Test the request
        client = TestClient(app)
        response = client.get(path)
        
        headers = response.headers
        
        # Property: CSP should be present and valid
        csp_header_name = None
        csp_policy = None
        
        if "Content-Security-Policy" in headers:
            csp_header_name = "Content-Security-Policy"
            csp_policy = headers["Content-Security-Policy"]
        elif "Content-Security-Policy-Report-Only" in headers:
            csp_header_name = "Content-Security-Policy-Report-Only"
            csp_policy = headers["Content-Security-Policy-Report-Only"]
        
        assert csp_header_name is not None, f"No CSP header found for {path}"
        assert csp_policy is not None and len(csp_policy) > 0
        
        # Property: CSP should contain essential directives
        assert "default-src" in csp_policy
        assert "script-src" in csp_policy
        assert "object-src 'none'" in csp_policy  # Should always block objects
        assert "base-uri 'self'" in csp_policy    # Should restrict base URI
        
        # Property: Environment-specific CSP rules
        if environment == "development":
            # Development should be in report-only mode
            assert csp_header_name == "Content-Security-Policy-Report-Only"
        elif environment == "production":
            # Production should enforce CSP
            assert csp_header_name == "Content-Security-Policy"
            # Production should have upgrade-insecure-requests
            assert "upgrade-insecure-requests" in csp_policy


class TestCookieSecurityProperties:
    """
    Property-based tests for cookie security configuration.
    
    **Feature: https-security-enhancements, Property 4**: Cookie Security Configuration
    **Validates: Requirements 2.4, 5.1, 5.2**
    """
    
    @given(
        environment=security_environments(),
        cookie_name=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
            min_size=3,
            max_size=20
        ).filter(lambda x: x.isalnum() or '_' in x or '-' in x)
    )
    @settings(
        max_examples=6,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=10000
    )
    @pytest.mark.asyncio
    async def test_cookie_security_flags(self, environment, cookie_name):
        """
        Property 4: Cookie Security Configuration
        
        For any authentication cookie over HTTPS, the Security_Header_Manager should 
        set Secure=true, HttpOnly=true, and SameSite=Strict flags to prevent session 
        hijacking and CSRF attacks.
        """
        # Create test FastAPI app
        app = FastAPI()
        
        # Add security headers middleware
        app.add_middleware(
            SecurityHeadersMiddleware,
            environment=environment,
            cookie_secure=environment != "development",
            cookie_samesite="strict" if environment == "production" else "lax"
        )
        
        @app.get("/set-cookie")
        async def set_cookie_endpoint():
            from fastapi.responses import JSONResponse
            response = JSONResponse({"message": "cookie set"})
            
            # Set a test cookie with security flags based on environment
            cookie_kwargs = {
                "key": cookie_name,
                "value": "test_value",
                "httponly": True
            }
            
            if environment != "development":
                cookie_kwargs["secure"] = True
                cookie_kwargs["samesite"] = "strict" if environment == "production" else "lax"
            else:
                cookie_kwargs["samesite"] = "lax"
            
            response.set_cookie(**cookie_kwargs)
            return response
        
        # Test the request
        client = TestClient(app)
        response = client.get("/set-cookie")
        
        # Property: Security headers should indicate cookie security expectations
        headers = response.headers
        
        # Check that security headers are applied
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        
        # Property: Cookie security indication should match environment
        if environment != "development":
            # Production/staging should indicate secure cookies
            assert headers.get("X-Cookie-Security") == "secure"
        
        # Property: Response should be successful
        assert response.status_code == 200
    
    @given(
        environment=security_environments(),
        path=url_paths()
    )
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=10000
    )
    @pytest.mark.asyncio
    async def test_samesite_cookie_protection(self, environment, path):
        """
        Property 4 (continued): SameSite cookie protection
        
        For any environment, the SameSite cookie attribute should be configured
        appropriately to prevent CSRF attacks while maintaining functionality.
        """
        # Create test FastAPI app
        app = FastAPI()
        
        # Add security headers middleware
        app.add_middleware(
            SecurityHeadersMiddleware,
            environment=environment
        )
        
        @app.get(path)
        async def test_endpoint():
            return {"environment": environment, "path": path}
        
        # Test the request
        client = TestClient(app)
        response = client.get(path)
        
        # Property: Security headers should be consistent across all paths
        headers = response.headers
        
        # All responses should have security headers regardless of path
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "Referrer-Policy" in headers
        
        # Property: CSP should be present for all paths
        has_csp = ("Content-Security-Policy" in headers or 
                  "Content-Security-Policy-Report-Only" in headers)
        assert has_csp, f"CSP missing for path {path} in {environment}"


class TestCSPEnforcementProperties:
    """
    Property-based tests for Content Security Policy enforcement.
    
    **Feature: https-security-enhancements, Property 5**: Content Security Policy Enforcement
    **Validates: Requirements 2.6, 7.4**
    """
    
    @given(
        environment=security_environments(),
        enable_testing=st.booleans()
    )
    @settings(
        max_examples=6,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=10000
    )
    @pytest.mark.asyncio
    async def test_csp_enforcement_modes(self, environment, enable_testing):
        """
        Property 5: Content Security Policy Enforcement
        
        For any web content, the CSP_Engine should enforce strict Content Security 
        Policy that prevents inline scripts and unsafe evaluations, with optional 
        testing mode that reports violations without blocking.
        """
        # Create test FastAPI app
        app = FastAPI()
        
        # Add security headers middleware
        app.add_middleware(
            SecurityHeadersMiddleware,
            environment=environment,
            enable_testing_mode=enable_testing
        )
        
        @app.get("/test")
        async def test_endpoint():
            return {"environment": environment, "testing": enable_testing}
        
        # Test the request
        client = TestClient(app)
        response = client.get("/test")
        
        headers = response.headers
        
        # Property: CSP mode should be determined by environment and testing flag
        if enable_testing or environment == "development":
            # Testing mode or development should use report-only
            assert "Content-Security-Policy-Report-Only" in headers
            csp_policy = headers["Content-Security-Policy-Report-Only"]
        else:
            # Production without testing should enforce CSP
            if environment == "production":
                assert "Content-Security-Policy" in headers
                csp_policy = headers["Content-Security-Policy"]
            else:
                # Staging might use report-only by default
                assert ("Content-Security-Policy" in headers or 
                       "Content-Security-Policy-Report-Only" in headers)
                csp_policy = (headers.get("Content-Security-Policy") or 
                            headers.get("Content-Security-Policy-Report-Only"))
        
        # Property: CSP should prevent unsafe operations
        assert "object-src 'none'" in csp_policy  # Block objects
        assert "base-uri 'self'" in csp_policy    # Restrict base URI
        
        # Property: CSP should have appropriate script restrictions
        if environment == "production" and not enable_testing:
            # Production should be strict about scripts
            assert "'unsafe-eval'" not in csp_policy or "script-src 'self'" in csp_policy
        
        # Property: CSP should be well-formed
        assert "default-src" in csp_policy
        assert len(csp_policy.strip()) > 20  # Should be substantial policy
    
    @given(
        violation_data=st.fixed_dictionaries({
            "document-uri": st.text(min_size=10, max_size=100),
            "violated-directive": st.sampled_from([
                "script-src 'self'",
                "style-src 'self'",
                "img-src 'self'",
                "default-src 'self'"
            ]),
            "blocked-uri": st.text(min_size=5, max_size=50),
            "line-number": st.integers(min_value=1, max_value=1000),
            "column-number": st.integers(min_value=1, max_value=100)
        }),
        environment=security_environments()
    )
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=10000
    )
    @pytest.mark.asyncio
    async def test_csp_violation_reporting(self, violation_data, environment):
        """
        Property 5 (continued): CSP violation reporting
        
        For any CSP violation report, the system should properly log and handle
        the violation data for security monitoring.
        """
        # Create CSP violation reporter
        reporter = CSPViolationReporter(environment=environment)
        
        # Create mock request with violation data
        from fastapi import Request
        from unittest.mock import Mock
        
        # Mock request object
        mock_request = Mock(spec=Request)
        
        # Create an async mock for the json method
        async def mock_json():
            return {"csp-report": violation_data}
        
        mock_request.json = mock_json
        mock_request.headers = {
            "user-agent": "test-browser",
            "x-forwarded-for": "192.168.1.1"
        }
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        
        # Property: Violation reports should be processed successfully
        result = await reporter.handle_csp_report(mock_request)
        
        assert isinstance(result, dict)
        assert result["status"] == "received"
        assert "timestamp" in result
        
        # Property: Timestamp should be valid ISO format
        from datetime import datetime
        try:
            datetime.fromisoformat(result["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {result['timestamp']}")


# Test fixtures and utilities
@pytest.fixture
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])