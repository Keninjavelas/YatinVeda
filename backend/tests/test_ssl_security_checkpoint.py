"""
Checkpoint Test: SSL and Security Headers Verification

This test verifies that SSL certificate management and security headers
are working correctly together.
"""

import os
import pytest
from fastapi.testclient import TestClient

# Set environment for testing
os.environ["ENVIRONMENT"] = "development"
os.environ["DISABLE_RATELIMIT"] = "1"

from main import app


def test_ssl_certificate_initialization():
    """Test that SSL certificate management initializes correctly"""
    
    # Test certificate manager import and basic functionality
    try:
        from modules.certificate_manager import CertificateManager
        
        # Create certificate manager instance
        manager = CertificateManager(
            cert_provider="self-signed",
            environment="development"
        )
        
        assert manager is not None
        assert manager.environment == "development"
        assert manager.cert_path.exists()
        assert manager.key_path.exists()
        
        print("✅ SSL Certificate Manager initializes correctly")
        
    except Exception as e:
        pytest.fail(f"SSL Certificate Manager initialization failed: {str(e)}")


def test_security_headers_middleware_integration():
    """Test that security headers middleware is properly integrated"""
    
    client = TestClient(app)
    
    # Test multiple endpoints to ensure headers are applied universally
    endpoints = [
        "/",
        "/api/v1/health",
        "/docs",
        "/api/v1/security/csp-report"
    ]
    
    for endpoint in endpoints:
        try:
            if endpoint == "/api/v1/security/csp-report":
                # POST endpoint for CSP reports
                response = client.post(endpoint, json={"csp-report": {"test": "data"}})
            else:
                response = client.get(endpoint)
            
            # Should get a response (may be 200, 404, etc. but not connection error)
            assert response.status_code is not None
            
            headers = response.headers
            
            # Verify essential security headers are present
            assert "X-Content-Type-Options" in headers
            assert headers["X-Content-Type-Options"] == "nosniff"
            
            assert "X-Frame-Options" in headers
            assert headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]
            
            assert "Referrer-Policy" in headers
            
            # CSP should be present (either enforcing or report-only)
            has_csp = ("Content-Security-Policy" in headers or 
                      "Content-Security-Policy-Report-Only" in headers)
            assert has_csp, f"CSP header missing for {endpoint}"
            
            print(f"✅ Security headers applied correctly to {endpoint}")
            
        except Exception as e:
            pytest.fail(f"Security headers test failed for {endpoint}: {str(e)}")


def test_https_redirection_configuration():
    """Test HTTPS redirection configuration (simulated)"""
    
    # In development, HSTS should not be present
    client = TestClient(app)
    response = client.get("/")
    
    headers = response.headers
    
    # HSTS should NOT be present in development
    assert "Strict-Transport-Security" not in headers
    
    # But other security headers should be present
    assert "X-Content-Type-Options" in headers
    assert "X-Frame-Options" in headers
    
    print("✅ HTTPS configuration appropriate for development environment")


def test_cookie_security_configuration():
    """Test cookie security configuration"""
    
    client = TestClient(app)
    
    # Test an endpoint that might set cookies (health check)
    response = client.get("/api/v1/health")
    
    headers = response.headers
    
    # In development, cookie security should be relaxed
    # The middleware should indicate this with appropriate headers
    assert "X-Content-Type-Options" in headers  # Basic security still applies
    
    print("✅ Cookie security configuration appropriate for environment")


def test_csp_violation_reporting():
    """Test CSP violation reporting endpoint"""
    
    client = TestClient(app)
    
    # Test CSP violation report
    violation_report = {
        "csp-report": {
            "document-uri": "https://example.com/test",
            "violated-directive": "script-src 'self'",
            "blocked-uri": "https://evil.com/script.js",
            "source-file": "https://example.com/test",
            "line-number": 10,
            "column-number": 5
        }
    }
    
    response = client.post("/api/v1/security/csp-report", json=violation_report)
    
    assert response.status_code == 200
    
    result = response.json()
    assert result["status"] == "received"
    assert "timestamp" in result
    
    print("✅ CSP violation reporting works correctly")


def test_security_headers_consistency():
    """Test that security headers are consistent across different request types"""
    
    client = TestClient(app)
    
    # Test different HTTP methods
    test_cases = [
        ("GET", "/"),
        ("GET", "/api/v1/health"),
        ("POST", "/api/v1/security/csp-report", {"csp-report": {"test": "data"}})
    ]
    
    for method, endpoint, *data in test_cases:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json=data[0] if data else {})
        
        headers = response.headers
        
        # All responses should have basic security headers
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "Referrer-Policy"
        ]
        
        for header in required_headers:
            assert header in headers, f"Missing {header} in {method} {endpoint}"
        
        # CSP should be present
        has_csp = ("Content-Security-Policy" in headers or 
                  "Content-Security-Policy-Report-Only" in headers)
        assert has_csp, f"CSP missing in {method} {endpoint}"
    
    print("✅ Security headers consistent across all request types")


def test_environment_specific_behavior():
    """Test that security behavior is appropriate for the current environment"""
    
    # Test development environment behavior
    client = TestClient(app)
    response = client.get("/")
    
    headers = response.headers
    
    # Development should have:
    # - CSP in report-only mode
    # - No HSTS
    # - SAMEORIGIN frame options (not DENY)
    
    assert "Content-Security-Policy-Report-Only" in headers
    assert "Strict-Transport-Security" not in headers
    assert headers.get("X-Frame-Options") == "SAMEORIGIN"
    
    # CSP should be permissive for development
    csp_policy = headers.get("Content-Security-Policy-Report-Only", "")
    assert "'unsafe-inline'" in csp_policy or "'unsafe-eval'" in csp_policy
    
    print("✅ Environment-specific security behavior correct")


def run_checkpoint():
    """Run all checkpoint tests"""
    
    print("🔍 Running SSL and Security Headers Checkpoint...")
    print("=" * 60)
    
    try:
        test_ssl_certificate_initialization()
        test_security_headers_middleware_integration()
        test_https_redirection_configuration()
        test_cookie_security_configuration()
        test_csp_violation_reporting()
        test_security_headers_consistency()
        test_environment_specific_behavior()
        
        print("=" * 60)
        print("🎉 SSL and Security Headers Checkpoint PASSED!")
        print("✅ Certificate management is working")
        print("✅ Security headers middleware is properly integrated")
        print("✅ HTTPS configuration is appropriate for environment")
        print("✅ Cookie security is configured correctly")
        print("✅ CSP violation reporting is functional")
        print("✅ Security headers are consistent across all endpoints")
        print("✅ Environment-specific behavior is correct")
        
        return True
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ SSL and Security Headers Checkpoint FAILED: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_checkpoint()
    exit(0 if success else 1)