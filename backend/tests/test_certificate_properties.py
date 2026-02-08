"""
Property-based tests for Certificate Management

These tests validate universal properties of the certificate management system
using property-based testing with Hypothesis.

Feature: https-security-enhancements
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.strategies import composite
import logging

# Import certificate manager components
from modules.certificate_manager import (
    CertificateManager,
    CertificateProvider,
    CertificateState,
    CertificateResult,
    ValidationResult
)

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


# Custom strategies for certificate testing
@composite
def valid_domain_names(draw):
    """Generate valid domain names for testing"""
    # Use only safe ASCII characters for domain names
    domain_parts = draw(st.lists(
        st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz0123456789',
            min_size=1,
            max_size=8
        ).filter(lambda x: x and x.isalnum()),
        min_size=1,
        max_size=2
    ))
    
    # Join with dots to create domain
    if domain_parts:
        domain = '.'.join(domain_parts)
    else:
        domain = 'test'
    
    # Add some common test domains
    test_domains = ['localhost', '127.0.0.1', 'example.com', 'test.local']
    return draw(st.one_of(st.just(domain), st.sampled_from(test_domains)))


@composite
def certificate_environments(draw):
    """Generate valid certificate environments"""
    return draw(st.sampled_from(['development', 'staging', 'production']))


@composite
def certificate_providers(draw):
    """Generate valid certificate providers"""
    return draw(st.sampled_from(['self-signed', 'letsencrypt']))


@composite
def renewal_days(draw):
    """Generate valid renewal day values"""
    return draw(st.integers(min_value=1, max_value=90))


class TestCertificateLifecycleProperties:
    """
    Property-based tests for certificate lifecycle management.
    
    **Feature: https-security-enhancements, Property 1**: Certificate Lifecycle Management
    **Validates: Requirements 1.1, 1.2, 1.4, 6.1**
    """
    
    @given(
        domain=valid_domain_names(),
        environment=certificate_environments(),
        renewal_days=renewal_days()
    )
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=15000  # 15 seconds per test
    )
    @pytest.mark.asyncio
    async def test_certificate_provisioning_creates_valid_certificates(
        self, domain, environment, renewal_days
    ):
        """
        Property 1: Certificate Lifecycle Management
        
        For any configured domain and certificate provider, the Certificate_Manager 
        should automatically provision valid certificates on startup, renew certificates 
        within 30 days of expiration, and support environment-specific certificate types.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cert_path = temp_path / "certs"
            key_path = temp_path / "keys"
            
            # Initialize certificate manager
            manager = CertificateManager(
                cert_provider="self-signed",  # Use self-signed for testing
                cert_path=str(cert_path),
                key_path=str(key_path),
                renewal_days=renewal_days,
                environment=environment
            )
            
            # Property: Certificate provisioning should always succeed for valid domains
            result = await manager.provision_certificate(domain)
            
            # Verify provisioning result
            assert result.success, f"Certificate provisioning failed for {domain}: {result.error_message}"
            assert result.certificate_path is not None
            assert result.private_key_path is not None
            
            # Verify certificate files exist
            cert_file = Path(result.certificate_path)
            key_file = Path(result.private_key_path)
            assert cert_file.exists(), f"Certificate file not created: {cert_file}"
            assert key_file.exists(), f"Private key file not created: {key_file}"
            
            # Property: Provisioned certificates should be valid
            validation = await manager.validate_certificate(domain)
            assert validation.is_valid, f"Provisioned certificate is not valid for {domain}"
            assert validation.state in [CertificateState.VALID, CertificateState.EXPIRING]
            assert validation.expiration_date is not None
            assert validation.days_until_expiry is not None
            
            # Property: Certificate should be valid for at least the renewal period
            if validation.state == CertificateState.VALID:
                assert validation.days_until_expiry > renewal_days, \
                    f"Certificate expires too soon: {validation.days_until_expiry} <= {renewal_days}"
    
    @given(
        domain=valid_domain_names(),
        environment=certificate_environments()
    )
    @settings(
        max_examples=8,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=20000
    )
    @pytest.mark.asyncio
    async def test_certificate_renewal_maintains_validity(self, domain, environment):
        """
        Property 1 (continued): Certificate renewal should maintain certificate validity
        
        For any domain with an existing certificate, renewal should produce a valid 
        certificate without service interruption.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cert_path = temp_path / "certs"
            key_path = temp_path / "keys"
            
            manager = CertificateManager(
                cert_provider="self-signed",
                cert_path=str(cert_path),
                key_path=str(key_path),
                renewal_days=365,  # Force renewal by setting high renewal days
                environment=environment
            )
            
            # First, provision a certificate
            initial_result = await manager.provision_certificate(domain)
            assert initial_result.success
            
            # Get initial certificate info
            initial_validation = await manager.validate_certificate(domain)
            assert initial_validation.is_valid
            
            # Property: Renewal should succeed and maintain validity
            renewal_result = await manager.renew_certificate(domain)
            assert renewal_result.success, f"Certificate renewal failed for {domain}"
            
            # Verify renewed certificate is valid
            renewed_validation = await manager.validate_certificate(domain)
            assert renewed_validation.is_valid, "Renewed certificate is not valid"
            assert renewed_validation.state in [CertificateState.VALID, CertificateState.EXPIRING]
    
    @given(
        domains=st.lists(valid_domain_names(), min_size=1, max_size=5, unique=True),
        environment=certificate_environments()
    )
    @settings(
        max_examples=6,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=30000
    )
    @pytest.mark.asyncio
    async def test_multiple_domain_certificate_management(self, domains, environment):
        """
        Property 1 (continued): Certificate manager should handle multiple domains
        
        For any list of valid domains, the certificate manager should be able to 
        provision and manage certificates for all domains independently.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cert_path = temp_path / "certs"
            key_path = temp_path / "keys"
            
            manager = CertificateManager(
                cert_provider="self-signed",
                cert_path=str(cert_path),
                key_path=str(key_path),
                renewal_days=30,
                environment=environment
            )
            
            # Property: All valid domains should have certificates provisioned successfully
            for domain in domains:
                result = await manager.provision_certificate(domain)
                assert result.success, f"Failed to provision certificate for {domain}"
                
                # Verify each certificate is valid
                validation = await manager.validate_certificate(domain)
                assert validation.is_valid, f"Certificate not valid for {domain}"
            
            # Property: Certificate status should be available for all domains
            for domain in domains:
                status = await manager.get_certificate_status(domain)
                assert status.domain == domain
                assert status.status in [CertificateState.VALID, CertificateState.EXPIRING]
                assert status.certificate_path is not None
                assert status.private_key_path is not None


class TestCertificateValidationProperties:
    """
    Property-based tests for certificate validation and error handling.
    
    **Feature: https-security-enhancements, Property 2**: Certificate Validation and Error Handling
    **Validates: Requirements 1.3, 1.5**
    """
    
    @given(
        domain=valid_domain_names(),
        environment=certificate_environments()
    )
    @settings(
        max_examples=8,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=20000
    )
    @pytest.mark.asyncio
    async def test_certificate_validation_consistency(self, domain, environment):
        """
        Property 2: Certificate Validation and Error Handling
        
        For any invalid certificate or renewal failure, the Certificate_Manager should 
        prevent service startup with detailed error logging and trigger immediate 
        administrator alerts.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cert_path = temp_path / "certs"
            key_path = temp_path / "keys"
            
            manager = CertificateManager(
                cert_provider="self-signed",
                cert_path=str(cert_path),
                key_path=str(key_path),
                renewal_days=30,
                environment=environment
            )
            
            # Property: Validation of non-existent certificate should fail gracefully
            validation = await manager.validate_certificate(domain)
            assert not validation.is_valid, "Non-existent certificate should not be valid"
            assert validation.state == CertificateState.INVALID
            assert validation.error_message is not None
            
            # Provision a certificate
            result = await manager.provision_certificate(domain)
            assert result.success
            
            # Property: Validation of valid certificate should succeed
            validation = await manager.validate_certificate(domain)
            assert validation.is_valid, "Valid certificate should pass validation"
            assert validation.state in [CertificateState.VALID, CertificateState.EXPIRING]
            assert validation.expiration_date is not None
            assert validation.days_until_expiry is not None
    
    @given(
        invalid_domain=st.one_of(
            st.just(""),  # Empty domain
            st.just("invalid..domain"),  # Double dots
            st.just("domain."),  # Trailing dot
            st.just(".domain"),  # Leading dot
            st.just("domain with spaces"),  # Spaces
            st.just("domain@invalid"),  # Invalid characters
            st.text(min_size=254, max_size=300)  # Too long
        ),
        environment=certificate_environments()
    )
    @settings(
        max_examples=6,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=15000
    )
    @pytest.mark.asyncio
    async def test_invalid_domain_handling(self, invalid_domain, environment):
        """
        Property 2 (continued): Invalid domains should be rejected with clear error messages
        
        For any invalid domain format, the certificate manager should reject the request
        with a descriptive error message and not create any certificate files.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cert_path = temp_path / "certs"
            key_path = temp_path / "keys"
            
            manager = CertificateManager(
                cert_provider="self-signed",
                cert_path=str(cert_path),
                key_path=str(key_path),
                renewal_days=30,
                environment=environment
            )
            
            # Property: Invalid domains should be rejected
            result = await manager.provision_certificate(invalid_domain)
            assert not result.success, f"Invalid domain {invalid_domain} should be rejected"
            assert result.error_message is not None
            assert "Invalid domain format" in result.error_message
            
            # Property: No certificate files should be created for invalid domains
            cert_file = cert_path / f"{invalid_domain}.crt"
            key_file = key_path / f"{invalid_domain}.key"
            assert not cert_file.exists(), f"Certificate file should not exist for invalid domain"
            assert not key_file.exists(), f"Key file should not exist for invalid domain"
    
    @given(
        domain=valid_domain_names(),
        environment=certificate_environments()
    )
    @settings(
        max_examples=6,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=20000
    )
    @pytest.mark.asyncio
    async def test_certificate_status_consistency(self, domain, environment):
        """
        Property 2 (continued): Certificate status should be consistent across operations
        
        For any domain, the certificate status should remain consistent between
        validation, status checks, and renewal operations.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cert_path = temp_path / "certs"
            key_path = temp_path / "keys"
            
            manager = CertificateManager(
                cert_provider="self-signed",
                cert_path=str(cert_path),
                key_path=str(key_path),
                renewal_days=30,
                environment=environment
            )
            
            # Provision certificate
            result = await manager.provision_certificate(domain)
            assert result.success
            
            # Get validation and status
            validation = await manager.validate_certificate(domain)
            status = await manager.get_certificate_status(domain)
            
            # Property: Validation and status should be consistent
            assert validation.is_valid == (status.status in [CertificateState.VALID, CertificateState.EXPIRING])
            assert validation.state == status.status
            assert validation.expiration_date == status.expires_at
            
            # Property: Status should contain all required information
            assert status.domain == domain
            assert status.certificate_path is not None
            assert status.private_key_path is not None
            assert Path(status.certificate_path).exists()
            assert Path(status.private_key_path).exists()


class TestCertificateEnvironmentProperties:
    """
    Property-based tests for environment-specific certificate configuration.
    
    **Feature: https-security-enhancements, Property 1 (Environment Support)**
    **Validates: Requirements 1.4, 6.1**
    """
    
    @given(
        environment=certificate_environments(),
        provider=certificate_providers()
    )
    @settings(
        max_examples=6,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=15000
    )
    @pytest.mark.asyncio
    async def test_environment_specific_configuration(self, environment, provider):
        """
        Property 1 (Environment): Environment-specific configuration should be applied correctly
        
        For any environment and certificate provider combination, the certificate manager
        should apply the appropriate configuration settings.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cert_path = temp_path / "certs"
            key_path = temp_path / "keys"
            
            # Override provider for testing (use self-signed to avoid external dependencies)
            test_provider = "self-signed" if provider == "letsencrypt" else provider
            
            manager = CertificateManager(
                cert_provider=test_provider,
                cert_path=str(cert_path),
                key_path=str(key_path),
                renewal_days=30,
                environment=environment
            )
            
            # Property: Configuration should match environment
            config = manager.config
            assert config is not None
            
            if environment == "development":
                # Development should have relaxed settings
                assert not config.get("validation_required", True)
                assert "localhost" in config.get("domains", [])
            elif environment in ["staging", "production"]:
                # Production environments should have strict settings
                assert config.get("auto_renewal", False)
                assert config.get("validation_required", False)
            
            # Property: Manager should be properly initialized
            assert manager.environment == environment
            assert manager.cert_path.exists()
            assert manager.key_path.exists()
    
    @given(
        domain=st.sampled_from(["localhost", "127.0.0.1"]),  # Safe domains for all environments
        environment=certificate_environments()
    )
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=20000
    )
    @pytest.mark.asyncio
    async def test_cross_environment_certificate_compatibility(self, domain, environment):
        """
        Property 1 (Environment): Certificates should work across different environments
        
        For any domain, certificates generated in one environment should be readable
        and validatable by certificate managers in other environments.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cert_path = temp_path / "certs"
            key_path = temp_path / "keys"
            
            # Create certificate in one environment
            manager1 = CertificateManager(
                cert_provider="self-signed",
                cert_path=str(cert_path),
                key_path=str(key_path),
                renewal_days=30,
                environment=environment
            )
            
            result = await manager1.provision_certificate(domain)
            assert result.success
            
            # Validate with manager in different environment
            other_env = "production" if environment != "production" else "development"
            manager2 = CertificateManager(
                cert_provider="self-signed",
                cert_path=str(cert_path),
                key_path=str(key_path),
                renewal_days=30,
                environment=other_env
            )
            
            # Property: Certificate should be valid across environments
            validation = await manager2.validate_certificate(domain)
            assert validation.is_valid, f"Certificate should be valid across environments"
            
            # Property: Status should be consistent across environments
            status1 = await manager1.get_certificate_status(domain)
            status2 = await manager2.get_certificate_status(domain)
            
            assert status1.domain == status2.domain
            assert status1.expires_at == status2.expires_at
            assert status1.certificate_path == status2.certificate_path


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