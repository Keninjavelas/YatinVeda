"""
Production Security Configuration Module for YatinVeda

This module implements environment-specific security configuration system with
strict production security policies, configurable settings via environment variables,
and integration with external logging systems.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import socket
import ssl
import certifi
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityEnvironment(Enum):
    """Security environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LoggingBackend(Enum):
    """External logging system backends"""
    LOCAL = "local"
    ELK = "elk"
    SPLUNK = "splunk"
    CLOUDWATCH = "cloudwatch"
    DATADOG = "datadog"


@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    # HTTPS enforcement
    enforce_https: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    
    # TLS configuration
    tls_min_version: str = "1.2"
    tls_prefer_version: str = "1.3"
    allowed_cipher_suites: List[str] = None
    
    # Cookie security
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: str = "strict"
    
    # CSRF protection
    csrf_enabled: bool = True
    csrf_token_lifetime: int = 3600
    csrf_double_submit: bool = True
    
    # Rate limiting
    rate_limiting_enabled: bool = True
    anonymous_rate_limit: str = "100/minute"
    authenticated_rate_limit: str = "1000/minute"
    login_rate_limit: str = "5/hour"
    
    # Security headers
    x_frame_options: str = "DENY"
    x_content_type_options: str = "nosniff"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"
    
    # Content Security Policy
    csp_default_src: str = "'self'"
    csp_script_src: str = "'self'"
    csp_style_src: str = "'self' 'unsafe-inline'"
    csp_img_src: str = "'self' data: https:"
    csp_connect_src: str = "'self'"
    csp_font_src: str = "'self'"
    csp_object_src: str = "'none'"
    csp_media_src: str = "'self'"
    csp_frame_src: str = "'none'"
    
    # Security monitoring
    security_monitoring_enabled: bool = True
    alert_webhook_enabled: bool = False
    correlation_tracking: bool = True
    
    # Certificate management
    cert_auto_renewal: bool = True
    cert_renewal_days_before: int = 30
    cert_validation_strict: bool = True
    
    def __post_init__(self):
        if self.allowed_cipher_suites is None:
            self.allowed_cipher_suites = [
                "ECDHE+AESGCM",
                "ECDHE+CHACHA20",
                "DHE+AESGCM",
                "DHE+CHACHA20",
                "!aNULL",
                "!MD5",
                "!DSS",
                "!RC4"
            ]


@dataclass
class LoggingConfiguration:
    """External logging system configuration"""
    backend: LoggingBackend = LoggingBackend.LOCAL
    enabled: bool = True
    
    # Common settings
    log_level: str = "INFO"
    structured_logging: bool = True
    include_request_id: bool = True
    include_user_id: bool = True
    include_client_ip: bool = True
    
    # ELK Stack configuration
    elasticsearch_host: Optional[str] = None
    elasticsearch_port: int = 9200
    elasticsearch_index: str = "yatinveda-security"
    elasticsearch_ssl: bool = True
    
    # Splunk configuration
    splunk_host: Optional[str] = None
    splunk_port: int = 8088
    splunk_token: Optional[str] = None
    splunk_index: str = "yatinveda"
    splunk_ssl: bool = True
    
    # CloudWatch configuration
    cloudwatch_region: str = "us-east-1"
    cloudwatch_log_group: str = "/aws/yatinveda/security"
    cloudwatch_log_stream: str = "security-events"
    
    # DataDog configuration
    datadog_api_key: Optional[str] = None
    datadog_app_key: Optional[str] = None
    datadog_site: str = "datadoghq.com"
    datadog_service: str = "yatinveda"


class ProductionSecurityConfig:
    """
    Production security configuration manager
    
    Manages environment-specific security policies and external logging integration.
    """
    
    def __init__(self, environment: SecurityEnvironment = None):
        self.environment = environment or self._detect_environment()
        self.policy = self._load_security_policy()
        self.logging_config = self._load_logging_configuration()
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info(f"Production security config initialized for {self.environment.value}")
    
    def _detect_environment(self) -> SecurityEnvironment:
        """Detect current environment from environment variables"""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        
        try:
            return SecurityEnvironment(env_name)
        except ValueError:
            logger.warning(f"Unknown environment '{env_name}', defaulting to development")
            return SecurityEnvironment.DEVELOPMENT
    
    def _load_security_policy(self) -> SecurityPolicy:
        """Load security policy based on environment"""
        
        if self.environment == SecurityEnvironment.PRODUCTION:
            return self._get_production_policy()
        elif self.environment == SecurityEnvironment.STAGING:
            return self._get_staging_policy()
        else:
            return self._get_development_policy()
    
    def _get_production_policy(self) -> SecurityPolicy:
        """Get strict production security policy"""
        return SecurityPolicy(
            # Strict HTTPS enforcement
            enforce_https=True,
            hsts_max_age=31536000,  # 1 year
            hsts_include_subdomains=True,
            hsts_preload=True,
            
            # Strict TLS configuration
            tls_min_version="1.2",
            tls_prefer_version="1.3",
            
            # Strict cookie security
            cookie_secure=True,
            cookie_httponly=True,
            cookie_samesite="strict",
            
            # Enhanced CSRF protection
            csrf_enabled=True,
            csrf_token_lifetime=int(os.getenv("CSRF_TOKEN_LIFETIME", "3600")),
            csrf_double_submit=True,
            
            # Conservative rate limiting
            rate_limiting_enabled=True,
            anonymous_rate_limit=os.getenv("PROD_ANONYMOUS_RATE_LIMIT", "50/minute"),
            authenticated_rate_limit=os.getenv("PROD_AUTHENTICATED_RATE_LIMIT", "500/minute"),
            login_rate_limit=os.getenv("PROD_LOGIN_RATE_LIMIT", "3/hour"),
            
            # Strict security headers
            x_frame_options="DENY",
            x_content_type_options="nosniff",
            referrer_policy="strict-origin-when-cross-origin",
            permissions_policy="geolocation=(), microphone=(), camera=(), payment=(), usb=()",
            
            # Strict CSP
            csp_default_src="'self'",
            csp_script_src="'self'",
            csp_style_src="'self'",
            csp_img_src="'self' data:",
            csp_connect_src="'self'",
            csp_font_src="'self'",
            csp_object_src="'none'",
            csp_media_src="'self'",
            csp_frame_src="'none'",
            
            # Enhanced monitoring
            security_monitoring_enabled=True,
            alert_webhook_enabled=bool(os.getenv("SECURITY_ALERT_WEBHOOK")),
            correlation_tracking=True,
            
            # Strict certificate management
            cert_auto_renewal=True,
            cert_renewal_days_before=30,
            cert_validation_strict=True
        )
    
    def _get_staging_policy(self) -> SecurityPolicy:
        """Get staging security policy (production-like but with some relaxations)"""
        policy = self._get_production_policy()
        
        # Slightly relaxed for testing
        policy.anonymous_rate_limit = os.getenv("STAGING_ANONYMOUS_RATE_LIMIT", "100/minute")
        policy.authenticated_rate_limit = os.getenv("STAGING_AUTHENTICATED_RATE_LIMIT", "1000/minute")
        policy.login_rate_limit = os.getenv("STAGING_LOGIN_RATE_LIMIT", "5/hour")
        
        # CSRF token lifetime can be configured
        policy.csrf_token_lifetime = int(os.getenv("CSRF_TOKEN_LIFETIME", "3600"))
        
        # Allow some testing flexibility in CSP
        policy.csp_script_src = "'self' 'unsafe-eval'"  # For testing tools
        policy.csp_style_src = "'self' 'unsafe-inline'"  # For testing tools
        
        return policy
    
    def _get_development_policy(self) -> SecurityPolicy:
        """Get development security policy (relaxed for development)"""
        return SecurityPolicy(
            # Relaxed HTTPS (can be disabled locally)
            enforce_https=os.getenv("DEV_ENFORCE_HTTPS", "false").lower() == "true",
            hsts_max_age=300,  # 5 minutes
            hsts_include_subdomains=False,
            hsts_preload=False,
            
            # Relaxed TLS
            tls_min_version="1.2",
            tls_prefer_version="1.3",
            
            # Relaxed cookie security
            cookie_secure=False,  # Allow HTTP cookies in development
            cookie_httponly=True,
            cookie_samesite="lax",
            
            # Optional CSRF protection
            csrf_enabled=os.getenv("DEV_CSRF_ENABLED", "true").lower() == "true",
            csrf_token_lifetime=int(os.getenv("CSRF_TOKEN_LIFETIME", "7200")),  # 2 hours
            csrf_double_submit=False,
            
            # Relaxed rate limiting
            rate_limiting_enabled=os.getenv("DEV_RATE_LIMITING", "false").lower() == "true",
            anonymous_rate_limit="1000/minute",
            authenticated_rate_limit="10000/minute",
            login_rate_limit="50/hour",
            
            # Relaxed security headers
            x_frame_options="SAMEORIGIN",
            x_content_type_options="nosniff",
            referrer_policy="strict-origin-when-cross-origin",
            permissions_policy="",
            
            # Relaxed CSP for development tools
            csp_default_src="'self'",
            csp_script_src="'self' 'unsafe-eval' 'unsafe-inline'",
            csp_style_src="'self' 'unsafe-inline'",
            csp_img_src="'self' data: blob:",
            csp_connect_src="'self' ws: wss:",
            csp_font_src="'self' data:",
            csp_object_src="'self'",
            csp_media_src="'self'",
            csp_frame_src="'self'",
            
            # Optional monitoring
            security_monitoring_enabled=os.getenv("DEV_SECURITY_MONITORING", "true").lower() == "true",
            alert_webhook_enabled=False,
            correlation_tracking=True,
            
            # Relaxed certificate management
            cert_auto_renewal=False,
            cert_renewal_days_before=7,
            cert_validation_strict=False
        )
    
    def _load_logging_configuration(self) -> LoggingConfiguration:
        """Load external logging configuration"""
        backend_name = os.getenv("LOGGING_BACKEND", "local").lower()
        
        try:
            backend = LoggingBackend(backend_name)
        except ValueError:
            logger.warning(f"Unknown logging backend '{backend_name}', using local")
            backend = LoggingBackend.LOCAL
        
        config = LoggingConfiguration(
            backend=backend,
            enabled=os.getenv("EXTERNAL_LOGGING_ENABLED", "true").lower() == "true",
            log_level=os.getenv("SECURITY_LOG_LEVEL", "INFO"),
            structured_logging=os.getenv("STRUCTURED_LOGGING", "true").lower() == "true",
            include_request_id=True,
            include_user_id=True,
            include_client_ip=True
        )
        
        # Load backend-specific configuration
        if backend == LoggingBackend.ELK:
            config.elasticsearch_host = os.getenv("ELASTICSEARCH_HOST")
            config.elasticsearch_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
            config.elasticsearch_index = os.getenv("ELASTICSEARCH_INDEX", "yatinveda-security")
            config.elasticsearch_ssl = os.getenv("ELASTICSEARCH_SSL", "true").lower() == "true"
            
        elif backend == LoggingBackend.SPLUNK:
            config.splunk_host = os.getenv("SPLUNK_HOST")
            config.splunk_port = int(os.getenv("SPLUNK_PORT", "8088"))
            config.splunk_token = os.getenv("SPLUNK_TOKEN")
            config.splunk_index = os.getenv("SPLUNK_INDEX", "yatinveda")
            config.splunk_ssl = os.getenv("SPLUNK_SSL", "true").lower() == "true"
            
        elif backend == LoggingBackend.CLOUDWATCH:
            config.cloudwatch_region = os.getenv("AWS_REGION", "us-east-1")
            config.cloudwatch_log_group = os.getenv("CLOUDWATCH_LOG_GROUP", "/aws/yatinveda/security")
            config.cloudwatch_log_stream = os.getenv("CLOUDWATCH_LOG_STREAM", "security-events")
            
        elif backend == LoggingBackend.DATADOG:
            config.datadog_api_key = os.getenv("DATADOG_API_KEY")
            config.datadog_app_key = os.getenv("DATADOG_APP_KEY")
            config.datadog_site = os.getenv("DATADOG_SITE", "datadoghq.com")
            config.datadog_service = os.getenv("DATADOG_SERVICE", "yatinveda")
        
        return config
    
    def _validate_configuration(self) -> None:
        """Validate security configuration and fail fast on errors"""
        errors = []
        
        # Production environment validations
        if self.environment == SecurityEnvironment.PRODUCTION:
            if not self.policy.enforce_https:
                errors.append("HTTPS enforcement is required in production")
            
            if not self.policy.csrf_enabled:
                errors.append("CSRF protection is required in production")
            
            if not self.policy.rate_limiting_enabled:
                errors.append("Rate limiting is required in production")
            
            if not self.policy.security_monitoring_enabled:
                errors.append("Security monitoring is required in production")
            
            if self.policy.cookie_samesite != "strict":
                errors.append("Strict SameSite cookies are required in production")
            
            if not self.policy.cookie_secure:
                errors.append("Secure cookies are required in production")
            
            # Validate TLS configuration
            if self.policy.tls_min_version not in ["1.2", "1.3"]:
                errors.append("TLS 1.2 or higher is required in production")
        
        # External logging validations
        if self.logging_config.enabled and self.logging_config.backend != LoggingBackend.LOCAL:
            if self.logging_config.backend == LoggingBackend.ELK:
                if not self.logging_config.elasticsearch_host:
                    errors.append("Elasticsearch host is required for ELK logging")
                    
            elif self.logging_config.backend == LoggingBackend.SPLUNK:
                if not self.logging_config.splunk_host or not self.logging_config.splunk_token:
                    errors.append("Splunk host and token are required for Splunk logging")
                    
            elif self.logging_config.backend == LoggingBackend.DATADOG:
                if not self.logging_config.datadog_api_key:
                    errors.append("DataDog API key is required for DataDog logging")
        
        # Certificate validation
        if self.policy.cert_validation_strict:
            try:
                # Test SSL context creation
                context = ssl.create_default_context(cafile=certifi.where())
                context.minimum_version = getattr(ssl.TLSVersion, f"TLSv{self.policy.tls_min_version.replace('.', '_')}")
                if hasattr(ssl.TLSVersion, f"TLSv{self.policy.tls_prefer_version.replace('.', '_')}"):
                    context.maximum_version = getattr(ssl.TLSVersion, f"TLSv{self.policy.tls_prefer_version.replace('.', '_')}")
            except Exception as e:
                errors.append(f"Invalid TLS configuration: {str(e)}")
        
        # Fail fast on configuration errors
        if errors:
            error_message = "Security configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_message)
            
            if self.environment == SecurityEnvironment.PRODUCTION:
                raise RuntimeError(error_message)
            else:
                logger.warning("Continuing with invalid configuration in non-production environment")
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers based on current policy"""
        headers = {}
        
        if self.policy.enforce_https:
            hsts_value = f"max-age={self.policy.hsts_max_age}"
            if self.policy.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.policy.hsts_preload:
                hsts_value += "; preload"
            headers["Strict-Transport-Security"] = hsts_value
        
        headers["X-Frame-Options"] = self.policy.x_frame_options
        headers["X-Content-Type-Options"] = self.policy.x_content_type_options
        headers["Referrer-Policy"] = self.policy.referrer_policy
        
        if self.policy.permissions_policy:
            headers["Permissions-Policy"] = self.policy.permissions_policy
        
        # Build CSP header
        csp_directives = [
            f"default-src {self.policy.csp_default_src}",
            f"script-src {self.policy.csp_script_src}",
            f"style-src {self.policy.csp_style_src}",
            f"img-src {self.policy.csp_img_src}",
            f"connect-src {self.policy.csp_connect_src}",
            f"font-src {self.policy.csp_font_src}",
            f"object-src {self.policy.csp_object_src}",
            f"media-src {self.policy.csp_media_src}",
            f"frame-src {self.policy.csp_frame_src}"
        ]
        headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        return headers
    
    def get_cookie_settings(self) -> Dict[str, Any]:
        """Get cookie security settings"""
        return {
            "secure": self.policy.cookie_secure,
            "httponly": self.policy.cookie_httponly,
            "samesite": self.policy.cookie_samesite
        }
    
    def get_rate_limit_settings(self) -> Dict[str, str]:
        """Get rate limiting settings"""
        return {
            "anonymous_limit": self.policy.anonymous_rate_limit,
            "authenticated_limit": self.policy.authenticated_rate_limit,
            "login_limit": self.policy.login_rate_limit,
            "enabled": str(self.policy.rate_limiting_enabled).lower()
        }
    
    def get_csrf_settings(self) -> Dict[str, Any]:
        """Get CSRF protection settings"""
        return {
            "enabled": self.policy.csrf_enabled,
            "token_lifetime": self.policy.csrf_token_lifetime,
            "double_submit": self.policy.csrf_double_submit
        }
    
    def get_tls_settings(self) -> Dict[str, Any]:
        """Get TLS configuration settings"""
        return {
            "min_version": self.policy.tls_min_version,
            "prefer_version": self.policy.tls_prefer_version,
            "cipher_suites": ":".join(self.policy.allowed_cipher_suites)
        }
    
    def get_monitoring_settings(self) -> Dict[str, Any]:
        """Get security monitoring settings"""
        return {
            "enabled": self.policy.security_monitoring_enabled,
            "alert_webhook_enabled": self.policy.alert_webhook_enabled,
            "correlation_tracking": self.policy.correlation_tracking
        }
    
    def get_certificate_settings(self) -> Dict[str, Any]:
        """Get certificate management settings"""
        return {
            "auto_renewal": self.policy.cert_auto_renewal,
            "renewal_days_before": self.policy.cert_renewal_days_before,
            "validation_strict": self.policy.cert_validation_strict
        }
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export complete configuration for debugging/documentation"""
        return {
            "environment": self.environment.value,
            "policy": asdict(self.policy),
            "logging": asdict(self.logging_config),
            "validation_timestamp": datetime.utcnow().isoformat()
        }
    
    def validate_external_logging(self) -> bool:
        """Test external logging connectivity"""
        if not self.logging_config.enabled or self.logging_config.backend == LoggingBackend.LOCAL:
            return True
        
        try:
            if self.logging_config.backend == LoggingBackend.ELK:
                return self._test_elasticsearch_connection()
            elif self.logging_config.backend == LoggingBackend.SPLUNK:
                return self._test_splunk_connection()
            elif self.logging_config.backend == LoggingBackend.CLOUDWATCH:
                return self._test_cloudwatch_connection()
            elif self.logging_config.backend == LoggingBackend.DATADOG:
                return self._test_datadog_connection()
        except Exception as e:
            logger.error(f"External logging validation failed: {str(e)}")
            return False
        
        return False
    
    def _test_elasticsearch_connection(self) -> bool:
        """Test Elasticsearch connectivity"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.logging_config.elasticsearch_host, self.logging_config.elasticsearch_port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _test_splunk_connection(self) -> bool:
        """Test Splunk connectivity"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.logging_config.splunk_host, self.logging_config.splunk_port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _test_cloudwatch_connection(self) -> bool:
        """Test CloudWatch connectivity (basic AWS connectivity)"""
        try:
            # Test basic AWS connectivity
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            # Test connection to AWS CloudWatch endpoint
            result = sock.connect_ex((f"logs.{self.logging_config.cloudwatch_region}.amazonaws.com", 443))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _test_datadog_connection(self) -> bool:
        """Test DataDog connectivity"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((f"api.{self.logging_config.datadog_site}", 443))
            sock.close()
            return result == 0
        except Exception:
            return False


# Global configuration instance
_production_security_config: Optional[ProductionSecurityConfig] = None


def get_production_security_config() -> ProductionSecurityConfig:
    """Get the global production security configuration instance"""
    global _production_security_config
    if _production_security_config is None:
        _production_security_config = ProductionSecurityConfig()
    return _production_security_config


def initialize_production_security_config(environment: SecurityEnvironment = None) -> ProductionSecurityConfig:
    """Initialize the global production security configuration"""
    global _production_security_config
    _production_security_config = ProductionSecurityConfig(environment)
    return _production_security_config


def validate_production_security() -> Dict[str, Any]:
    """Validate production security configuration and return status"""
    config = get_production_security_config()
    
    validation_results = {
        "environment": config.environment.value,
        "timestamp": datetime.utcnow().isoformat(),
        "policy_validation": "passed",
        "external_logging_validation": "not_tested",
        "tls_validation": "passed",
        "errors": [],
        "warnings": []
    }
    
    try:
        # Test external logging if enabled
        if config.logging_config.enabled and config.logging_config.backend != LoggingBackend.LOCAL:
            logging_valid = config.validate_external_logging()
            validation_results["external_logging_validation"] = "passed" if logging_valid else "failed"
            
            if not logging_valid:
                validation_results["errors"].append("External logging connectivity test failed")
        else:
            validation_results["external_logging_validation"] = "disabled"
        
        # Validate TLS settings
        try:
            tls_settings = config.get_tls_settings()
            context = ssl.create_default_context()
            # Basic TLS validation passed during config initialization
        except Exception as e:
            validation_results["tls_validation"] = "failed"
            validation_results["errors"].append(f"TLS validation failed: {str(e)}")
        
        # Environment-specific warnings
        if config.environment == SecurityEnvironment.DEVELOPMENT:
            if not config.policy.enforce_https:
                validation_results["warnings"].append("HTTPS enforcement is disabled in development")
            if not config.policy.rate_limiting_enabled:
                validation_results["warnings"].append("Rate limiting is disabled in development")
        
        # Overall status
        if validation_results["errors"]:
            validation_results["overall_status"] = "failed"
        elif validation_results["warnings"]:
            validation_results["overall_status"] = "warning"
        else:
            validation_results["overall_status"] = "passed"
            
    except Exception as e:
        validation_results["policy_validation"] = "failed"
        validation_results["overall_status"] = "failed"
        validation_results["errors"].append(f"Configuration validation error: {str(e)}")
    
    return validation_results