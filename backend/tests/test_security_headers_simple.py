"""
Simple test for Security Headers Middleware
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from middleware.security_headers import SecurityHeadersMiddleware


def test_security_headers_middleware():
    """Test that security headers middleware applies headers correctly"""
    
    # Create a simple FastAPI app for testing
    app = FastAPI()
    
    # Add security headers middleware
    app.add_middleware(
        SecurityHeadersMiddleware,
        environment="production",
        hsts_max_age=31536000,
        hsts_include_subdomains=True,
        hsts_preload=True,
        cookie_secure=True,
        cookie_samesite="strict"
    )
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    # Test the middleware
    client = TestClient(app)
    response = client.get("/test")
    
    # Check that response is successful
    assert response.status_code == 200
    
    # Check that security headers are present
    headers = response.headers
    
    # CSP should be present (either enforcing or report-only)
    assert "Content-Security-Policy" in headers or "Content-Security-Policy-Report-Only" in headers
    
    # X-Frame-Options should be present
    assert "X-Frame-Options" in headers
    assert headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]
    
    # X-Content-Type-Options should be present
    assert "X-Content-Type-Options" in headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    
    # Referrer-Policy should be present
    assert "Referrer-Policy" in headers
    
    # Permissions-Policy should be present
    assert "Permissions-Policy" in headers
    
    print("✅ Security headers middleware test passed!")
    print(f"Applied headers: {list(headers.keys())}")


def test_development_vs_production_headers():
    """Test that development and production environments have different header policies"""
    
    # Test development environment
    app_dev = FastAPI()
    app_dev.add_middleware(
        SecurityHeadersMiddleware,
        environment="development"
    )
    
    @app_dev.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    client_dev = TestClient(app_dev)
    response_dev = client_dev.get("/test")
    
    # Test production environment
    app_prod = FastAPI()
    app_prod.add_middleware(
        SecurityHeadersMiddleware,
        environment="production"
    )
    
    @app_prod.get("/test")
    async def test_endpoint_prod():
        return {"message": "test"}
    
    client_prod = TestClient(app_prod)
    response_prod = client_prod.get("/test")
    
    # Development should not have HSTS (since it's not HTTPS)
    assert "Strict-Transport-Security" not in response_dev.headers
    
    # Production should have stricter X-Frame-Options
    assert response_prod.headers.get("X-Frame-Options") == "DENY"
    
    # Both should have basic security headers
    for response in [response_dev, response_prod]:
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "Referrer-Policy" in response.headers
    
    print("✅ Environment-specific headers test passed!")


if __name__ == "__main__":
    test_security_headers_middleware()
    test_development_vs_production_headers()
    print("🎉 All security headers tests passed!")