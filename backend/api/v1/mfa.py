"""
Multi-Factor Authentication (MFA) API endpoints

Provides a smooth MFA experience:
- Easy QR code setup
- Backup codes for recovery
- Trusted device management (skip MFA for 30 days)
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.database import User
from modules.auth import get_current_user
from modules.mfa import MFAManager

router = APIRouter(prefix="/api/v1/mfa", tags=["Multi-Factor Authentication"])


# ==================== Schemas ====================

class MFASetupResponse(BaseModel):
    """Response after initiating MFA setup"""
    qr_code: str = Field(..., description="Base64-encoded QR code image")
    secret_key: str = Field(..., description="Manual entry key (for apps without camera)")
    backup_codes: List[str] = Field(..., description="One-time backup codes (save securely)")


class MFAEnableRequest(BaseModel):
    """Request to enable MFA"""
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA code during login"""
    code: str = Field(..., description="6-digit TOTP or 10-character backup code")
    trust_device: bool = Field(default=False, description="Remember this device for 30 days")


class MFADisableRequest(BaseModel):
    """Request to disable MFA"""
    code: Optional[str] = Field(None, description="6-digit TOTP code for verification")


class TrustedDeviceResponse(BaseModel):
    """Trusted device information"""
    id: int
    device_name: str
    trusted_at: datetime
    expires_at: datetime
    last_used_at: datetime
    ip_address: Optional[str]

    class Config:
        from_attributes = True


class BackupCodesStatusResponse(BaseModel):
    """Backup codes usage status"""
    total: int
    used: int
    remaining: int


class MFAStatusResponse(BaseModel):
    """Current MFA status"""
    is_enabled: bool
    verified_at: Optional[datetime]
    backup_codes_status: Optional[BackupCodesStatusResponse]
    trusted_devices_count: int


# ==================== Endpoints ====================

@router.get("/status", response_model=MFAStatusResponse)
async def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current MFA configuration status.

    Returns MFA enabled state, backup codes status, and trusted device count.
    """
    mfa_manager = MFAManager(db)
    mfa_settings = mfa_manager.get_mfa_settings(current_user)

    if not mfa_settings:
        return MFAStatusResponse(
            is_enabled=False,
            verified_at=None,
            backup_codes_status=None,
            trusted_devices_count=0
        )

    backup_codes_status = mfa_manager.get_backup_codes_status(current_user)
    trusted_devices = mfa_manager.list_trusted_devices(current_user)

    return MFAStatusResponse(
        is_enabled=mfa_settings.is_enabled,
        verified_at=mfa_settings.verified_at,
        backup_codes_status=BackupCodesStatusResponse(**backup_codes_status),
        trusted_devices_count=len(trusted_devices)
    )


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize MFA setup for the user.

    Returns:
        - QR code for authenticator apps (Google Authenticator, Authy, etc.)
        - Secret key for manual entry
        - Backup codes for recovery (save these securely!)

    Note: MFA is not enabled until you verify the code with /mfa/enable
    """
    mfa_manager = MFAManager(db)

    # Check if MFA is already enabled
    if mfa_manager.is_mfa_enabled(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled. Disable it first to reconfigure."
        )

    # Fetch the full User ORM model (setup_mfa needs user.email for QR code)
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    secret_key, qr_code, backup_codes = mfa_manager.setup_mfa(user)

    return MFASetupResponse(
        qr_code=qr_code,
        secret_key=secret_key,
        backup_codes=backup_codes
    )


@router.post("/enable")
async def enable_mfa(
    request: MFAEnableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enable MFA after scanning QR code.

    Submit a code from your authenticator app to verify the setup.
    """
    mfa_manager = MFAManager(db)

    # Check if MFA is already enabled
    if mfa_manager.is_mfa_enabled(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled"
        )

    # Verify and enable
    success = mfa_manager.enable_mfa(current_user, request.code)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please try again."
        )

    return {
        "message": "MFA enabled successfully! Your account is now more secure.",
        "is_enabled": True
    }


@router.post("/disable")
async def disable_mfa(
    request: MFADisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disable MFA for the account.

    Requires TOTP code verification if MFA is currently enabled.
    """
    mfa_manager = MFAManager(db)

    success = mfa_manager.disable_mfa(current_user, request.code)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to disable MFA. Invalid verification code or MFA not set up."
        )

    return {
        "message": "MFA disabled successfully",
        "is_enabled": False
    }


@router.post("/backup-codes/regenerate", response_model=List[str])
async def regenerate_backup_codes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate new backup codes (invalidates old ones).

    WARNING: Save these codes securely! They won't be shown again.
    Old backup codes will stop working.
    """
    mfa_manager = MFAManager(db)

    if not mfa_manager.is_mfa_enabled(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )

    backup_codes = mfa_manager.regenerate_backup_codes(current_user)

    return backup_codes


@router.get("/backup-codes/status", response_model=BackupCodesStatusResponse)
async def get_backup_codes_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get backup codes usage statistics.

    Shows how many backup codes are remaining (without revealing the codes).
    """
    mfa_manager = MFAManager(db)

    if not mfa_manager.is_mfa_enabled(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )

    status_data = mfa_manager.get_backup_codes_status(current_user)

    return BackupCodesStatusResponse(**status_data)


@router.get("/devices", response_model=List[TrustedDeviceResponse])
async def list_trusted_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all trusted devices.

    Trusted devices skip MFA for 30 days from last use.
    """
    mfa_manager = MFAManager(db)

    if not mfa_manager.is_mfa_enabled(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )

    devices = mfa_manager.list_trusted_devices(current_user)

    return [
        TrustedDeviceResponse(
            id=device.id,
            device_name=device.device_name,
            trusted_at=device.trusted_at,
            expires_at=device.expires_at,
            last_used_at=device.last_used_at,
            ip_address=device.ip_address
        )
        for device in devices
    ]


@router.delete("/devices/{device_id}")
async def revoke_trusted_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke trust for a specific device.

    That device will require MFA on next login.
    """
    mfa_manager = MFAManager(db)

    success = mfa_manager.revoke_device(current_user, device_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    return {
        "message": "Device trust revoked successfully"
    }
