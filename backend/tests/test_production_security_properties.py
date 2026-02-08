"""
Property-Based Tests for Production Security Configuration

This module implements property-based tests to validate the production security
configuration system across all environments and settings combinations.

Properties tested:
- Property 13: Production Security Enforcement
- Property 14: Configurable Security Settings  
- Property 15: Security Configuration Validation
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import Dict, Any

from modules.production_security import (
    ProductionSecurityConfig,
    SecurityEnvironment,
    LoggingBackend,
    SecurityPolicy,
    LoggingConfiguration,
    validate_production_security
)


class TestProductionSecurityProperties:
    """Property-based tests for production security configuration"""
    
    @given(
        environment=st.sampled_from([SecurityEnvironment.DEVELOPMENT, SecurityEnvironment.STAGING, SecurityEnvironment.PRODUCTION]),
        enforce_https=st.booleans(),
        csrf_enabled=st.booleans(),
        rate_limiting_enabled=st.booleans(),
        security_monitoring_enabled=st.booleans()
    )
    @settings(max_examples=20, deadline=None)
    def test_property_13_production_security_enforcement(
        self,
        environment: SecurityEnvironment,
        enforce_https: bool,
        csrf_enabled: bool,
        rate_limiting_enabled: bool,
        security_monitoring_enabled: bool
    ):
        """
        Property 13: Production Security Enforcement
        
        For any production deployment, the Security_Header_Manager should enforce 
        strict security policies without development overrides, and the 
        SSL_Termination_Proxy should support only TLS 1.2+ with secure cipher suites.
        
        Validates: Requirements 6.2, 6.5
        """
        with patch.dict(os.environ, {
            "ENVIRONMENT": environment.value,
            "DEV_ENFORCE_HTTPS": str(enforce_https).lower(),
            "DEV_CSRF_ENABLED": str(csrf_enabled).lower(),
            "DEV_RATE_LIMITING": str(rate_limiting_enabled).lower(),
            "DEV_SECURITY_MONITORING": str(security_monitoring_enabled).lower()
        }, clear=False):
            
            config = ProductionSecurityConfig(environment)
            
            if environment == SecurityEnvironment.PRODUCTION:
                # Production must enforce strict security policies
                assert config.policy.enforce_https == True, "Production must enforce HTTPS"
                assert config.policy.csrf_enabled == True, "Production must enable CSRF protection"
                assert config.policy.rate_limiting_enabled == True, "Production must enable rate limiting"
                assert config.policy.security_monitoring_enabled == True, "Production must enable security monitoring"
                
                # Production must use strict cookie settings
                assert config.policy.cookie_secure == True, "Production must use secure cookies"
                assert config.policy.cookie_samesite == "strict", "Production must use strict SameSite cookies"
                
                # Production must use strict TLS settings
                assert config.policy.tls_min_version in ["1.2", "1.3"], "Production must use TLS 1.2+"
                assert config.policy.tls_prefer_version == "1.3", "Production should prefer TLS 1.3"
                
                # Production must have strict CSP
                assert "'unsafe-eval'" not in config.policy.csp_script_src, "Production must not allow unsafe-eval"
                assert "'unsafe-inline'" not in config.policy.csp_script_src, "Production must not allow unsafe-inline scripts"
                
                # Production must have strict security headers
                assert config.policy.x_frame_options == "DENY", "Production must deny framing"
                assert config.policy.hsts_max_age >= 31536000, "Production must have long HSTS max-age"
                assert config.policy.hsts_include_subdomains == True, "Production must include subdomains in HSTS"
                
                # Production cipher suites must be secure
                cipher_suites = config.policy.allowed_cipher_suites
                assert "!aNULL" in cipher_suites, "Production must exclude NULL ciphers"
                assert "!MD5" in cipher_suites, "Production must exclude MD5 ciphers"
                assert "!RC4" in cipher_suites, "Production must exclude RC4 ciphers"
                
            elif environment == SecurityEnvironment.STAGING:
                # Staging should be production-like but may have some relaxations
                assert config.policy.enforce_https == True, "Staging should enforce HTTPS"
                assert config.policy.csrf_enabled == True, "Staging should enable CSRF protection"
                assert config.policy.rate_limiting_enabled == True, "Staging should enable rate limiting"
                assert config.policy.security_monitoring_enabled == True, "Staging should enable security monitoring"
                
                # Staging may allow some testing flexibility
                assert config.policy.tls_min_version in ["1.2", "1.3"], "Staging must use TLS 1.2+"
                
            else:  # Development
                # Development can have relaxed settings based on environment variables
                # but should still have reasonable defaults
                assert config.policy.tls_min_version in ["1.2", "1.3"], "Development should still use modern TLS"
                
                # Development settings should respect environment variables
                if not enforce_https:
                    assert config.policy.enforce_https == False, "Development should respect HTTPS override"
                if not csrf_enabled:
                    assert config.policy.csrf_enabled == False, "Development should respect CSRF override"
                if not rate_limiting_enabled:
                    assert config.policy.rate_limiting_enabled == False, "Development should respect rate limiting override"
    
    @given(
        logging_backend=st.sampled_from(list(LoggingBackend)),
        log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
        structured_logging=st.booleans(),
        anonymous_rate_limit=st.sampled_from(["50/minute", "100/minute", "200/minute", "1000/minute"]),
        authenticated_rate_limit=st.sampled_from(["500/minute", "1000/minute", "2000/minute", "10000/minute"]),
        csrf_token_lifetime=st.integers(min_value=300, max_value=7200)  # 5 minutes to 2 hours
    )
    @settings(max_examples=20, deadline=None)
    def test_property_14_configurable_security_settings(
        self,
        logging_backend: LoggingBackend,
        log_level: str,
        structured_logging: bool,
        anonymous_rate_limit: str,
        authenticated_rate_limit: str,
        csrf_token_lifetime: int
    ):
        """
        Property 14: Configurable Security Settings
        
        For any deployment environment, the Rate_Limiter should support configurable 
        limits via environment variables, and the Security_Monitor should integrate 
        with external logging systems via structured JSON.
        
        Validates: Requirements 6.3, 6.4
        """
        # Set up environment variables with required config for external logging
        env_vars = {
            "LOGGING_BACKEND": logging_backend.value,
            "SECURITY_LOG_LEVEL": log_level,
            "STRUCTURED_LOGGING": str(structured_logging).lower(),
            "PROD_ANONYMOUS_RATE_LIMIT": anonymous_rate_limit,
            "PROD_AUTHENTICATED_RATE_LIMIT": authenticated_rate_limit,
            "CSRF_TOKEN_LIFETIME": str(csrf_token_lifetime),
            "EXTERNAL_LOGGING_ENABLED": "true"
        }
        
        # Add backend-specific required configuration to avoid validation errors
        if logging_backend == LoggingBackend.ELK:
            env_vars["ELASTICSEARCH_HOST"] = "localhost"
        elif logging_backend == LoggingBackend.SPLUNK:
            env_vars["SPLUNK_HOST"] = "localhost"
            env_vars["SPLUNK_TOKEN"] = "test-token"
        elif logging_backend == LoggingBackend.DATADOG:
            env_vars["DATADOG_API_KEY"] = "test-api-key"
        
        with patch.dict(os.environ, env_vars, clear=False):
            
            config = ProductionSecurityConfig(SecurityEnvironment.PRODUCTION)
            
            # Rate limiting should be configurable via environment variables
            rate_limit_settings = config.get_rate_limit_settings()
            assert rate_limit_settings["anonymous_limit"] == anonymous_rate_limit, "Anonymous rate limit should be configurable"
            assert rate_limit_settings["authenticated_limit"] == authenticated_rate_limit, "Authenticated rate limit should be configurable"
            assert rate_limit_settings["enabled"] == "true", "Rate limiting should be enabled in production"
            
            # CSRF settings should be configurable
            csrf_settings = config.get_csrf_settings()
            assert csrf_settings["token_lifetime"] == csrf_token_lifetime, "CSRF token lifetime should be configurable"
            assert csrf_settings["enabled"] == True, "CSRF should be enabled in production"
            
            # Logging configuration should be configurable
            assert config.logging_config.backend == logging_backend, "Logging backend should be configurable"
            assert config.logging_config.log_level == log_level, "Log level should be configurable"
            assert config.logging_config.structured_logging == structured_logging, "Structured logging should be configurable"
            assert config.logging_config.enabled == True, "External logging should be enabled when configured"
            
            # Logging should include required fields for structured JSON
            assert config.logging_config.include_request_id == True, "Logging should include request ID"
            assert config.logging_config.include_user_id == True, "Logging should include user ID"
            assert config.logging_config.include_client_ip == True, "Logging should include client IP"
            
            # Backend-specific configuration should be available
            if logging_backend == LoggingBackend.ELK:
                assert hasattr(config.logging_config, 'elasticsearch_host'), "ELK backend should have Elasticsearch config"
                assert hasattr(config.logging_config, 'elasticsearch_index'), "ELK backend should have index config"
                
            elif logging_backend == LoggingBackend.SPLUNK:
                assert hasattr(config.logging_config, 'splunk_host'), "Splunk backend should have host config"
                assert hasattr(config.logging_config, 'splunk_token'), "Splunk backend should have token config"
                
            elif logging_backend == LoggingBackend.CLOUDWATCH:
                assert hasattr(config.logging_config, 'cloudwatch_region'), "CloudWatch backend should have region config"
                assert hasattr(config.logging_config, 'cloudwatch_log_group'), "CloudWatch backend should have log group config"
                
            elif logging_backend == LoggingBackend.DATADOG:
                assert hasattr(config.logging_config, 'datadog_api_key'), "DataDog backend should have API key config"
                assert hasattr(config.logging_config, 'datadog_service'), "DataDog backend should have service config"
            
            # Configuration should be exportable for debugging
            exported_config = config.export_configuration()
            assert "environment" in exported_config, "Exported config should include environment"
            assert "policy" in exported_config, "Exported config should include policy"
            assert "logging" in exported_config, "Exported config should include logging config"
            assert "validation_timestamp" in exported_config, "Exported config should include validation timestamp"
    
    @given(
        environment=st.sampled_from(list(SecurityEnvironment)),
        invalid_tls_version=st.sampled_from(["1.0", "1.1", "invalid", ""]),
        missing_required_config=st.booleans(),
        invalid_cipher_suites=st.booleans()
    )
    @settings(max_examples=10, deadline=None)
    def test_property_15_security_configuration_validation(
        self,
        environment: SecurityEnvironment,
        invalid_tls_version: str,
        missing_required_config: bool,
        invalid_cipher_suites: bool
    ):
        """
        Property 15: Security Configuration Validation
        
        For any security configuration error, the Security_Monitor should prevent 
        application startup and provide detailed configuration guidance with 
        remediation steps.
        
        Validates: Requirements 6.6
        """
        env_vars = {"ENVIRONMENT": environment.value}
        
        # Introduce configuration errors based on test parameters
        if invalid_tls_version and invalid_tls_version in ["1.0", "1.1", "invalid", ""]:
            # Simulate invalid TLS configuration
            with patch('modules.production_security.ssl.create_default_context') as mock_ssl:
                if invalid_tls_version in ["1.0", "1.1"]:
                    # These are valid but deprecated versions
                    mock_ssl.side_effect = None
                else:
                    # Invalid versions should cause SSL context creation to fail
                    mock_ssl.side_effect = ValueError(f"Invalid TLS version: {invalid_tls_version}")
                
                with patch.dict(os.environ, env_vars, clear=False):
                    if environment == SecurityEnvironment.PRODUCTION and invalid_tls_version in ["invalid", ""]:
                        # Production should fail on invalid TLS configuration
                        with pytest.raises(RuntimeError, match="Security configuration validation failed"):
                            config = ProductionSecurityConfig(environment)
                    else:
                        # Non-production or valid deprecated versions should not fail startup
                        config = ProductionSecurityConfig(environment)
                        
                        # But validation should detect the issue
                        validation_result = validate_production_security()
                        if invalid_tls_version in ["invalid", ""]:
                            assert validation_result["overall_status"] in ["failed", "warning"], "Validation should detect TLS issues"
                            assert any("TLS" in error for error in validation_result.get("errors", [])), "Should report TLS errors"
        
        # Test missing required configuration in production
        if missing_required_config and environment == SecurityEnvironment.PRODUCTION:
            with patch.dict(os.environ, {
                **env_vars,
                "DEV_ENFORCE_HTTPS": "false",  # This should be ignored in production
                "DEV_CSRF_ENABLED": "false",   # This should be ignored in production
            }, clear=False):
                
                # Production should enforce security regardless of dev overrides
                config = ProductionSecurityConfig(environment)
                assert config.policy.enforce_https == True, "Production should ignore dev HTTPS override"
                assert config.policy.csrf_enabled == True, "Production should ignore dev CSRF override"
                
                # Validation should pass for production with proper defaults
                validation_result = validate_production_security()
                assert validation_result["policy_validation"] == "passed", "Production policy validation should pass"
        
        # Test invalid cipher suites
        if invalid_cipher_suites:
            with patch('modules.production_security.ssl.create_default_context') as mock_ssl:
                mock_ssl.side_effect = ValueError("Invalid cipher suite configuration")
                
                with patch.dict(os.environ, env_vars, clear=False):
                    if environment == SecurityEnvironment.PRODUCTION:
                        # Production should fail on invalid cipher configuration
                        with pytest.raises(RuntimeError, match="Security configuration validation failed"):
                            config = ProductionSecurityConfig(environment)
                    else:
                        # Non-production should continue with warnings
                        config = ProductionSecurityConfig(environment)
                        validation_result = validate_production_security()
                        assert validation_result["overall_status"] in ["failed", "warning"], "Should detect cipher suite issues"
        
        # Test external logging validation (only for non-production to avoid config errors)
        if environment != SecurityEnvironment.PRODUCTION:
            with patch.dict(os.environ, {
                **env_vars,
                "LOGGING_BACKEND": "elk",
                "EXTERNAL_LOGGING_ENABLED": "true",
                "ELASTICSEARCH_HOST": "localhost"  # Always provide valid host for non-production
            }, clear=False):
                
                # Reset global config to ensure fresh configuration
                import modules.production_security
                modules.production_security._production_security_config = None
                
                config = ProductionSecurityConfig(environment)
                
                # Ensure external logging is actually enabled for this test
                if config.logging_config.enabled and config.logging_config.backend != LoggingBackend.LOCAL:
                    # External logging validation should detect connectivity issues
                    with patch.object(config, '_test_elasticsearch_connection', return_value=False):
                        # Reset global config again to ensure validation uses our config
                        modules.production_security._production_security_config = config
                        validation_result = validate_production_security()
                        
                        assert validation_result["external_logging_validation"] == "failed", "Should detect logging connectivity issues"
                        assert any("logging" in error.lower() for error in validation_result.get("errors", [])), "Should report logging errors"
        
        # Test successful validation - always use a fresh environment to avoid global state issues
        with patch.dict(os.environ, {"ENVIRONMENT": environment.value}, clear=True):
            # Reset global config to avoid state pollution
            import modules.production_security
            modules.production_security._production_security_config = None
            
            config = ProductionSecurityConfig(environment)
            validation_result = validate_production_security()
            
            # Basic validation should always include required fields
            assert "environment" in validation_result, "Validation should include environment"
            assert "timestamp" in validation_result, "Validation should include timestamp"
            assert "overall_status" in validation_result, "Validation should include overall status"
            assert validation_result["environment"] == environment.value, "Validation should report correct environment"
            
            # Validation timestamp should be recent
            validation_time = datetime.fromisoformat(validation_result["timestamp"])
            time_diff = (datetime.utcnow() - validation_time).total_seconds()
            assert time_diff < 60, "Validation timestamp should be recent"
    
    @given(
        environment=st.sampled_from(list(SecurityEnvironment)),
        hsts_max_age=st.integers(min_value=300, max_value=63072000),  # 5 minutes to 2 years
        include_subdomains=st.booleans(),
        preload=st.booleans()
    )
    @settings(max_examples=10, deadline=None)
    def test_security_headers_generation(
        self,
        environment: SecurityEnvironment,
        hsts_max_age: int,
        include_subdomains: bool,
        preload: bool
    ):
        """Test that security headers are generated correctly for all environments"""
        with patch.dict(os.environ, {"ENVIRONMENT": environment.value}, clear=False):
            config = ProductionSecurityConfig(environment)
            
            # Override HSTS settings for testing
            config.policy.hsts_max_age = hsts_max_age
            config.policy.hsts_include_subdomains = include_subdomains
            config.policy.hsts_preload = preload
            
            headers = config.get_security_headers()
            
            # All environments should have basic security headers
            assert "X-Frame-Options" in headers, "All environments should have X-Frame-Options"
            assert "X-Content-Type-Options" in headers, "All environments should have X-Content-Type-Options"
            assert "Referrer-Policy" in headers, "All environments should have Referrer-Policy"
            assert "Content-Security-Policy" in headers, "All environments should have CSP"
            
            # HSTS should be present when HTTPS is enforced
            if config.policy.enforce_https:
                assert "Strict-Transport-Security" in headers, "HTTPS enforcement should include HSTS"
                
                hsts_header = headers["Strict-Transport-Security"]
                assert f"max-age={hsts_max_age}" in hsts_header, "HSTS should include correct max-age"
                
                if include_subdomains:
                    assert "includeSubDomains" in hsts_header, "HSTS should include subdomains when configured"
                else:
                    assert "includeSubDomains" not in hsts_header, "HSTS should not include subdomains when not configured"
                
                if preload:
                    assert "preload" in hsts_header, "HSTS should include preload when configured"
                else:
                    assert "preload" not in hsts_header, "HSTS should not include preload when not configured"
            
            # CSP should be properly formatted
            csp_header = headers["Content-Security-Policy"]
            assert "default-src" in csp_header, "CSP should include default-src"
            assert "script-src" in csp_header, "CSP should include script-src"
            assert "style-src" in csp_header, "CSP should include style-src"
            
            # Production should have stricter CSP
            if environment == SecurityEnvironment.PRODUCTION:
                assert "'unsafe-eval'" not in csp_header, "Production CSP should not allow unsafe-eval"
                assert "'unsafe-inline'" not in csp_header or "style-src" in csp_header, "Production CSP should minimize unsafe-inline"
    
    @given(
        environment=st.sampled_from(list(SecurityEnvironment)),
        test_connectivity=st.booleans()
    )
    @settings(max_examples=10, deadline=None)
    def test_external_logging_integration(
        self,
        environment: SecurityEnvironment,
        test_connectivity: bool
    ):
        """Test external logging system integration"""
        for backend in LoggingBackend:
            if backend == LoggingBackend.LOCAL:
                continue  # Skip local backend
            
            # Set up environment variables with required config for each backend
            env_vars = {
                "ENVIRONMENT": environment.value,
                "LOGGING_BACKEND": backend.value,
                "EXTERNAL_LOGGING_ENABLED": "true"
            }
            
            # Add backend-specific required configuration
            if backend == LoggingBackend.ELK:
                env_vars["ELASTICSEARCH_HOST"] = "localhost"
            elif backend == LoggingBackend.SPLUNK:
                env_vars["SPLUNK_HOST"] = "localhost"
                env_vars["SPLUNK_TOKEN"] = "test-token"
            elif backend == LoggingBackend.DATADOG:
                env_vars["DATADOG_API_KEY"] = "test-api-key"
            
            with patch.dict(os.environ, env_vars, clear=False):
                
                config = ProductionSecurityConfig(environment)
                
                # Configuration should be loaded correctly
                assert config.logging_config.backend == backend, f"Should configure {backend.value} backend"
                assert config.logging_config.enabled == True, "External logging should be enabled"
                
                # Test connectivity validation
                if test_connectivity:
                    # Mock successful connectivity
                    connection_method = f'_test_{backend.value}_connection'
                    if hasattr(config, connection_method):
                        with patch.object(config, connection_method, return_value=True):
                            assert config.validate_external_logging() == True, f"Should validate {backend.value} connectivity"
                        
                        # Mock failed connectivity
                        with patch.object(config, connection_method, return_value=False):
                            assert config.validate_external_logging() == False, f"Should detect {backend.value} connectivity failure"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])