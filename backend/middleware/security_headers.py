"""
Security Headers Middleware for YatinVeda

This middleware implements comprehensive security headers including:
- HSTS (HTTP Strict Transport Security) with subdomains and preload
- Content Security Policy (CSP) with strict policies
- X-Frame-Options for clickjacking protection
- X-Content-Type-Options for MIME type sniffing protection
- Referrer-Policy for referrer information control
- Secure cookie configuration for HTTPS
"""

import os
import logging
from typing import Optional, Dict, Any, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for comprehensive security headers management.
    
    Implements HSTS, CSP, and other security headers with environment-specific configuration.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
        csp_policy: Optional[str] = None,
        environment: str = "development",
        cookie_secure: bool = True,
        cookie_samesite: str = "strict",
        enable_testing_mode: bool = False
    ):
        """
        Initialize Security Headers Middleware.
        
        Args:
            app: ASGI application
            hsts_max_age: HSTS max-age in seconds (default: 1 year)
            hsts_include_subdomains: Include subdomains in HSTS
            hsts_preload: Enable HSTS preload
            csp_policy: Custom CSP policy string
            environment: Deployment environment (development, staging, production)
            cookie_secure: Set Secure flag on cookies
            cookie_samesite: SameSite cookie attribute
            enable_testing_mode: Enable CSP testing mode (report-only)
        """
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.environment = environment
        self.cookie_secure = cookie_secure
        self.cookie_samesite = cookie_samesite
        self.enable_testing_mode = enable_testing_mode
        
        # Load environment-specific configuration
        self.config = self._load_security_config()
        
        # Set up CSP policy
        self.csp_policy = csp_policy or self._get_default_csp_policy()
        
        logger.info(f"Security Headers Middleware initialized: environment={environment}")
    
    def _load_security_config(self) -> Dict[str, Any]:
        """Load environment-specific security configuration"""
        config = {
            "development": {
                "hsts_enabled": False,  # Don't enforce HSTS in development
                "csp_report_only": True,
                "strict_policies": False,
                "allowed_hosts": ["localhost", "127.0.0.1", "0.0.0.0"],
                "cookie_secure_override": False  # Allow insecure cookies in dev
            },
            "staging": {
                "hsts_enabled": True,
                "csp_report_only": True,  # Test CSP in staging
                "strict_policies": True,
                "allowed_hosts": os.getenv("STAGING_HOSTS", "staging.yatinveda.com").split(","),
                "cookie_secure_override": None
            },
            "production": {
                "hsts_enabled": True,
                "csp_report_only": False,  # Enforce CSP in production
                "strict_policies": True,
                "allowed_hosts": os.getenv("PRODUCTION_HOSTS", "yatinveda.com,api.yatinveda.com").split(","),
                "cookie_secure_override": None
            }
        }
        
        return config.get(self.environment, config["development"])
    
    def _get_default_csp_policy(self) -> str:
        """Generate default Content Security Policy based on environment"""
        if self.environment == "development":
            # More permissive CSP for development
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:* 127.0.0.1:*; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss: localhost:* 127.0.0.1:*; "
                "media-src 'self'; "
                "object-src 'none'; "
                "frame-ancestors 'self'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # Strict CSP for staging/production - more specific for YatinVeda
            allowed_domains = os.getenv("CSP_ALLOWED_DOMAINS", "yatinveda.com,www.yatinveda.com,api.yatinveda.com").split(",")
            img_src_domains = " ".join([f"https://{domain}" for domain in allowed_domains])
            connect_src_domains = " ".join([f"https://{domain}" for domain in allowed_domains])
            
            # Add any CDN domains or external APIs if configured
            cdn_domains = os.getenv("CDN_DOMAINS", "")
            if cdn_domains:
                img_src_domains += " " + " ".join([f"https://{domain}" for domain in cdn_domains.split(",")])
                connect_src_domains += " " + " ".join([f"https://{domain}" for domain in cdn_domains.split(",")])
            
            # Add allowed font domains
            font_domains = os.getenv("FONT_DOMAINS", "fonts.googleapis.com,fonts.gstatic.com")
            font_src_domains = " ".join([f"https://{domain}" for domain in font_domains.split(",")])
            
            # Add allowed script domains (for analytics, etc.)
            script_domains = os.getenv("SCRIPT_DOMAINS", "")
            script_src_domains = ""
            if script_domains:
                script_src_domains = " ".join([f"https://{domain}" for domain in script_domains.split(",")])
            
            return (
                f"default-src 'self'; "
                f"script-src 'self'{f' {script_src_domains}' if script_src_domains else ''}; "
                f"style-src 'self' 'unsafe-inline'; "
                f"img-src 'self' data: {img_src_domains}; "
                f"font-src 'self' {font_src_domains}; "
                f"connect-src 'self' {connect_src_domains}; "
                f"media-src 'self' https:; "
                f"object-src 'none'; "
                f"frame-ancestors 'none'; "
                f"base-uri 'self'; "
                f"form-action 'self'; "
                f"upgrade-insecure-requests; "
                f"report-uri /api/v1/security/csp-report"
            )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers to response.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain
            
        Returns:
            Response with security headers applied
        """
        # Process the request
        response = await call_next(request)
        
        # Apply security headers
        self._apply_security_headers(request, response)
        
        # Apply cookie security settings
        self._apply_cookie_security(response)
        
        # Log security header application
        self._log_security_headers(request, response)
        
        return response
    
    def _apply_security_headers(self, request: Request, response: Response) -> None:
        """Apply comprehensive security headers to response"""
        
        # HSTS (HTTP Strict Transport Security)
        if self.config["hsts_enabled"] and self._is_https_request(request):
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # Content Security Policy
        csp_header = "Content-Security-Policy-Report-Only" if (
            self.config["csp_report_only"] or self.enable_testing_mode
        ) else "Content-Security-Policy"
        response.headers[csp_header] = self.csp_policy
        
        # X-Frame-Options (Clickjacking protection)
        response.headers["X-Frame-Options"] = "DENY" if self.config["strict_policies"] else "SAMEORIGIN"
        
        # X-Content-Type-Options (MIME type sniffing protection)
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection (Legacy XSS protection)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy (Referrer information control)
        if self.config["strict_policies"]:
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        else:
            response.headers["Referrer-Policy"] = "same-origin"
        
        # Permissions-Policy (Feature policy restrictions)
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy
        
        # Cross-Origin-Embedder-Policy
        if self.config["strict_policies"]:
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        
        # Cross-Origin-Opener-Policy
        if self.config["strict_policies"]:
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        
        # Cross-Origin-Resource-Policy
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    
    def _apply_cookie_security(self, response: Response) -> None:
        """Apply security settings to cookies in response"""
        if not hasattr(response, 'set_cookie'):
            return
        
        # Check if we should apply secure cookie settings
        should_secure = self.cookie_secure
        if self.config.get("cookie_secure_override") is not None:
            should_secure = self.config["cookie_secure_override"]
        
        # Note: Cookie security is primarily handled by FastAPI's cookie settings
        # This middleware ensures headers are consistent with cookie policies
        
        # Add security-related response headers for cookie handling
        if should_secure:
            # Indicate that cookies should be secure
            response.headers["X-Cookie-Security"] = "secure"
    
    def _is_https_request(self, request: Request) -> bool:
        """Check if request is over HTTPS"""
        # Check various ways HTTPS can be indicated
        if request.url.scheme == "https":
            return True
        
        # Check for proxy headers
        if request.headers.get("x-forwarded-proto") == "https":
            return True
        
        if request.headers.get("x-forwarded-ssl") == "on":
            return True
        
        return False
    
    def _log_security_headers(self, request: Request, response: Response) -> None:
        """Log security header application for monitoring"""
        try:
            security_info = {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request.headers.get("x-request-id", "unknown"),
                "client_ip": self._get_client_ip(request),
                "path": str(request.url.path),
                "method": request.method,
                "is_https": self._is_https_request(request),
                "headers_applied": {
                    "hsts": "Strict-Transport-Security" in response.headers,
                    "csp": any(h in response.headers for h in ["Content-Security-Policy", "Content-Security-Policy-Report-Only"]),
                    "x_frame_options": "X-Frame-Options" in response.headers,
                    "x_content_type_options": "X-Content-Type-Options" in response.headers,
                    "referrer_policy": "Referrer-Policy" in response.headers
                },
                "environment": self.environment
            }
            
            logger.debug(f"Security headers applied: {json.dumps(security_info)}")
            
        except Exception as e:
            logger.warning(f"Failed to log security headers: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first (proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown"


class CSPViolationReporter:
    """
    Handler for Content Security Policy violation reports.
    
    Processes CSP violation reports and logs them for security monitoring.
    """
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.logger = logging.getLogger(f"{__name__}.CSPViolationReporter")
    
    async def handle_csp_report(self, request: Request) -> Dict[str, Any]:
        """
        Handle CSP violation report.
        
        Args:
            request: Request containing CSP violation report
            
        Returns:
            Response data for the report endpoint
        """
        try:
            # Parse CSP violation report
            report_data = await request.json()
            
            # Extract violation details
            csp_report = report_data.get("csp-report", {})
            
            violation_info = {
                "timestamp": datetime.utcnow().isoformat(),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", "unknown"),
                "document_uri": csp_report.get("document-uri"),
                "violated_directive": csp_report.get("violated-directive"),
                "blocked_uri": csp_report.get("blocked-uri"),
                "source_file": csp_report.get("source-file"),
                "line_number": csp_report.get("line-number"),
                "column_number": csp_report.get("column-number"),
                "original_policy": csp_report.get("original-policy"),
                "environment": self.environment
            }
            
            # Log CSP violation
            self.logger.warning(f"CSP Violation: {json.dumps(violation_info)}")
            
            # In production, you might want to send this to a security monitoring system
            if self.environment == "production":
                await self._send_to_security_monitor(violation_info)
            
            return {"status": "received", "timestamp": violation_info["timestamp"]}
            
        except Exception as e:
            self.logger.error(f"Failed to process CSP violation report: {str(e)}")
            return {"status": "error", "message": "Failed to process report"}
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _send_to_security_monitor(self, violation_info: Dict[str, Any]) -> None:
        """Send CSP violation to security monitoring system"""
        # Placeholder for integration with security monitoring
        # In a real implementation, this would send to your security monitoring system
        pass


# Utility functions for cookie security
def set_secure_cookie_defaults() -> Dict[str, Any]:
    """
    Get secure cookie configuration for FastAPI.
    
    Returns:
        Dictionary with secure cookie settings
    """
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "development":
        return {
            "secure": False,  # Allow insecure cookies in development
            "httponly": True,
            "samesite": "lax"  # More permissive for development
        }
    else:
        return {
            "secure": True,   # Require HTTPS for cookies
            "httponly": True,
            "samesite": "strict"  # Strict CSRF protection
        }


def get_csp_report_endpoint():
    """
    Create FastAPI endpoint for CSP violation reporting.
    
    Returns:
        FastAPI route function for CSP reports
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    
    csp_reporter = CSPViolationReporter(
        environment=os.getenv("ENVIRONMENT", "development")
    )
    
    async def csp_report_endpoint(request: Request):
        """Endpoint to receive CSP violation reports"""
        result = await csp_reporter.handle_csp_report(request)
        return JSONResponse(content=result)
    
    return csp_report_endpoint