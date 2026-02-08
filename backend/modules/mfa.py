"""
Multi-Factor Authentication (MFA) Module

Provides TOTP-based 2FA with smooth user experience:
- QR code generation for easy authenticator app setup
- Backup codes for account recovery
- Trusted device management (skip MFA for 30 days)
- User-friendly device naming
"""

import base64
import hashlib
import io
import os
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import pyotp
import qrcode
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from models.database import MFABackupCode, MFASettings, TrustedDevice, User
from modules.auth import SECRET_KEY


class MFAManager:
    """Manages Multi-Factor Authentication operations"""

    BACKUP_CODE_COUNT = 8
    BACKUP_CODE_LENGTH = 10
    TRUSTED_DEVICE_DAYS = 30

    def __init__(self, db: Session):
        self.db = db
        self._fernet = self._build_fernet()

    # ==================== Setup & Configuration ====================

    def setup_mfa(self, user: User) -> Tuple[str, str, List[str]]:
        """
        Initialize MFA for a user (does not enable yet).

        Returns:
            Tuple of (secret_key, qr_code_base64, backup_codes)
        """
        # Check if MFA settings already exist
        existing = self.db.query(MFASettings).filter_by(user_id=user.id).first()
        if existing:
            # Regenerate secret and backup codes
            secret_key = pyotp.random_base32()
            existing.secret_key = self._encrypt_secret(secret_key)
            existing.is_enabled = False
            existing.verified_at = None
        else:
            # Create new MFA settings
            secret_key = pyotp.random_base32()
            mfa_settings = MFASettings(
                user_id=user.id,
                secret_key=self._encrypt_secret(secret_key),
                is_enabled=False
            )
            self.db.add(mfa_settings)

        # Generate QR code
        qr_code = self._generate_qr_code(user.email, secret_key)

        # Generate backup codes
        backup_codes = self._generate_backup_codes(user.id)

        self.db.commit()

        return secret_key, qr_code, backup_codes

    def enable_mfa(self, user: User, verification_code: str) -> bool:
        """
        Enable MFA after verifying the setup code.

        Args:
            user: User object
            verification_code: 6-digit TOTP code from authenticator app

        Returns:
            True if enabled successfully, False if verification failed
        """
        mfa_settings = self.db.query(MFASettings).filter_by(user_id=user.id).first()
        if not mfa_settings:
            return False

        # Verify the code
        if self.verify_totp(user, verification_code):
            mfa_settings.is_enabled = True
            mfa_settings.verified_at = datetime.utcnow()
            self.db.commit()
            return True

        return False

    def disable_mfa(self, user: User, verification_code: Optional[str] = None) -> bool:
        """
        Disable MFA for a user.

        Args:
            user: User object
            verification_code: Optional TOTP code for verification

        Returns:
            True if disabled successfully
        """
        mfa_settings = self.db.query(MFASettings).filter_by(user_id=user.id).first()
        if not mfa_settings:
            return False

        # If MFA is enabled, require verification
        if mfa_settings.is_enabled and verification_code:
            if not self.verify_totp(user, verification_code):
                return False

        mfa_settings.is_enabled = False
        mfa_settings.verified_at = None

        # Clear all trusted devices
        self.db.query(TrustedDevice).filter_by(mfa_settings_id=mfa_settings.id).delete()

        self.db.commit()
        return True

    # ==================== Verification ====================

    def verify_totp(self, user: User, code: str) -> bool:
        """
        Verify a TOTP code.

        Args:
            user: User object
            code: 6-digit TOTP code

        Returns:
            True if code is valid
        """
        mfa_settings = self.db.query(MFASettings).filter_by(user_id=user.id).first()
        if not mfa_settings:
            return False

        secret = self._decrypt_secret(mfa_settings.secret_key)
        totp = pyotp.TOTP(secret)
        # Allow 1 interval before/after for clock drift (30-second window)
        return totp.verify(code, valid_window=1)

    def verify_backup_code(self, user: User, code: str) -> bool:
        """
        Verify and consume a backup code.

        Args:
            user: User object
            code: 10-character backup code

        Returns:
            True if code is valid and not used
        """
        code_hash = self._hash_backup_code(code)

        backup_code = (
            self.db.query(MFABackupCode)
            .filter_by(user_id=user.id, code_hash=code_hash, used_at=None)
            .first()
        )

        if backup_code:
            backup_code.used_at = datetime.utcnow()
            self.db.commit()
            return True

        return False

    def verify_mfa(self, user: User, code: str) -> bool:
        """
        Verify MFA using either TOTP or backup code.

        Args:
            user: User object
            code: TOTP or backup code

        Returns:
            True if verification successful
        """
        # Try TOTP first (6 digits)
        if len(code) == 6 and code.isdigit():
            return self.verify_totp(user, code)

        # Try backup code (10 characters)
        if len(code) == 10:
            return self.verify_backup_code(user, code)

        return False

    # ==================== Trusted Devices ====================

    def is_device_trusted(self, user: User, device_fingerprint: str) -> bool:
        """
        Check if a device is trusted and not expired.

        Args:
            user: User object
            device_fingerprint: Hash of device info (user-agent + IP pattern)

        Returns:
            True if device is trusted
        """
        mfa_settings = self.db.query(MFASettings).filter_by(user_id=user.id).first()
        if not mfa_settings:
            return False

        trusted_device = (
            self.db.query(TrustedDevice)
            .filter(
                TrustedDevice.mfa_settings_id == mfa_settings.id,
                TrustedDevice.device_fingerprint == device_fingerprint,
                TrustedDevice.expires_at > datetime.utcnow()
            )
            .first()
        )

        if trusted_device:
            # Update last used timestamp
            trusted_device.last_used_at = datetime.utcnow()
            self.db.commit()
            return True

        return False

    def trust_device(
        self,
        user: User,
        device_fingerprint: str,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TrustedDevice:
        """
        Mark a device as trusted for 30 days.

        Args:
            user: User object
            device_fingerprint: Hash of device info
            device_name: User-friendly device name
            ip_address: Device IP address
            user_agent: Device user agent

        Returns:
            TrustedDevice object
        """
        mfa_settings = self.db.query(MFASettings).filter_by(user_id=user.id).first()
        if not mfa_settings:
            raise ValueError("MFA not set up for user")

        # Check if device already exists
        existing = (
            self.db.query(TrustedDevice)
            .filter_by(mfa_settings_id=mfa_settings.id, device_fingerprint=device_fingerprint)
            .first()
        )

        if existing:
            # Update existing device
            existing.expires_at = datetime.utcnow() + timedelta(days=self.TRUSTED_DEVICE_DAYS)
            existing.last_used_at = datetime.utcnow()
            existing.ip_address = ip_address
            existing.user_agent = user_agent
            self.db.commit()
            return existing

        # Create new trusted device
        trusted_device = TrustedDevice(
            mfa_settings_id=mfa_settings.id,
            device_fingerprint=device_fingerprint,
            device_name=device_name or self._generate_device_name(user_agent),
            expires_at=datetime.utcnow() + timedelta(days=self.TRUSTED_DEVICE_DAYS),
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(trusted_device)
        self.db.commit()
        self.db.refresh(trusted_device)

        return trusted_device

    def revoke_device(self, user: User, device_id: int) -> bool:
        """
        Revoke trust for a specific device.

        Args:
            user: User object
            device_id: TrustedDevice ID

        Returns:
            True if device was revoked
        """
        mfa_settings = self.db.query(MFASettings).filter_by(user_id=user.id).first()
        if not mfa_settings:
            return False

        device = (
            self.db.query(TrustedDevice)
            .filter_by(id=device_id, mfa_settings_id=mfa_settings.id)
            .first()
        )

        if device:
            self.db.delete(device)
            self.db.commit()
            return True

        return False

    def list_trusted_devices(self, user: User) -> List[TrustedDevice]:
        """Get all trusted devices for a user."""
        mfa_settings = self.db.query(MFASettings).filter_by(user_id=user.id).first()
        if not mfa_settings:
            return []

        return (
            self.db.query(TrustedDevice)
            .filter(
                TrustedDevice.mfa_settings_id == mfa_settings.id,
                TrustedDevice.expires_at > datetime.utcnow()
            )
            .order_by(TrustedDevice.last_used_at.desc())
            .all()
        )

    # ==================== Backup Codes ====================

    def regenerate_backup_codes(self, user: User) -> List[str]:
        """
        Generate new backup codes (invalidates old ones).

        Args:
            user: User object

        Returns:
            List of new backup codes
        """
        # Delete old backup codes
        self.db.query(MFABackupCode).filter_by(user_id=user.id).delete()

        # Generate new codes
        backup_codes = self._generate_backup_codes(user.id)

        self.db.commit()

        return backup_codes

    def get_backup_codes_status(self, user: User) -> dict:
        """
        Get backup codes usage statistics.

        Returns:
            Dict with total, used, and remaining counts
        """
        codes = self.db.query(MFABackupCode).filter_by(user_id=user.id).all()

        total = len(codes)
        used = sum(1 for code in codes if code.used_at is not None)
        remaining = total - used

        return {
            "total": total,
            "used": used,
            "remaining": remaining
        }

    # ==================== Status Check ====================

    def is_mfa_enabled(self, user: User) -> bool:
        """Check if MFA is enabled for a user."""
        mfa_settings = self.db.query(MFASettings).filter_by(user_id=user.id).first()
        return mfa_settings.is_enabled if mfa_settings else False

    def get_mfa_settings(self, user: User) -> Optional[MFASettings]:
        """Get MFA settings for a user."""
        return self.db.query(MFASettings).filter_by(user_id=user.id).first()

    # ==================== Helper Methods ====================

    def _build_fernet(self) -> Fernet:
        """Build Fernet instance; derive key from MFA_ENCRYPTION_KEY or SECRET_KEY."""
        key_env = os.getenv("MFA_ENCRYPTION_KEY")

        def derive(key_material: str) -> bytes:
            return base64.urlsafe_b64encode(hashlib.sha256(key_material.encode()).digest())

        if key_env:
            try:
                return Fernet(key_env)
            except Exception:
                return Fernet(derive(key_env))

        return Fernet(derive(SECRET_KEY))

    def _encrypt_secret(self, secret: str) -> str:
        """Encrypt TOTP secret; fallback to plain on failure for compatibility."""
        if not secret:
            return secret
        try:
            return self._fernet.encrypt(secret.encode()).decode()
        except Exception:
            return secret

    def _decrypt_secret(self, secret: str) -> str:
        """Decrypt stored secret; returns original if not encrypted or invalid."""
        if not secret:
            return secret
        try:
            return self._fernet.decrypt(secret.encode()).decode()
        except InvalidToken:
            return secret
        except Exception:
            return secret

    def _generate_qr_code(self, email: str, secret_key: str) -> str:
        """
        Generate QR code for authenticator app.

        Returns:
            Base64-encoded PNG image
        """
        totp = pyotp.TOTP(secret_key)
        provisioning_uri = totp.provisioning_uri(
            name=email,
            issuer_name="YatinVeda"
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return img_str

    def _generate_backup_codes(self, user_id: int) -> List[str]:
        """
        Generate and store backup codes.

        Returns:
            List of plaintext backup codes (show to user once)
        """
        codes = []

        for _ in range(self.BACKUP_CODE_COUNT):
            # Generate random alphanumeric code
            code = ''.join(
                secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789')
                for _ in range(self.BACKUP_CODE_LENGTH)
            )
            codes.append(code)

            # Store hashed version
            code_hash = self._hash_backup_code(code)
            backup_code = MFABackupCode(
                user_id=user_id,
                code_hash=code_hash
            )
            self.db.add(backup_code)

        return codes

    def _hash_backup_code(self, code: str) -> str:
        """Hash a backup code using SHA-256."""
        return hashlib.sha256(code.encode()).hexdigest()

    def _generate_device_name(self, user_agent: Optional[str]) -> str:
        """Generate a user-friendly device name from user agent."""
        if not user_agent:
            return "Unknown Device"

        user_agent = user_agent.lower()

        # Detect browser
        browser = "Browser"
        if "chrome" in user_agent and "edg" not in user_agent:
            browser = "Chrome"
        elif "firefox" in user_agent:
            browser = "Firefox"
        elif "safari" in user_agent and "chrome" not in user_agent:
            browser = "Safari"
        elif "edg" in user_agent:
            browser = "Edge"

        # Detect OS
        os = "Unknown OS"
        if "windows" in user_agent:
            os = "Windows"
        elif "mac" in user_agent:
            os = "macOS"
        elif "linux" in user_agent:
            os = "Linux"
        elif "android" in user_agent:
            os = "Android"
        elif "iphone" in user_agent or "ipad" in user_agent:
            os = "iOS"

        return f"{browser} on {os}"

    @staticmethod
    def generate_device_fingerprint(user_agent: str, ip_address: str) -> str:
        """
        Generate a device fingerprint from user agent and IP.

        Note: Uses IP subnet (first 3 octets) to handle dynamic IPs.
        """
        # Extract IP subnet (e.g., "192.168.1.x" -> "192.168.1")
        ip_parts = ip_address.split(".")
        ip_subnet = ".".join(ip_parts[:3]) if len(ip_parts) == 4 else ip_address

        # Combine user agent and IP subnet
        fingerprint_data = f"{user_agent}:{ip_subnet}"

        # Hash to create fingerprint
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
