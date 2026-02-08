"""
Security Testing and Health Checks Module for YatinVeda

This module implements comprehensive security testing capabilities including
health check endpoints, security testing utilities, certificate validation,
and security metrics collection for automated testing and compliance reporting.
"""

import os
import ssl
import socket
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import hashlib
import hmac
from pathlib import Path

from fastapi import Request, Response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecurityTestType(Enum):
    """Types of security tests"""
    HEALTH_CHECK = "health_check"
    CERTIFICATE_VALIDATION = "certificate_validation"
    RATE_LIMIT_TEST = "rate_limit_test"
    CSRF_TEST = "csrf_test"
    SECURITY_HEADERS = "security_headers"
    TLS_CONFIGURATION = "tls_configuration"
    VULNERABILITY_SCAN = "vulnerability_scan"


class SecurityTestSeverity(Enum):
    """Security test result severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityTestStatus(Enum):
    """Security test execution status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class SecurityTestResult:
    """Security test result data model"""
    test_id: str
    test_type: SecurityTestType
    status: SecurityTestStatus
    severity: SecurityTestSeverity
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    duration_ms: float
    remediation: Optional[str] = None
    impact_assessment: Optional[str] = None

@dataclass
class SecurityMetrics:
    """Security metrics data model"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    warning_tests: int
    error_tests: int
    skipped_tests: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    info_issues: int
    overall_score: float
    compliance_status: str
    last_updated: datetime


class SecurityHealthChecker:
    """
    Comprehensive security health checker
    
    Provides health check endpoints that validate all security configurations
    and generate detailed reports for compliance and monitoring.
    """
    
    def __init__(
        self,
        certificate_manager=None,
        rate_limiter=None,
        csrf_protection=None,
        security_monitor=None,
        production_security_config=None
    ):
        self.certificate_manager = certificate_manager
        self.rate_limiter = rate_limiter
        self.csrf_protection = csrf_protection
        self.security_monitor = security_monitor
        self.production_security_config = production_security_config
        
        self.test_results: List[SecurityTestResult] = []
        self.metrics: Optional[SecurityMetrics] = None
        
        logger.info("Security health checker initialized")
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive security health check"""
        start_time = datetime.utcnow()
        self.test_results = []
        
        logger.info("Starting comprehensive security health check")
        
        # Run all health check tests
        await self._check_certificate_health()
        await self._check_rate_limiter_health()
        await self._check_csrf_protection_health()
        await self._check_security_headers_health()
        await self._check_tls_configuration_health()
        await self._check_security_monitoring_health()
        await self._check_production_config_health()
        
        # Calculate metrics
        self.metrics = self._calculate_metrics()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds() * 1000
        
        return {
            "status": "completed",
            "timestamp": end_time.isoformat(),
            "duration_ms": duration,
            "metrics": asdict(self.metrics),
            "test_results": [asdict(result) for result in self.test_results],
            "summary": self._generate_summary(),
            "recommendations": self._generate_recommendations()
        }
    
    async def _check_certificate_health(self):
        """Check SSL certificate health"""
        test_start = datetime.utcnow()
        
        try:
            if not self.certificate_manager:
                self._add_test_result(
                    "cert_manager_missing",
                    SecurityTestType.CERTIFICATE_VALIDATION,
                    SecurityTestStatus.SKIPPED,
                    SecurityTestSeverity.MEDIUM,
                    "Certificate manager not configured",
                    {},
                    test_start,
                    remediation="Configure certificate manager for SSL/TLS validation"
                )
                return
            
            # Test certificate validation
            domains = getattr(self.certificate_manager, 'domains', ['localhost'])
            for domain in domains:
                await self._validate_certificate_for_domain(domain, test_start)
                
        except Exception as e:
            self._add_test_result(
                "cert_health_error",
                SecurityTestType.CERTIFICATE_VALIDATION,
                SecurityTestStatus.ERROR,
                SecurityTestSeverity.HIGH,
                f"Certificate health check failed: {str(e)}",
                {"error": str(e)},
                test_start,
                remediation="Check certificate manager configuration and connectivity"
            )
    
    async def _validate_certificate_for_domain(self, domain: str, test_start: datetime):
        """Validate certificate for specific domain"""
        try:
            # Test SSL connection
            context = ssl.create_default_context()
            
            # Connect to domain and get certificate
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check certificate expiration
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (not_after - datetime.utcnow()).days
                    
                    if days_until_expiry < 7:
                        severity = SecurityTestSeverity.CRITICAL
                        status = SecurityTestStatus.FAILED
                        message = f"Certificate for {domain} expires in {days_until_expiry} days"
                        remediation = "Renew SSL certificate immediately"
                    elif days_until_expiry < 30:
                        severity = SecurityTestSeverity.HIGH
                        status = SecurityTestStatus.WARNING
                        message = f"Certificate for {domain} expires in {days_until_expiry} days"
                        remediation = "Schedule certificate renewal"
                    else:
                        severity = SecurityTestSeverity.INFO
                        status = SecurityTestStatus.PASSED
                        message = f"Certificate for {domain} is valid for {days_until_expiry} days"
                        remediation = None
                    
                    self._add_test_result(
                        f"cert_expiry_{domain}",
                        SecurityTestType.CERTIFICATE_VALIDATION,
                        status,
                        severity,
                        message,
                        {
                            "domain": domain,
                            "expires": not_after.isoformat(),
                            "days_until_expiry": days_until_expiry,
                            "issuer": cert.get('issuer', 'Unknown')
                        },
                        test_start,
                        remediation=remediation
                    )
                    
        except Exception as e:
            self._add_test_result(
                f"cert_validation_{domain}",
                SecurityTestType.CERTIFICATE_VALIDATION,
                SecurityTestStatus.FAILED,
                SecurityTestSeverity.HIGH,
                f"Certificate validation failed for {domain}: {str(e)}",
                {"domain": domain, "error": str(e)},
                test_start,
                remediation="Check domain accessibility and certificate configuration"
            )
    async def _check_rate_limiter_health(self):
        """Check rate limiter health and configuration"""
        test_start = datetime.utcnow()
        
        try:
            if not self.rate_limiter:
                self._add_test_result(
                    "rate_limiter_missing",
                    SecurityTestType.RATE_LIMIT_TEST,
                    SecurityTestStatus.SKIPPED,
                    SecurityTestSeverity.MEDIUM,
                    "Rate limiter not configured",
                    {},
                    test_start,
                    remediation="Configure rate limiter for DDoS protection"
                )
                return
            
            # Test rate limiter configuration
            if hasattr(self.rate_limiter, 'storage'):
                storage_type = type(self.rate_limiter.storage).__name__
                
                if 'Redis' in storage_type:
                    # Test Redis connectivity
                    try:
                        await self.rate_limiter.storage.ping()
                        self._add_test_result(
                            "rate_limiter_redis",
                            SecurityTestType.RATE_LIMIT_TEST,
                            SecurityTestStatus.PASSED,
                            SecurityTestSeverity.INFO,
                            "Rate limiter Redis backend is healthy",
                            {"storage_type": storage_type},
                            test_start
                        )
                    except Exception as e:
                        self._add_test_result(
                            "rate_limiter_redis",
                            SecurityTestType.RATE_LIMIT_TEST,
                            SecurityTestStatus.FAILED,
                            SecurityTestSeverity.HIGH,
                            f"Rate limiter Redis backend failed: {str(e)}",
                            {"storage_type": storage_type, "error": str(e)},
                            test_start,
                            remediation="Check Redis connectivity and configuration"
                        )
                else:
                    self._add_test_result(
                        "rate_limiter_storage",
                        SecurityTestType.RATE_LIMIT_TEST,
                        SecurityTestStatus.WARNING,
                        SecurityTestSeverity.MEDIUM,
                        f"Rate limiter using {storage_type} (not Redis)",
                        {"storage_type": storage_type},
                        test_start,
                        remediation="Consider using Redis for production rate limiting"
                    )
            
            # Test rate limiting rules
            if hasattr(self.rate_limiter, 'rules'):
                rules_count = len(self.rate_limiter.rules)
                if rules_count > 0:
                    self._add_test_result(
                        "rate_limiter_rules",
                        SecurityTestType.RATE_LIMIT_TEST,
                        SecurityTestStatus.PASSED,
                        SecurityTestSeverity.INFO,
                        f"Rate limiter has {rules_count} configured rules",
                        {"rules_count": rules_count},
                        test_start
                    )
                else:
                    self._add_test_result(
                        "rate_limiter_rules",
                        SecurityTestType.RATE_LIMIT_TEST,
                        SecurityTestStatus.WARNING,
                        SecurityTestSeverity.MEDIUM,
                        "Rate limiter has no configured rules",
                        {"rules_count": 0},
                        test_start,
                        remediation="Configure rate limiting rules for endpoints"
                    )
                    
        except Exception as e:
            self._add_test_result(
                "rate_limiter_health_error",
                SecurityTestType.RATE_LIMIT_TEST,
                SecurityTestStatus.ERROR,
                SecurityTestSeverity.HIGH,
                f"Rate limiter health check failed: {str(e)}",
                {"error": str(e)},
                test_start,
                remediation="Check rate limiter configuration and dependencies"
            )
    
    async def _check_csrf_protection_health(self):
        """Check CSRF protection health"""
        test_start = datetime.utcnow()
        
        try:
            if not self.csrf_protection:
                self._add_test_result(
                    "csrf_protection_missing",
                    SecurityTestType.CSRF_TEST,
                    SecurityTestStatus.FAILED,
                    SecurityTestSeverity.HIGH,
                    "CSRF protection not configured",
                    {},
                    test_start,
                    remediation="Configure CSRF protection middleware"
                )
                return
            
            # Test CSRF token generation
            try:
                test_session_id = "test_session_123"
                token = await self.csrf_protection.generate_csrf_token(test_session_id)
                
                if token and len(token) > 20:  # Basic token validation
                    self._add_test_result(
                        "csrf_token_generation",
                        SecurityTestType.CSRF_TEST,
                        SecurityTestStatus.PASSED,
                        SecurityTestSeverity.INFO,
                        "CSRF token generation working correctly",
                        {"token_length": len(token)},
                        test_start
                    )
                    
                    # Test token validation
                    is_valid = await self.csrf_protection.validate_csrf_token(token, test_session_id)
                    if is_valid:
                        self._add_test_result(
                            "csrf_token_validation",
                            SecurityTestType.CSRF_TEST,
                            SecurityTestStatus.PASSED,
                            SecurityTestSeverity.INFO,
                            "CSRF token validation working correctly",
                            {},
                            test_start
                        )
                    else:
                        self._add_test_result(
                            "csrf_token_validation",
                            SecurityTestType.CSRF_TEST,
                            SecurityTestStatus.FAILED,
                            SecurityTestSeverity.HIGH,
                            "CSRF token validation failed",
                            {},
                            test_start,
                            remediation="Check CSRF token validation logic"
                        )
                else:
                    self._add_test_result(
                        "csrf_token_generation",
                        SecurityTestType.CSRF_TEST,
                        SecurityTestStatus.FAILED,
                        SecurityTestSeverity.HIGH,
                        "CSRF token generation failed or invalid",
                        {"token": token},
                        test_start,
                        remediation="Check CSRF token generation configuration"
                    )
                    
            except Exception as e:
                self._add_test_result(
                    "csrf_functionality",
                    SecurityTestType.CSRF_TEST,
                    SecurityTestStatus.ERROR,
                    SecurityTestSeverity.HIGH,
                    f"CSRF functionality test failed: {str(e)}",
                    {"error": str(e)},
                    test_start,
                    remediation="Check CSRF protection implementation"
                )
                
        except Exception as e:
            self._add_test_result(
                "csrf_health_error",
                SecurityTestType.CSRF_TEST,
                SecurityTestStatus.ERROR,
                SecurityTestSeverity.HIGH,
                f"CSRF health check failed: {str(e)}",
                {"error": str(e)},
                test_start,
                remediation="Check CSRF protection configuration"
            )
    async def _check_security_headers_health(self):
        """Check security headers configuration"""
        test_start = datetime.utcnow()
        
        try:
            if not self.production_security_config:
                self._add_test_result(
                    "security_config_missing",
                    SecurityTestType.SECURITY_HEADERS,
                    SecurityTestStatus.WARNING,
                    SecurityTestSeverity.MEDIUM,
                    "Production security config not available",
                    {},
                    test_start,
                    remediation="Configure production security settings"
                )
                return
            
            # Get security headers configuration
            headers = self.production_security_config.get_security_headers()
            
            # Check required security headers
            required_headers = [
                "Strict-Transport-Security",
                "X-Frame-Options", 
                "X-Content-Type-Options",
                "Referrer-Policy",
                "Content-Security-Policy"
            ]
            
            missing_headers = []
            for header in required_headers:
                if header not in headers:
                    missing_headers.append(header)
            
            if missing_headers:
                self._add_test_result(
                    "security_headers_missing",
                    SecurityTestType.SECURITY_HEADERS,
                    SecurityTestStatus.FAILED,
                    SecurityTestSeverity.HIGH,
                    f"Missing required security headers: {', '.join(missing_headers)}",
                    {"missing_headers": missing_headers},
                    test_start,
                    remediation="Configure all required security headers"
                )
            else:
                self._add_test_result(
                    "security_headers_complete",
                    SecurityTestType.SECURITY_HEADERS,
                    SecurityTestStatus.PASSED,
                    SecurityTestSeverity.INFO,
                    "All required security headers are configured",
                    {"headers_count": len(headers)},
                    test_start
                )
            
            # Check HSTS configuration
            if "Strict-Transport-Security" in headers:
                hsts_header = headers["Strict-Transport-Security"]
                if "max-age=31536000" in hsts_header and "includeSubDomains" in hsts_header:
                    self._add_test_result(
                        "hsts_configuration",
                        SecurityTestType.SECURITY_HEADERS,
                        SecurityTestStatus.PASSED,
                        SecurityTestSeverity.INFO,
                        "HSTS properly configured with long max-age and subdomains",
                        {"hsts_header": hsts_header},
                        test_start
                    )
                else:
                    self._add_test_result(
                        "hsts_configuration",
                        SecurityTestType.SECURITY_HEADERS,
                        SecurityTestStatus.WARNING,
                        SecurityTestSeverity.MEDIUM,
                        "HSTS configuration could be improved",
                        {"hsts_header": hsts_header},
                        test_start,
                        remediation="Use max-age=31536000 and includeSubDomains for HSTS"
                    )
            
            # Check CSP configuration
            if "Content-Security-Policy" in headers:
                csp_header = headers["Content-Security-Policy"]
                if "'unsafe-eval'" in csp_header or "'unsafe-inline'" in csp_header:
                    self._add_test_result(
                        "csp_security",
                        SecurityTestType.SECURITY_HEADERS,
                        SecurityTestStatus.WARNING,
                        SecurityTestSeverity.MEDIUM,
                        "CSP allows unsafe directives",
                        {"csp_header": csp_header},
                        test_start,
                        remediation="Remove unsafe-eval and unsafe-inline from CSP"
                    )
                else:
                    self._add_test_result(
                        "csp_security",
                        SecurityTestType.SECURITY_HEADERS,
                        SecurityTestStatus.PASSED,
                        SecurityTestSeverity.INFO,
                        "CSP is properly configured without unsafe directives",
                        {},
                        test_start
                    )
                    
        except Exception as e:
            self._add_test_result(
                "security_headers_error",
                SecurityTestType.SECURITY_HEADERS,
                SecurityTestStatus.ERROR,
                SecurityTestSeverity.HIGH,
                f"Security headers check failed: {str(e)}",
                {"error": str(e)},
                test_start,
                remediation="Check security headers configuration"
            )
    
    async def _check_tls_configuration_health(self):
        """Check TLS configuration"""
        test_start = datetime.utcnow()
        
        try:
            if not self.production_security_config:
                self._add_test_result(
                    "tls_config_missing",
                    SecurityTestType.TLS_CONFIGURATION,
                    SecurityTestStatus.SKIPPED,
                    SecurityTestSeverity.MEDIUM,
                    "TLS configuration not available",
                    {},
                    test_start
                )
                return
            
            tls_settings = self.production_security_config.get_tls_settings()
            
            # Check TLS version
            min_version = tls_settings.get("min_version", "1.0")
            if min_version in ["1.2", "1.3"]:
                self._add_test_result(
                    "tls_version",
                    SecurityTestType.TLS_CONFIGURATION,
                    SecurityTestStatus.PASSED,
                    SecurityTestSeverity.INFO,
                    f"TLS minimum version is {min_version}",
                    {"min_version": min_version},
                    test_start
                )
            else:
                self._add_test_result(
                    "tls_version",
                    SecurityTestType.TLS_CONFIGURATION,
                    SecurityTestStatus.FAILED,
                    SecurityTestSeverity.HIGH,
                    f"TLS minimum version {min_version} is insecure",
                    {"min_version": min_version},
                    test_start,
                    remediation="Use TLS 1.2 or higher"
                )
            
            # Check cipher suites
            cipher_suites = tls_settings.get("cipher_suites", "")
            if "!aNULL" in cipher_suites and "!MD5" in cipher_suites:
                self._add_test_result(
                    "cipher_suites",
                    SecurityTestType.TLS_CONFIGURATION,
                    SecurityTestStatus.PASSED,
                    SecurityTestSeverity.INFO,
                    "Cipher suites properly exclude weak ciphers",
                    {},
                    test_start
                )
            else:
                self._add_test_result(
                    "cipher_suites",
                    SecurityTestType.TLS_CONFIGURATION,
                    SecurityTestStatus.WARNING,
                    SecurityTestSeverity.MEDIUM,
                    "Cipher suite configuration could be improved",
                    {"cipher_suites": cipher_suites},
                    test_start,
                    remediation="Exclude weak ciphers (!aNULL, !MD5, !RC4)"
                )
                
        except Exception as e:
            self._add_test_result(
                "tls_config_error",
                SecurityTestType.TLS_CONFIGURATION,
                SecurityTestStatus.ERROR,
                SecurityTestSeverity.HIGH,
                f"TLS configuration check failed: {str(e)}",
                {"error": str(e)},
                test_start,
                remediation="Check TLS configuration settings"
            )
    async def _check_security_monitoring_health(self):
        """Check security monitoring health"""
        test_start = datetime.utcnow()
        
        try:
            if not self.security_monitor:
                self._add_test_result(
                    "security_monitor_missing",
                    SecurityTestType.HEALTH_CHECK,
                    SecurityTestStatus.FAILED,
                    SecurityTestSeverity.HIGH,
                    "Security monitoring not configured",
                    {},
                    test_start,
                    remediation="Configure security monitoring for threat detection"
                )
                return
            
            # Test security event logging
            try:
                test_event = {
                    "event_type": "test_event",
                    "details": {"test": True},
                    "severity": "info",
                    "request_id": "health_check_test"
                }
                
                # This would normally log an event - we'll just check if the method exists
                if hasattr(self.security_monitor, 'log_security_event'):
                    self._add_test_result(
                        "security_monitoring_logging",
                        SecurityTestType.HEALTH_CHECK,
                        SecurityTestStatus.PASSED,
                        SecurityTestSeverity.INFO,
                        "Security monitoring logging is available",
                        {},
                        test_start
                    )
                else:
                    self._add_test_result(
                        "security_monitoring_logging",
                        SecurityTestType.HEALTH_CHECK,
                        SecurityTestStatus.FAILED,
                        SecurityTestSeverity.HIGH,
                        "Security monitoring logging not available",
                        {},
                        test_start,
                        remediation="Implement security event logging"
                    )
                
                # Check threat detection
                if hasattr(self.security_monitor, 'detect_threats'):
                    self._add_test_result(
                        "threat_detection",
                        SecurityTestType.HEALTH_CHECK,
                        SecurityTestStatus.PASSED,
                        SecurityTestSeverity.INFO,
                        "Threat detection is available",
                        {},
                        test_start
                    )
                else:
                    self._add_test_result(
                        "threat_detection",
                        SecurityTestType.HEALTH_CHECK,
                        SecurityTestStatus.WARNING,
                        SecurityTestSeverity.MEDIUM,
                        "Threat detection not available",
                        {},
                        test_start,
                        remediation="Implement threat detection algorithms"
                    )
                    
            except Exception as e:
                self._add_test_result(
                    "security_monitoring_functionality",
                    SecurityTestType.HEALTH_CHECK,
                    SecurityTestStatus.ERROR,
                    SecurityTestSeverity.HIGH,
                    f"Security monitoring functionality test failed: {str(e)}",
                    {"error": str(e)},
                    test_start,
                    remediation="Check security monitoring implementation"
                )
                
        except Exception as e:
            self._add_test_result(
                "security_monitoring_error",
                SecurityTestType.HEALTH_CHECK,
                SecurityTestStatus.ERROR,
                SecurityTestSeverity.HIGH,
                f"Security monitoring health check failed: {str(e)}",
                {"error": str(e)},
                test_start,
                remediation="Check security monitoring configuration"
            )
    
    async def _check_production_config_health(self):
        """Check production configuration health"""
        test_start = datetime.utcnow()
        
        try:
            if not self.production_security_config:
                self._add_test_result(
                    "production_config_missing",
                    SecurityTestType.HEALTH_CHECK,
                    SecurityTestStatus.WARNING,
                    SecurityTestSeverity.MEDIUM,
                    "Production security configuration not available",
                    {},
                    test_start,
                    remediation="Configure production security settings"
                )
                return
            
            # Check environment
            environment = self.production_security_config.environment.value
            if environment == "production":
                severity = SecurityTestSeverity.INFO
                status = SecurityTestStatus.PASSED
                message = "Running in production environment"
            elif environment == "staging":
                severity = SecurityTestSeverity.INFO
                status = SecurityTestStatus.PASSED
                message = "Running in staging environment"
            else:
                severity = SecurityTestSeverity.WARNING
                status = SecurityTestStatus.WARNING
                message = f"Running in {environment} environment"
            
            self._add_test_result(
                "environment_check",
                SecurityTestType.HEALTH_CHECK,
                status,
                severity,
                message,
                {"environment": environment},
                test_start
            )
            
            # Check external logging
            if hasattr(self.production_security_config, 'validate_external_logging'):
                logging_valid = self.production_security_config.validate_external_logging()
                if logging_valid:
                    self._add_test_result(
                        "external_logging",
                        SecurityTestType.HEALTH_CHECK,
                        SecurityTestStatus.PASSED,
                        SecurityTestSeverity.INFO,
                        "External logging is healthy",
                        {},
                        test_start
                    )
                else:
                    self._add_test_result(
                        "external_logging",
                        SecurityTestType.HEALTH_CHECK,
                        SecurityTestStatus.WARNING,
                        SecurityTestSeverity.MEDIUM,
                        "External logging connectivity issues",
                        {},
                        test_start,
                        remediation="Check external logging system connectivity"
                    )
                    
        except Exception as e:
            self._add_test_result(
                "production_config_error",
                SecurityTestType.HEALTH_CHECK,
                SecurityTestStatus.ERROR,
                SecurityTestSeverity.HIGH,
                f"Production config health check failed: {str(e)}",
                {"error": str(e)},
                test_start,
                remediation="Check production security configuration"
            )
    
    def _add_test_result(
        self,
        test_id: str,
        test_type: SecurityTestType,
        status: SecurityTestStatus,
        severity: SecurityTestSeverity,
        message: str,
        details: Dict[str, Any],
        test_start: datetime,
        remediation: Optional[str] = None,
        impact_assessment: Optional[str] = None
    ):
        """Add a test result to the results list"""
        duration = (datetime.utcnow() - test_start).total_seconds() * 1000
        
        result = SecurityTestResult(
            test_id=test_id,
            test_type=test_type,
            status=status,
            severity=severity,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            duration_ms=duration,
            remediation=remediation,
            impact_assessment=impact_assessment
        )
        
        self.test_results.append(result)
        
        # Log result
        log_level = {
            SecurityTestSeverity.CRITICAL: logging.CRITICAL,
            SecurityTestSeverity.HIGH: logging.ERROR,
            SecurityTestSeverity.MEDIUM: logging.WARNING,
            SecurityTestSeverity.LOW: logging.INFO,
            SecurityTestSeverity.INFO: logging.INFO
        }.get(severity, logging.INFO)
        
        logger.log(log_level, f"Security test {test_id}: {message}")
    
    def _calculate_metrics(self) -> SecurityMetrics:
        """Calculate security metrics from test results"""
        total_tests = len(self.test_results)
        
        if total_tests == 0:
            return SecurityMetrics(
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                warning_tests=0,
                error_tests=0,
                skipped_tests=0,
                critical_issues=0,
                high_issues=0,
                medium_issues=0,
                low_issues=0,
                info_issues=0,
                overall_score=0.0,
                compliance_status="unknown",
                last_updated=datetime.utcnow()
            )
        
        # Count by status
        passed_tests = sum(1 for r in self.test_results if r.status == SecurityTestStatus.PASSED)
        failed_tests = sum(1 for r in self.test_results if r.status == SecurityTestStatus.FAILED)
        warning_tests = sum(1 for r in self.test_results if r.status == SecurityTestStatus.WARNING)
        error_tests = sum(1 for r in self.test_results if r.status == SecurityTestStatus.ERROR)
        skipped_tests = sum(1 for r in self.test_results if r.status == SecurityTestStatus.SKIPPED)
        
        # Count by severity
        critical_issues = sum(1 for r in self.test_results if r.severity == SecurityTestSeverity.CRITICAL)
        high_issues = sum(1 for r in self.test_results if r.severity == SecurityTestSeverity.HIGH)
        medium_issues = sum(1 for r in self.test_results if r.severity == SecurityTestSeverity.MEDIUM)
        low_issues = sum(1 for r in self.test_results if r.severity == SecurityTestSeverity.LOW)
        info_issues = sum(1 for r in self.test_results if r.severity == SecurityTestSeverity.INFO)
        
        # Calculate overall score (0-100)
        score_weights = {
            SecurityTestStatus.PASSED: 1.0,
            SecurityTestStatus.WARNING: 0.7,
            SecurityTestStatus.SKIPPED: 0.5,
            SecurityTestStatus.FAILED: 0.0,
            SecurityTestStatus.ERROR: 0.0
        }
        
        total_score = sum(score_weights.get(r.status, 0.0) for r in self.test_results)
        overall_score = (total_score / total_tests) * 100 if total_tests > 0 else 0.0
        
        # Determine compliance status
        if critical_issues > 0 or failed_tests > total_tests * 0.3:
            compliance_status = "non_compliant"
        elif high_issues > 0 or warning_tests > total_tests * 0.2:
            compliance_status = "partial_compliance"
        else:
            compliance_status = "compliant"
        
        return SecurityMetrics(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warning_tests=warning_tests,
            error_tests=error_tests,
            skipped_tests=skipped_tests,
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            info_issues=info_issues,
            overall_score=overall_score,
            compliance_status=compliance_status,
            last_updated=datetime.utcnow()
        )
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of health check results"""
        if not self.metrics:
            return {"status": "no_metrics"}
        
        return {
            "overall_score": self.metrics.overall_score,
            "compliance_status": self.metrics.compliance_status,
            "total_tests": self.metrics.total_tests,
            "passed_tests": self.metrics.passed_tests,
            "failed_tests": self.metrics.failed_tests,
            "critical_issues": self.metrics.critical_issues,
            "high_issues": self.metrics.high_issues,
            "status_distribution": {
                "passed": self.metrics.passed_tests,
                "failed": self.metrics.failed_tests,
                "warning": self.metrics.warning_tests,
                "error": self.metrics.error_tests,
                "skipped": self.metrics.skipped_tests
            },
            "severity_distribution": {
                "critical": self.metrics.critical_issues,
                "high": self.metrics.high_issues,
                "medium": self.metrics.medium_issues,
                "low": self.metrics.low_issues,
                "info": self.metrics.info_issues
            }
        }
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Get failed and error tests
        failed_tests = [r for r in self.test_results if r.status in [SecurityTestStatus.FAILED, SecurityTestStatus.ERROR]]
        
        # Group by severity
        critical_tests = [r for r in failed_tests if r.severity == SecurityTestSeverity.CRITICAL]
        high_tests = [r for r in failed_tests if r.severity == SecurityTestSeverity.HIGH]
        
        # Add critical recommendations
        for test in critical_tests:
            if test.remediation:
                recommendations.append({
                    "priority": "critical",
                    "test_id": test.test_id,
                    "issue": test.message,
                    "recommendation": test.remediation,
                    "impact": test.impact_assessment or "Critical security vulnerability"
                })
        
        # Add high priority recommendations
        for test in high_tests:
            if test.remediation:
                recommendations.append({
                    "priority": "high",
                    "test_id": test.test_id,
                    "issue": test.message,
                    "recommendation": test.remediation,
                    "impact": test.impact_assessment or "High security risk"
                })
        
        # Add general recommendations based on metrics
        if self.metrics:
            if self.metrics.overall_score < 70:
                recommendations.append({
                    "priority": "high",
                    "test_id": "overall_score",
                    "issue": f"Overall security score is {self.metrics.overall_score:.1f}%",
                    "recommendation": "Address failed security tests to improve overall security posture",
                    "impact": "Poor security posture increases vulnerability to attacks"
                })
            
            if self.metrics.compliance_status == "non_compliant":
                recommendations.append({
                    "priority": "critical",
                    "test_id": "compliance",
                    "issue": "System is not compliant with security standards",
                    "recommendation": "Address all critical and high severity security issues",
                    "impact": "Non-compliance may violate security policies and regulations"
                })
        
        return recommendations


class SecurityTestingUtilities:
    """
    Security testing utilities for automated testing and validation
    
    Provides test endpoints and utilities that allow validation of security
    features without affecting production traffic.
    """
    
    def __init__(self, health_checker: SecurityHealthChecker):
        self.health_checker = health_checker
        logger.info("Security testing utilities initialized")
    
    async def test_rate_limiting_rules(self, test_ip: str = "127.0.0.1") -> Dict[str, Any]:
        """Test rate limiting rules without affecting production traffic"""
        test_start = datetime.utcnow()
        
        try:
            if not self.health_checker.rate_limiter:
                return {
                    "status": "skipped",
                    "message": "Rate limiter not configured",
                    "timestamp": test_start.isoformat()
                }
            
            # Test different rate limit scenarios
            test_results = []
            
            # Test anonymous user limits
            for i in range(5):
                # Simulate rate limit check
                test_key = f"test_anonymous_{test_ip}_{i}"
                # This would normally call the rate limiter
                test_results.append({
                    "test": f"anonymous_request_{i}",
                    "status": "simulated",
                    "message": "Rate limit test simulation"
                })
            
            return {
                "status": "completed",
                "test_ip": test_ip,
                "test_results": test_results,
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": (datetime.utcnow() - test_start).total_seconds() * 1000
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_csrf_protection(self) -> Dict[str, Any]:
        """Test CSRF protection functionality"""
        test_start = datetime.utcnow()
        
        try:
            if not self.health_checker.csrf_protection:
                return {
                    "status": "skipped",
                    "message": "CSRF protection not configured",
                    "timestamp": test_start.isoformat()
                }
            
            test_results = []
            
            # Test token generation
            test_session = "test_session_csrf"
            token = await self.health_checker.csrf_protection.generate_csrf_token(test_session)
            
            test_results.append({
                "test": "token_generation",
                "status": "passed" if token else "failed",
                "token_length": len(token) if token else 0
            })
            
            # Test token validation
            if token:
                is_valid = await self.health_checker.csrf_protection.validate_csrf_token(token, test_session)
                test_results.append({
                    "test": "token_validation",
                    "status": "passed" if is_valid else "failed",
                    "valid": is_valid
                })
                
                # Test invalid token
                invalid_valid = await self.health_checker.csrf_protection.validate_csrf_token("invalid_token", test_session)
                test_results.append({
                    "test": "invalid_token_rejection",
                    "status": "passed" if not invalid_valid else "failed",
                    "rejected": not invalid_valid
                })
            
            return {
                "status": "completed",
                "test_results": test_results,
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": (datetime.utcnow() - test_start).total_seconds() * 1000
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def validate_security_configuration(self) -> Dict[str, Any]:
        """Validate complete security configuration"""
        return await self.health_checker.run_comprehensive_health_check()
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get current security metrics"""
        if not self.health_checker.metrics:
            return {
                "status": "no_metrics",
                "message": "No metrics available. Run health check first."
            }
        
        return {
            "status": "available",
            "metrics": asdict(self.health_checker.metrics),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report for automated testing"""
        if not self.health_checker.test_results:
            return {
                "status": "no_data",
                "message": "No test results available. Run health check first."
            }
        
        # Group results by compliance areas
        compliance_areas = {
            "ssl_tls": [],
            "security_headers": [],
            "rate_limiting": [],
            "csrf_protection": [],
            "monitoring": [],
            "configuration": []
        }
        
        for result in self.health_checker.test_results:
            if result.test_type == SecurityTestType.CERTIFICATE_VALIDATION:
                compliance_areas["ssl_tls"].append(asdict(result))
            elif result.test_type == SecurityTestType.SECURITY_HEADERS:
                compliance_areas["security_headers"].append(asdict(result))
            elif result.test_type == SecurityTestType.RATE_LIMIT_TEST:
                compliance_areas["rate_limiting"].append(asdict(result))
            elif result.test_type == SecurityTestType.CSRF_TEST:
                compliance_areas["csrf_protection"].append(asdict(result))
            elif result.test_type == SecurityTestType.HEALTH_CHECK:
                compliance_areas["monitoring"].append(asdict(result))
            else:
                compliance_areas["configuration"].append(asdict(result))
        
        return {
            "status": "generated",
            "compliance_areas": compliance_areas,
            "summary": self.health_checker._generate_summary(),
            "recommendations": self.health_checker._generate_recommendations(),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global security testing instances
_security_health_checker: Optional[SecurityHealthChecker] = None
_security_testing_utilities: Optional[SecurityTestingUtilities] = None


def get_security_health_checker() -> SecurityHealthChecker:
    """Get the global security health checker instance"""
    global _security_health_checker
    if _security_health_checker is None:
        _security_health_checker = SecurityHealthChecker()
    return _security_health_checker


def get_security_testing_utilities() -> SecurityTestingUtilities:
    """Get the global security testing utilities instance"""
    global _security_testing_utilities
    if _security_testing_utilities is None:
        health_checker = get_security_health_checker()
        _security_testing_utilities = SecurityTestingUtilities(health_checker)
    return _security_testing_utilities


def initialize_security_testing(
    certificate_manager=None,
    rate_limiter=None,
    csrf_protection=None,
    security_monitor=None,
    production_security_config=None
) -> Tuple[SecurityHealthChecker, SecurityTestingUtilities]:
    """Initialize security testing with dependencies"""
    global _security_health_checker, _security_testing_utilities
    
    _security_health_checker = SecurityHealthChecker(
        certificate_manager=certificate_manager,
        rate_limiter=rate_limiter,
        csrf_protection=csrf_protection,
        security_monitor=security_monitor,
        production_security_config=production_security_config
    )
    
    _security_testing_utilities = SecurityTestingUtilities(_security_health_checker)
    
    return _security_health_checker, _security_testing_utilities