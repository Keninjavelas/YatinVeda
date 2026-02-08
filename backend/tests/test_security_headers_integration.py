"""
Integration test for Security Headers Middleware with main FastAPI app
"""

import os
import pytest
from fastapi.testclient import TestClient

# Set environment to development for testing
os.environ["ENVIRONMENT"] = "development"
os.environ["DISABLE_RATELIMIT"] = "1"  # Disable rate limiting for tests

from main import app


def test_security_headers_on_main_app():
    """Test security headers are applied to the main FastAPI application"""
    
    client = TestClient(app)
    
    # Test the root endpoint
    response = client.get("/")
    
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    # Check that response is successful
    assert response.status_code == 200
    
    # Check that security headers are present
    headers = response.headers
    
    # CSP should be present (report-only in development)
    assert "Content-Security-Policy-Report-Only" in headers
    csp_policy = headers["Content-Security-Policy-Report-Only"]
    assert "default-src 'self'" in csp_policy
    print(f"✅ CSP Policy: {csp_policy}")
    
    # X-Frame-Options should be present
    assert "X-Frame-Options" in headers
    assert headers["X-Frame-Options"] == "SAMEORIGIN"  # Less strict in development
    print(f"✅ X-Frame-Options: {headers['X-Frame-Options']}")
    
    # X-Content-Type-Options should be present
    assert "X-Content-Type-Options" in headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    print(f"✅ X-Content-Type-Options: {headers['X-Content-Type-Options']}")
    
    # Referrer-Policy should be present
    assert "Referrer-Policy" in headers
    print(f"✅ Referrer-Policy: {headers['Referrer-Policy']}")
    
    # Permissions-Policy should be present
    assert "Permissions-Policy" in headers
    print(f"✅ Permissions-Policy: {headers['Permissions-Policy']}")
    
    # HSTS should NOT be present in development (no HTTPS)
    assert "Strict-Transport-Security" not in headers
    print("✅ HSTS correctly disabled in development")
    
    print("🎉 All security headers integration tests passed!")


def test_csp_report_endpoint():
    """Test that CSP violation reporting endpoint exists and works"""
    
    client = TestClient(app)
    
    # Test CSP report endpoint with sample violation report
    csp_report = {
        "csp-report": {
            "document-uri": "https://example.com/page",
            "violated-directive": "script-src 'self'",
            "blocked-uri": "https://evil.com/script.js",
            "source-file": "https://example.com/page",
            "line-number": 10,
            "column-number": 5
        }
    }
    
    response = client.post("/api/v1/security/csp-report", json=csp_report)
    
    print(f"CSP report response: {response.status_code}")
    print(f"CSP report content: {response.json()}")
    
    # Should accept the report
    assert response.status_code == 200
    
    # Should return success status
    result = response.json()
    assert result["status"] == "received"
    assert "timestamp" in result
    
    print("✅ CSP violation reporting endpoint works correctly!")


def test_api_endpoints_have_security_headers():
    """Test that API endpoints also receive security headers"""
    
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/api/v1/health")
    
    print(f"Health endpoint status: {response.status_code}")
    
    # Should have security headers
    headers = response.headers
    assert "X-Content-Type-Options" in headers
    assert "X-Frame-Options" in headers
    assert "Content-Security-Policy-Report-Only" in headers
    
    print("✅ API endpoints have security headers!")


if __name__ == "__main__":
    test_security_headers_on_main_app()
    test_csp_report_endpoint()
    test_api_endpoints_have_security_headers()
    print("🚀 All integration tests passed!")