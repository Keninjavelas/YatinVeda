"""
Security Testing and Health Check API Endpoints

This module provides REST API endpoints for security testing, health checks,
certificate validation, and security metrics collection.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from modules.security_testing import (
    get_security_health_checker,
    get_security_testing_utilities,
    SecurityTestType,
    SecurityTestSeverity,
    SecurityTestStatus
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/security-testing", tags=["Security Testing"])


class SecurityHealthCheckResponse(BaseModel):
    """Security health check response model"""
    status: str
    timestamp: str
    duration_ms: float
    metrics: Dict[str, Any]
    test_results: list
    summary: Dict[str, Any]
    recommendations: list


class SecurityTestRequest(BaseModel):
    """Security test request model"""
    test_type: Optional[str] = Field(None, description="Type of security test to run")
    test_ip: Optional[str] = Field("127.0.0.1", description="IP address for testing")
    include_details: bool = Field(True, description="Include detailed test results")


class SecurityMetricsResponse(BaseModel):
    """Security metrics response model"""
    status: str
    metrics: Optional[Dict[str, Any]] = None
    timestamp: str
    message: Optional[str] = None


@router.get("/health", response_model=SecurityHealthCheckResponse)
async def security_health_check(
    include_certificate_validation: bool = Query(True, description="Include certificate validation tests"),
    include_rate_limiting: bool = Query(True, description="Include rate limiting tests"),
    include_csrf_protection: bool = Query(True, description="Include CSRF protection tests"),
    include_security_headers: bool = Query(True, description="Include security headers tests"),
    include_tls_config: bool = Query(True, description="Include TLS configuration tests")
):
    """
    Run comprehensive security health check
    
    Validates all security configurations and returns detailed health status.
    This endpoint provides security health check that validates all security
    configurations as required by Requirement 7.1.
    """
    try:
        logger.info("Starting security health check via API")
        
        health_checker = get_security_health_checker()
        
        # Run comprehensive health check
        result = await health_checker.run_comprehensive_health_check()
        
        # Filter results based on query parameters
        if not include_certificate_validation:
            result["test_results"] = [
                r for r in result["test_results"] 
                if r.get("test_type") != SecurityTestType.CERTIFICATE_VALIDATION.value
            ]
        
        if not include_rate_limiting:
            result["test_results"] = [
                r for r in result["test_results"] 
                if r.get("test_type") != SecurityTestType.RATE_LIMIT_TEST.value
            ]
        
        if not include_csrf_protection:
            result["test_results"] = [
                r for r in result["test_results"] 
                if r.get("test_type") != SecurityTestType.CSRF_TEST.value
            ]
        
        if not include_security_headers:
            result["test_results"] = [
                r for r in result["test_results"] 
                if r.get("test_type") != SecurityTestType.SECURITY_HEADERS.value
            ]
        
        if not include_tls_config:
            result["test_results"] = [
                r for r in result["test_results"] 
                if r.get("test_type") != SecurityTestType.TLS_CONFIGURATION.value
            ]
        
        logger.info(f"Security health check completed with {len(result['test_results'])} tests")
        
        return SecurityHealthCheckResponse(**result)
        
    except Exception as e:
        logger.error(f"Security health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Security health check failed: {str(e)}"
        )


@router.get("/certificate-validation")
async def certificate_validation_test(
    domain: Optional[str] = Query(None, description="Specific domain to validate"),
    check_expiry: bool = Query(True, description="Check certificate expiry"),
    check_chain: bool = Query(True, description="Check certificate chain integrity")
):
    """
    Validate SSL certificate configuration and integrity
    
    This endpoint validates certificate chain integrity and expiration dates
    as required by Requirement 7.2.
    """
    try:
        logger.info(f"Starting certificate validation test for domain: {domain}")
        
        health_checker = get_security_health_checker()
        
        # Run certificate-specific health check
        await health_checker._check_certificate_health()
        
        # Filter results to certificate validation only
        cert_results = [
            result for result in health_checker.test_results
            if result.test_type == SecurityTestType.CERTIFICATE_VALIDATION
        ]
        
        # Filter by domain if specified
        if domain:
            cert_results = [
                result for result in cert_results
                if domain in result.details.get("domain", "")
            ]
        
        return {
            "status": "completed",
            "domain": domain,
            "timestamp": datetime.utcnow().isoformat(),
            "test_results": [
                {
                    "test_id": result.test_id,
                    "status": result.status.value,
                    "severity": result.severity.value,
                    "message": result.message,
                    "details": result.details,
                    "remediation": result.remediation
                }
                for result in cert_results
            ]
        }
        
    except Exception as e:
        logger.error(f"Certificate validation test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Certificate validation test failed: {str(e)}"
        )


@router.post("/rate-limiting-test")
async def rate_limiting_test(request: SecurityTestRequest):
    """
    Test rate limiting rules without affecting production traffic
    
    This endpoint provides test endpoints that allow validation of rate limiting
    rules without affecting production traffic as required by Requirement 7.3.
    """
    try:
        logger.info(f"Starting rate limiting test for IP: {request.test_ip}")
        
        testing_utilities = get_security_testing_utilities()
        
        # Run rate limiting test
        result = await testing_utilities.test_rate_limiting_rules(request.test_ip)
        
        return {
            "status": result["status"],
            "test_ip": request.test_ip,
            "timestamp": result["timestamp"],
            "test_results": result.get("test_results", []),
            "duration_ms": result.get("duration_ms", 0),
            "message": result.get("message", "Rate limiting test completed")
        }
        
    except Exception as e:
        logger.error(f"Rate limiting test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Rate limiting test failed: {str(e)}"
        )


@router.post("/csrf-protection-test")
async def csrf_protection_test():
    """
    Test CSRF protection functionality
    
    Tests CSRF token generation, validation, and security policy enforcement.
    """
    try:
        logger.info("Starting CSRF protection test")
        
        testing_utilities = get_security_testing_utilities()
        
        # Run CSRF protection test
        result = await testing_utilities.test_csrf_protection()
        
        return {
            "status": result["status"],
            "timestamp": result["timestamp"],
            "test_results": result.get("test_results", []),
            "duration_ms": result.get("duration_ms", 0),
            "message": result.get("message", "CSRF protection test completed")
        }
        
    except Exception as e:
        logger.error(f"CSRF protection test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"CSRF protection test failed: {str(e)}"
        )


@router.get("/security-metrics", response_model=SecurityMetricsResponse)
async def get_security_metrics():
    """
    Get current security metrics for automated testing and compliance reporting
    
    This endpoint maintains security metrics that can be queried for automated
    security testing and compliance reporting as required by Requirement 7.5.
    """
    try:
        logger.info("Retrieving security metrics")
        
        testing_utilities = get_security_testing_utilities()
        
        # Get security metrics
        metrics_result = testing_utilities.get_security_metrics()
        
        return SecurityMetricsResponse(
            status=metrics_result["status"],
            metrics=metrics_result.get("metrics"),
            timestamp=metrics_result["timestamp"],
            message=metrics_result.get("message")
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve security metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve security metrics: {str(e)}"
        )


@router.get("/compliance-report")
async def generate_compliance_report(
    format: str = Query("json", description="Report format (json, summary)"),
    include_recommendations: bool = Query(True, description="Include security recommendations")
):
    """
    Generate compliance report for automated testing
    
    Provides detailed remediation guidance and impact assessment when security
    vulnerabilities are detected as required by Requirement 7.6.
    """
    try:
        logger.info(f"Generating compliance report in {format} format")
        
        testing_utilities = get_security_testing_utilities()
        
        # Generate compliance report
        report = testing_utilities.generate_compliance_report()
        
        if format == "summary":
            # Return summarized version
            return {
                "status": report["status"],
                "timestamp": report["timestamp"],
                "summary": report.get("summary", {}),
                "recommendations": report.get("recommendations", []) if include_recommendations else [],
                "compliance_areas_count": {
                    area: len(tests) for area, tests in report.get("compliance_areas", {}).items()
                }
            }
        else:
            # Return full report
            if not include_recommendations:
                report.pop("recommendations", None)
            
            return report
        
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate compliance report: {str(e)}"
        )


@router.get("/vulnerability-assessment")
async def vulnerability_assessment(
    severity_filter: Optional[str] = Query(None, description="Filter by severity (critical, high, medium, low)"),
    include_remediation: bool = Query(True, description="Include remediation guidance")
):
    """
    Perform vulnerability assessment and provide remediation guidance
    
    This endpoint provides detailed remediation guidance and impact assessment
    when security vulnerabilities are detected during testing as required by
    Requirement 7.6.
    """
    try:
        logger.info(f"Starting vulnerability assessment with severity filter: {severity_filter}")
        
        health_checker = get_security_health_checker()
        
        # Run comprehensive health check if no results exist
        if not health_checker.test_results:
            await health_checker.run_comprehensive_health_check()
        
        # Filter results by severity if specified
        results = health_checker.test_results
        if severity_filter:
            try:
                filter_severity = SecurityTestSeverity(severity_filter.lower())
                results = [r for r in results if r.severity == filter_severity]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid severity filter: {severity_filter}"
                )
        
        # Get failed and warning results (vulnerabilities)
        vulnerabilities = [
            r for r in results 
            if r.status in [SecurityTestStatus.FAILED, SecurityTestStatus.ERROR, SecurityTestStatus.WARNING]
        ]
        
        # Format vulnerability report
        vulnerability_report = []
        for vuln in vulnerabilities:
            vuln_data = {
                "vulnerability_id": vuln.test_id,
                "type": vuln.test_type.value,
                "severity": vuln.severity.value,
                "status": vuln.status.value,
                "description": vuln.message,
                "details": vuln.details,
                "timestamp": vuln.timestamp.isoformat()
            }
            
            if include_remediation:
                vuln_data["remediation"] = vuln.remediation
                vuln_data["impact_assessment"] = vuln.impact_assessment
            
            vulnerability_report.append(vuln_data)
        
        # Generate summary
        severity_counts = {}
        for severity in SecurityTestSeverity:
            severity_counts[severity.value] = sum(
                1 for v in vulnerabilities if v.severity == severity
            )
        
        return {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "total_vulnerabilities": len(vulnerabilities),
            "severity_distribution": severity_counts,
            "vulnerabilities": vulnerability_report,
            "recommendations": health_checker._generate_recommendations() if include_remediation else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vulnerability assessment failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Vulnerability assessment failed: {str(e)}"
        )


@router.get("/test-endpoints")
async def list_test_endpoints():
    """
    List all available security test endpoints
    
    Provides information about available security testing capabilities.
    """
    return {
        "endpoints": {
            "/health": {
                "method": "GET",
                "description": "Comprehensive security health check",
                "requirement": "7.1 - Security health check endpoints"
            },
            "/certificate-validation": {
                "method": "GET", 
                "description": "SSL certificate validation and integrity check",
                "requirement": "7.2 - Certificate chain integrity validation"
            },
            "/rate-limiting-test": {
                "method": "POST",
                "description": "Test rate limiting rules without affecting production",
                "requirement": "7.3 - Rate limiting validation endpoints"
            },
            "/csrf-protection-test": {
                "method": "POST",
                "description": "Test CSRF protection functionality",
                "requirement": "7.4 - Security policy testing mode"
            },
            "/security-metrics": {
                "method": "GET",
                "description": "Get security metrics for automated testing",
                "requirement": "7.5 - Security metrics for compliance reporting"
            },
            "/compliance-report": {
                "method": "GET",
                "description": "Generate compliance report",
                "requirement": "7.5 - Compliance reporting"
            },
            "/vulnerability-assessment": {
                "method": "GET",
                "description": "Vulnerability assessment with remediation guidance",
                "requirement": "7.6 - Remediation guidance and impact assessment"
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }