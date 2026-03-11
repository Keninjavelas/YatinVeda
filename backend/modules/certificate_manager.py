"""
SSL/TLS Certificate Management Module for YatinVeda

This module provides automated SSL certificate management with support for:
- Let's Encrypt certificate provisioning and renewal
- Self-signed certificates for development
- Certificate validation and health checks
- Environment-specific configuration
"""

import os
import ssl
import socket
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import asyncio
import aiofiles
import hashlib
import json

logger = logging.getLogger(__name__)


class CertificateState(Enum):
    """Certificate status states"""
    VALID = "valid"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    INVALID = "invalid"
    PROVISIONING = "provisioning"
    RENEWAL_FAILED = "renewal_failed"


class CertificateProvider(Enum):
    """Supported certificate providers"""
    LETSENCRYPT = "letsencrypt"
    SELF_SIGNED = "self-signed"
    CUSTOM = "custom"


@dataclass
class CertificateResult:
    """Result of certificate operations"""
    success: bool
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    error_message: Optional[str] = None
    expiration_date: Optional[datetime] = None


@dataclass
class ValidationResult:
    """Result of certificate validation"""
    is_valid: bool
    state: CertificateState
    expiration_date: Optional[datetime] = None
    days_until_expiry: Optional[int] = None
    error_message: Optional[str] = None
    certificate_chain: Optional[List[str]] = None


@dataclass
class CertificateStatus:
    """Certificate status information"""
    domain: str
    status: CertificateState
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    issuer: Optional[str] = None
    renewal_scheduled: Optional[datetime] = None
    last_renewal_attempt: Optional[datetime] = None
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None


class CertificateManager:
    """
    Manages SSL/TLS certificates with automatic provisioning and renewal.
    
    Supports multiple certificate providers and environment-specific configuration.
    """
    
    def __init__(
        self,
        cert_provider: str = "letsencrypt",
        cert_path: str = "/etc/ssl/certs",
        key_path: str = "/etc/ssl/private",
        renewal_days: int = 30,
        environment: str = "development"
    ):
        """
        Initialize Certificate Manager.
        
        Args:
            cert_provider: Certificate provider (letsencrypt, self-signed, custom)
            cert_path: Directory for certificate files
            key_path: Directory for private key files
            renewal_days: Days before expiration to trigger renewal
            environment: Deployment environment (development, staging, production)
        """
        self.cert_provider = CertificateProvider(cert_provider)
        self.cert_path = Path(cert_path)
        self.key_path = Path(key_path)
        self.renewal_days = renewal_days
        self.environment = environment
        
        # Create directories if they don't exist
        self.cert_path.mkdir(parents=True, exist_ok=True)
        self.key_path.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.config = self._load_configuration()
        
        # Certificate status cache
        self._certificate_cache: Dict[str, CertificateStatus] = {}
        
        logger.info(f"Certificate Manager initialized: provider={cert_provider}, environment={environment}")
    
    def _load_configuration(self) -> Dict:
        """Load environment-specific certificate configuration"""
        config = {
            "development": {
                "provider": CertificateProvider.SELF_SIGNED,
                "domains": ["localhost", "127.0.0.1"],
                "auto_renewal": False,
                "validation_required": False
            },
            "staging": {
                "provider": CertificateProvider.LETSENCRYPT,
                "domains": os.getenv("STAGING_DOMAINS", "staging.yatinveda.com").split(","),
                "auto_renewal": True,
                "validation_required": True,
                "acme_server": "https://acme-staging-v02.api.letsencrypt.org/directory"
            },
            "production": {
                "provider": CertificateProvider.LETSENCRYPT,
                "domains": os.getenv("PRODUCTION_DOMAINS", "yatinveda.com,api.yatinveda.com").split(","),
                "auto_renewal": True,
                "validation_required": True,
                "acme_server": "https://acme-v02.api.letsencrypt.org/directory"
            }
        }
        
        env_config = config.get(self.environment, config["development"])
        
        # Override provider with explicitly passed value (for testing)
        env_config["provider"] = self.cert_provider
        
        # Override provider if explicitly set
        if self.cert_provider != CertificateProvider.SELF_SIGNED:
            env_config["provider"] = self.cert_provider
        
        return env_config
    
    async def provision_certificate(self, domain: str) -> CertificateResult:
        """
        Provision SSL certificate for a domain.
        
        Args:
            domain: Domain name for certificate
            
        Returns:
            CertificateResult with operation status and file paths
        """
        logger.info(f"Provisioning certificate for domain: {domain}")
        
        try:
            # Validate domain format
            if not self._is_valid_domain(domain):
                return CertificateResult(
                    success=False,
                    error_message=f"Invalid domain format: {domain}"
                )
            
            # Check if certificate already exists and is valid
            existing_cert = await self.validate_certificate(domain)
            if existing_cert.is_valid and existing_cert.days_until_expiry > self.renewal_days:
                logger.info(f"Valid certificate already exists for {domain}")
                return CertificateResult(
                    success=True,
                    certificate_path=str(self.cert_path / f"{domain}.crt"),
                    private_key_path=str(self.key_path / f"{domain}.key"),
                    expiration_date=existing_cert.expiration_date
                )
            
            # Provision based on provider
            if self.config["provider"] == CertificateProvider.LETSENCRYPT:
                result = await self._provision_letsencrypt_certificate(domain)
            elif self.config["provider"] == CertificateProvider.SELF_SIGNED:
                result = await self._provision_self_signed_certificate(domain)
            else:
                return CertificateResult(
                    success=False,
                    error_message=f"Unsupported certificate provider: {self.config['provider']}"
                )
            
            if result.success:
                # Update certificate cache
                await self._update_certificate_cache(domain)
                logger.info(f"Successfully provisioned certificate for {domain}")
            else:
                logger.error(f"Failed to provision certificate for {domain}: {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error provisioning certificate for {domain}: {str(e)}")
            return CertificateResult(
                success=False,
                error_message=f"Certificate provisioning failed: {str(e)}"
            )
    
    async def renew_certificate(self, domain: str) -> CertificateResult:
        """
        Renew SSL certificate for a domain.
        
        Args:
            domain: Domain name for certificate renewal
            
        Returns:
            CertificateResult with renewal status
        """
        logger.info(f"Renewing certificate for domain: {domain}")
        
        try:
            # Validate current certificate
            validation = await self.validate_certificate(domain)
            
            if not validation.is_valid:
                logger.warning(f"Current certificate for {domain} is invalid, provisioning new one")
                return await self.provision_certificate(domain)
            
            if validation.days_until_expiry > self.renewal_days:
                logger.info(f"Certificate for {domain} does not need renewal yet ({validation.days_until_expiry} days remaining)")
                return CertificateResult(
                    success=True,
                    certificate_path=str(self.cert_path / f"{domain}.crt"),
                    private_key_path=str(self.key_path / f"{domain}.key"),
                    expiration_date=validation.expiration_date
                )
            
            # Backup current certificate
            await self._backup_certificate(domain)
            
            # Renew based on provider
            if self.config["provider"] == CertificateProvider.LETSENCRYPT:
                result = await self._renew_letsencrypt_certificate(domain)
            elif self.config["provider"] == CertificateProvider.SELF_SIGNED:
                result = await self._provision_self_signed_certificate(domain)
            else:
                return CertificateResult(
                    success=False,
                    error_message=f"Unsupported certificate provider for renewal: {self.config['provider']}"
                )
            
            if result.success:
                await self._update_certificate_cache(domain)
                logger.info(f"Successfully renewed certificate for {domain}")
            else:
                logger.error(f"Failed to renew certificate for {domain}: {result.error_message}")
                # Restore backup if renewal failed
                await self._restore_certificate_backup(domain)
            
            return result
            
        except Exception as e:
            logger.error(f"Error renewing certificate for {domain}: {str(e)}")
            return CertificateResult(
                success=False,
                error_message=f"Certificate renewal failed: {str(e)}"
            )
    
    async def validate_certificate(self, domain: str) -> ValidationResult:
        """
        Validate SSL certificate for a domain.
        
        Args:
            domain: Domain name to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        try:
            cert_file = self.cert_path / f"{domain}.crt"
            
            if not cert_file.exists():
                return ValidationResult(
                    is_valid=False,
                    state=CertificateState.INVALID,
                    error_message=f"Certificate file not found: {cert_file}"
                )
            
            # Read certificate file
            async with aiofiles.open(cert_file, 'r') as f:
                cert_content = await f.read()
            
            # Parse certificate
            cert = ssl.PEM_cert_to_DER_cert(cert_content)
            cert_info = ssl.DER_cert_to_PEM_cert(cert)
            
            # Extract certificate details using OpenSSL
            result = await self._extract_certificate_info(cert_file)
            
            if not result:
                return ValidationResult(
                    is_valid=False,
                    state=CertificateState.INVALID,
                    error_message="Failed to parse certificate"
                )
            
            expiration_date, issuer, subject = result
            
            # Calculate days until expiry
            now = datetime.utcnow()
            days_until_expiry = (expiration_date - now).days
            
            # Determine certificate state
            if days_until_expiry < 0:
                state = CertificateState.EXPIRED
                is_valid = False
            elif days_until_expiry <= self.renewal_days:
                state = CertificateState.EXPIRING
                is_valid = True
            else:
                state = CertificateState.VALID
                is_valid = True
            
            return ValidationResult(
                is_valid=is_valid,
                state=state,
                expiration_date=expiration_date,
                days_until_expiry=days_until_expiry
            )
            
        except Exception as e:
            logger.error(f"Error validating certificate for {domain}: {str(e)}")
            return ValidationResult(
                is_valid=False,
                state=CertificateState.INVALID,
                error_message=f"Certificate validation failed: {str(e)}"
            )
    
    async def get_certificate_status(self, domain: str) -> CertificateStatus:
        """
        Get comprehensive certificate status for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            CertificateStatus with detailed information
        """
        # Check cache first
        if domain in self._certificate_cache:
            cached_status = self._certificate_cache[domain]
            # Return cached status if it's recent (within 1 hour)
            if cached_status.last_renewal_attempt and \
               (datetime.utcnow() - cached_status.last_renewal_attempt).seconds < 3600:
                return cached_status
        
        # Validate certificate
        validation = await self.validate_certificate(domain)
        
        # Create status object
        status = CertificateStatus(
            domain=domain,
            status=validation.state,
            expires_at=validation.expiration_date,
            certificate_path=str(self.cert_path / f"{domain}.crt"),
            private_key_path=str(self.key_path / f"{domain}.key")
        )
        
        # Try to extract additional information
        try:
            cert_file = self.cert_path / f"{domain}.crt"
            if cert_file.exists():
                result = await self._extract_certificate_info(cert_file)
                if result:
                    _, issuer, _ = result
                    status.issuer = issuer
        except Exception as e:
            logger.warning(f"Could not extract certificate info for {domain}: {str(e)}")
        
        # Update cache
        self._certificate_cache[domain] = status
        
        return status
    
    async def check_renewal_needed(self) -> List[str]:
        """
        Check which certificates need renewal.
        
        Returns:
            List of domain names that need certificate renewal
        """
        domains_needing_renewal = []
        
        for domain in self.config.get("domains", []):
            try:
                validation = await self.validate_certificate(domain)
                
                if not validation.is_valid or \
                   (validation.days_until_expiry is not None and validation.days_until_expiry <= self.renewal_days):
                    domains_needing_renewal.append(domain)
                    
            except Exception as e:
                logger.error(f"Error checking renewal for {domain}: {str(e)}")
                domains_needing_renewal.append(domain)
        
        return domains_needing_renewal
    
    async def _provision_letsencrypt_certificate(self, domain: str) -> CertificateResult:
        """Provision Let's Encrypt certificate using certbot"""
        try:
            # Check if certbot is available
            certbot_cmd = await self._find_certbot_command()
            if not certbot_cmd:
                return CertificateResult(
                    success=False,
                    error_message="Certbot not found. Please install certbot for Let's Encrypt certificates."
                )
            
            # Prepare certbot command
            acme_server = self.config.get("acme_server", "https://acme-v02.api.letsencrypt.org/directory")
            
            cmd = [
                certbot_cmd,
                "certonly",
                "--standalone",
                "--non-interactive",
                "--agree-tos",
                "--email", os.getenv("LETSENCRYPT_EMAIL", "admin@yatinveda.com"),
                "--server", acme_server,
                "--cert-path", str(self.cert_path),
                "--key-path", str(self.key_path),
                "-d", domain
            ]
            
            # Execute certbot
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Move certificates to our directory structure
                await self._organize_letsencrypt_certificates(domain)
                
                return CertificateResult(
                    success=True,
                    certificate_path=str(self.cert_path / f"{domain}.crt"),
                    private_key_path=str(self.key_path / f"{domain}.key")
                )
            else:
                error_msg = stderr.decode() if stderr else "Unknown certbot error"
                return CertificateResult(
                    success=False,
                    error_message=f"Certbot failed: {error_msg}"
                )
                
        except Exception as e:
            return CertificateResult(
                success=False,
                error_message=f"Let's Encrypt provisioning failed: {str(e)}"
            )
    
    async def _provision_self_signed_certificate(self, domain: str) -> CertificateResult:
        """Generate self-signed certificate for development"""
        try:
            cert_file = self.cert_path / f"{domain}.crt"
            key_file = self.key_path / f"{domain}.key"
            
            # Generate private key and certificate using OpenSSL
            cmd = [
                "openssl", "req", "-x509", "-newkey", "rsa:4096",
                "-keyout", str(key_file),
                "-out", str(cert_file),
                "-days", "365",
                "-nodes",
                "-subj", f"/C=US/ST=CA/L=San Francisco/O=YatinVeda/CN={domain}"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Set appropriate permissions
                os.chmod(key_file, 0o600)
                os.chmod(cert_file, 0o644)
                
                return CertificateResult(
                    success=True,
                    certificate_path=str(cert_file),
                    private_key_path=str(key_file)
                )
            else:
                error_msg = stderr.decode() if stderr else "Unknown OpenSSL error"
                return CertificateResult(
                    success=False,
                    error_message=f"OpenSSL failed: {error_msg}"
                )
                
        except Exception as e:
            return CertificateResult(
                success=False,
                error_message=f"Self-signed certificate generation failed: {str(e)}"
            )
    
    async def _renew_letsencrypt_certificate(self, domain: str) -> CertificateResult:
        """Renew Let's Encrypt certificate"""
        try:
            certbot_cmd = await self._find_certbot_command()
            if not certbot_cmd:
                return CertificateResult(
                    success=False,
                    error_message="Certbot not found for certificate renewal"
                )
            
            cmd = [
                certbot_cmd,
                "renew",
                "--cert-name", domain,
                "--non-interactive"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                await self._organize_letsencrypt_certificates(domain)
                
                return CertificateResult(
                    success=True,
                    certificate_path=str(self.cert_path / f"{domain}.crt"),
                    private_key_path=str(self.key_path / f"{domain}.key")
                )
            else:
                error_msg = stderr.decode() if stderr else "Unknown certbot renewal error"
                return CertificateResult(
                    success=False,
                    error_message=f"Certbot renewal failed: {error_msg}"
                )
                
        except Exception as e:
            return CertificateResult(
                success=False,
                error_message=f"Let's Encrypt renewal failed: {str(e)}"
            )
    
    async def _find_certbot_command(self) -> Optional[str]:
        """Find certbot command in system PATH"""
        for cmd in ["certbot", "certbot-auto", "/usr/bin/certbot", "/usr/local/bin/certbot"]:
            try:
                process = await asyncio.create_subprocess_exec(
                    "which", cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await process.communicate()
                
                if process.returncode == 0:
                    return cmd
            except:
                continue
        
        return None
    
    async def _organize_letsencrypt_certificates(self, domain: str):
        """Organize Let's Encrypt certificates into our directory structure"""
        # Let's Encrypt typically stores certificates in /etc/letsencrypt/live/
        letsencrypt_live = Path("/etc/letsencrypt/live") / domain
        
        if letsencrypt_live.exists():
            # Copy certificate files
            cert_source = letsencrypt_live / "fullchain.pem"
            key_source = letsencrypt_live / "privkey.pem"
            
            cert_dest = self.cert_path / f"{domain}.crt"
            key_dest = self.key_path / f"{domain}.key"
            
            if cert_source.exists():
                async with aiofiles.open(cert_source, 'rb') as src:
                    content = await src.read()
                async with aiofiles.open(cert_dest, 'wb') as dst:
                    await dst.write(content)
            
            if key_source.exists():
                async with aiofiles.open(key_source, 'rb') as src:
                    content = await src.read()
                async with aiofiles.open(key_dest, 'wb') as dst:
                    await dst.write(content)
                
                # Set secure permissions for private key
                os.chmod(key_dest, 0o600)
    
    async def _extract_certificate_info(self, cert_file: Path) -> Optional[Tuple[datetime, str, str]]:
        """Extract certificate information using OpenSSL"""
        try:
            # Get certificate expiration date
            cmd = ["openssl", "x509", "-in", str(cert_file), "-noout", "-enddate"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            
            if process.returncode != 0:
                return None
            
            # Parse expiration date
            enddate_line = stdout.decode().strip()
            date_str = enddate_line.split("=")[1]
            expiration_date = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
            
            # Get issuer
            cmd = ["openssl", "x509", "-in", str(cert_file), "-noout", "-issuer"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            
            issuer = "Unknown"
            if process.returncode == 0:
                issuer_line = stdout.decode().strip()
                issuer = issuer_line.split("=", 1)[1] if "=" in issuer_line else issuer_line
            
            # Get subject
            cmd = ["openssl", "x509", "-in", str(cert_file), "-noout", "-subject"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            
            subject = "Unknown"
            if process.returncode == 0:
                subject_line = stdout.decode().strip()
                subject = subject_line.split("=", 1)[1] if "=" in subject_line else subject_line
            
            return expiration_date, issuer, subject
            
        except Exception as e:
            logger.error(f"Error extracting certificate info: {str(e)}")
            return None
    
    async def _backup_certificate(self, domain: str):
        """Backup existing certificate before renewal"""
        try:
            cert_file = self.cert_path / f"{domain}.crt"
            key_file = self.key_path / f"{domain}.key"
            
            backup_dir = self.cert_path / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            if cert_file.exists():
                backup_cert = backup_dir / f"{domain}_{timestamp}.crt"
                async with aiofiles.open(cert_file, 'rb') as src:
                    content = await src.read()
                async with aiofiles.open(backup_cert, 'wb') as dst:
                    await dst.write(content)
            
            if key_file.exists():
                backup_key = backup_dir / f"{domain}_{timestamp}.key"
                async with aiofiles.open(key_file, 'rb') as src:
                    content = await src.read()
                async with aiofiles.open(backup_key, 'wb') as dst:
                    await dst.write(content)
                os.chmod(backup_key, 0o600)
                
        except Exception as e:
            logger.warning(f"Failed to backup certificate for {domain}: {str(e)}")
    
    async def _restore_certificate_backup(self, domain: str):
        """Restore certificate from backup if renewal fails"""
        try:
            backup_dir = self.cert_path / "backups"
            
            # Find most recent backup
            backup_files = list(backup_dir.glob(f"{domain}_*.crt"))
            if not backup_files:
                return
            
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            timestamp = latest_backup.stem.split("_", 1)[1]
            
            backup_cert = backup_dir / f"{domain}_{timestamp}.crt"
            backup_key = backup_dir / f"{domain}_{timestamp}.key"
            
            cert_file = self.cert_path / f"{domain}.crt"
            key_file = self.key_path / f"{domain}.key"
            
            if backup_cert.exists():
                async with aiofiles.open(backup_cert, 'rb') as src:
                    content = await src.read()
                async with aiofiles.open(cert_file, 'wb') as dst:
                    await dst.write(content)
            
            if backup_key.exists():
                async with aiofiles.open(backup_key, 'rb') as src:
                    content = await src.read()
                async with aiofiles.open(key_file, 'wb') as dst:
                    await dst.write(content)
                os.chmod(key_file, 0o600)
                
            logger.info(f"Restored certificate backup for {domain}")
            
        except Exception as e:
            logger.error(f"Failed to restore certificate backup for {domain}: {str(e)}")
    
    async def _update_certificate_cache(self, domain: str):
        """Update certificate status cache"""
        try:
            status = await self.get_certificate_status(domain)
            self._certificate_cache[domain] = status
        except Exception as e:
            logger.warning(f"Failed to update certificate cache for {domain}: {str(e)}")
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Validate domain name format"""
        if not domain or len(domain) > 253:
            return False
        
        # Allow localhost and IP addresses for development
        if domain in ["localhost", "127.0.0.1"] and self.environment == "development":
            return True
        
        # Basic domain validation
        import re
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, domain))


# Global certificate manager instance
certificate_manager: Optional[CertificateManager] = None


def get_certificate_manager() -> CertificateManager:
    """Get global certificate manager instance"""
    global certificate_manager
    
    if certificate_manager is None:
        # Initialize with environment-specific settings
        environment = os.getenv("ENVIRONMENT", "development")
        cert_provider = os.getenv("CERT_PROVIDER", "self-signed" if environment == "development" else "letsencrypt")
        
        certificate_manager = CertificateManager(
            cert_provider=cert_provider,
            cert_path=os.getenv("CERT_PATH", "/etc/ssl/certs"),
            key_path=os.getenv("KEY_PATH", "/etc/ssl/private"),
            renewal_days=int(os.getenv("CERT_RENEWAL_DAYS", "30")),
            environment=environment
        )
    
    return certificate_manager


async def initialize_certificates():
    """Initialize certificates for all configured domains"""
    manager = get_certificate_manager()
    
    domains = manager.config.get("domains", [])
    if not domains:
        logger.warning("No domains configured for certificate management")
        return
    
    logger.info(f"Initializing certificates for domains: {domains}")
    
    for domain in domains:
        try:
            result = await manager.provision_certificate(domain)
            if result.success:
                logger.info(f"Certificate ready for {domain}")
            else:
                logger.error(f"Failed to initialize certificate for {domain}: {result.error_message}")
                
                # In production, this should prevent startup
                if manager.environment == "production" and manager.config.get("validation_required", False):
                    raise RuntimeError(f"Certificate initialization failed for {domain}: {result.error_message}")
                    
        except Exception as e:
            logger.error(f"Error initializing certificate for {domain}: {str(e)}")
            
            if manager.environment == "production":
                raise


async def _alert_cert_renewal_failure(domain: str, error_message: str) -> None:
    """Send a security alert when certificate renewal fails."""
    try:
        from middleware.security_monitor import get_security_monitor, ThreatAlert, SecuritySeverity
        import uuid

        monitor = get_security_monitor()
        now = datetime.utcnow()
        alert = ThreatAlert(
            id=str(uuid.uuid4()),
            alert_type="certificate_renewal_failure",
            severity=SecuritySeverity.HIGH,
            description=f"Certificate renewal failed for {domain}: {error_message}",
            affected_ips=[],
            event_count=1,
            time_window=timedelta(seconds=0),
            first_seen=now,
            last_seen=now,
            recommended_action="Manually renew the certificate or check ACME provider connectivity",
        )
        await monitor._send_alert(alert)
    except Exception as e:
        logger.error(f"Failed to send cert renewal alert for {domain}: {e}")


async def check_and_renew_certificates():
    """Check and renew certificates that are expiring"""
    manager = get_certificate_manager()
    
    try:
        domains_needing_renewal = await manager.check_renewal_needed()
        
        if not domains_needing_renewal:
            logger.info("No certificates need renewal")
            return
        
        logger.info(f"Renewing certificates for domains: {domains_needing_renewal}")
        
        for domain in domains_needing_renewal:
            try:
                result = await manager.renew_certificate(domain)
                if result.success:
                    logger.info(f"Successfully renewed certificate for {domain}")
                else:
                    logger.error(f"Failed to renew certificate for {domain}: {result.error_message}")
                    
                    await _alert_cert_renewal_failure(domain, result.error_message)
                    
            except Exception as e:
                logger.error(f"Error renewing certificate for {domain}: {str(e)}")
                await _alert_cert_renewal_failure(domain, str(e))
                
    except Exception as e:
        logger.error(f"Error checking certificate renewals: {str(e)}")


if __name__ == "__main__":
    # Test certificate manager
    import asyncio
    
    async def test_certificate_manager():
        manager = CertificateManager(environment="development")
        
        # Test self-signed certificate generation
        result = await manager.provision_certificate("localhost")
        print(f"Provision result: {result}")
        
        # Test certificate validation
        validation = await manager.validate_certificate("localhost")
        print(f"Validation result: {validation}")
        
        # Test certificate status
        status = await manager.get_certificate_status("localhost")
        print(f"Certificate status: {status}")
    
    asyncio.run(test_certificate_manager())