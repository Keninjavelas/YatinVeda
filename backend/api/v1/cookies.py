"""Cookie consent management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import logging

from database import get_db
from modules.auth import get_current_user, get_current_user_optional
from models.database import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cookies", tags=["Cookie Consent"])


class CookiePreferences(BaseModel):
    """Cookie preference settings."""
    essential_cookies: bool = True  # Always true, cannot be disabled
    functional_cookies: bool = False
    analytics_cookies: bool = False
    marketing_cookies: bool = False


class LegalConsent(BaseModel):
    """Legal consent record."""
    consent_type: str  # 'terms', 'privacy', 'cookies', 'marketing'
    consent_version: str  # e.g., '1.0.0'


@router.get("/preferences")
async def get_cookie_preferences(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's cookie preferences.
    
    Returns defaults if user is not authenticated or has not set preferences.
    """
    try:
        if not current_user:
            # Return default preferences for anonymous users
            return {
                "essential_cookies": True,
                "functional_cookies": False,
                "analytics_cookies": False,
                "marketing_cookies": False,
                "is_configured": False
            }
        
        from models.database import CookiePreference
        
        # Get user's cookie preferences
        query = select(CookiePreference).where(
            CookiePreference.user_id == current_user.id
        )
        result = await db.execute(query)
        prefs = result.scalar_one_or_none()
        
        if prefs:
            return {
                "essential_cookies": prefs.essential_cookies,
                "functional_cookies": prefs.functional_cookies,
                "analytics_cookies": prefs.analytics_cookies,
                "marketing_cookies": prefs.marketing_cookies,
                "is_configured": True,
                "updated_at": prefs.updated_at
            }
        else:
            # User  has not set preferences yet
            return {
                "essential_cookies": True,
                "functional_cookies": False,
                "analytics_cookies": False,
                "marketing_cookies": False,
                "is_configured": False
            }
            
    except Exception as e:
        logger.error(f"Error fetching cookie preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch cookie preferences")


@router.post("/preferences")
async def update_cookie_preferences(
    preferences: CookiePreferences,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user's cookie preferences.
    
    Can be called by authenticated or anonymous users.
    For anonymous users, preferences are stored in browser local storage.
    """
    try:
        # Ensure essential cookies are always enabled
        if not preferences.essential_cookies:
            preferences.essential_cookies = True
        
        if current_user:
            from models.database import CookiePreference
            
            # Check if preferences exist
            query = select(CookiePreference).where(
                CookiePreference.user_id == current_user.id
            )
            result = await db.execute(query)
            prefs = result.scalar_one_or_none()
            
            if prefs:
                # Update existing preferences
                prefs.essential_cookies = preferences.essential_cookies
                prefs.functional_cookies = preferences.functional_cookies
                prefs.analytics_cookies = preferences.analytics_cookies
                prefs.marketing_cookies = preferences.marketing_cookies
                prefs.updated_at = datetime.utcnow()
            else:
                # Create new preferences
                prefs = CookiePreference(
                    user_id=current_user.id,
                    essential_cookies=preferences.essential_cookies,
                    functional_cookies=preferences.functional_cookies,
                    analytics_cookies=preferences.analytics_cookies,
                    marketing_cookies=preferences.marketing_cookies,
                    updated_at=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                db.add(prefs)
            
            await db.commit()
            await db.refresh(prefs)
            
            return {
                "message": "Cookie preferences updated successfully",
                "preferences": {
                    "essential_cookies": prefs.essential_cookies,
                    "functional_cookies": prefs.functional_cookies,
                    "analytics_cookies": prefs.analytics_cookies,
                    "marketing_cookies": prefs.marketing_cookies,
                    "updated_at": prefs.updated_at
                }
            }
        else:
            # For anonymous users, return the preferences to be stored client-side
            return {
                "message": "Cookie preferences received",
                "preferences": preferences.dict(),
                "note": "Preferences will be stored in browser until you create an account"
            }
            
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating cookie preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update cookie preferences")


@router.post("/consent")
async def record_legal_consent(
    consent: LegalConsent,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Record user's consent to legal documents (GDPR compliance).
    
    This creates an audit trail of when users accepted Terms, Privacy Policy, etc.
    """
    try:
        from models.database import LegalConsent as LegalConsentModel
        
        # Validate consent type
        valid_types = ['terms', 'privacy', 'cookies', 'marketing']
        if consent.consent_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid consent type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Create consent record
        consent_record = LegalConsentModel(
            user_id=current_user.id,
            consent_type=consent.consent_type,
            consent_version=consent.consent_version,
            consented_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        db.add(consent_record)
        await db.commit()
        await db.refresh(consent_record)
        
        return {
            "message": f"Consent to {consent.consent_type} recorded successfully",
            "consent_id": consent_record.id,
            "consented_at": consent_record.consented_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error recording legal consent: {e}")
        raise HTTPException(status_code=500, detail="Failed to record consent")


@router.get("/consent/history")
async def get_consent_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's consent history.
    
    Shows all legal documents the user has consented to.
    """
    try:
        from models.database import LegalConsent as LegalConsentModel
        
        query = select(LegalConsentModel).where(
            LegalConsentModel.user_id == current_user.id
        ).order_by(LegalConsentModel.consented_at.desc())
        
        result = await db.execute(query)
        consents = result.scalars().all()
        
        return {
            "consents": [
                {
                    "consent_type": c.consent_type,
                    "consent_version": c.consent_version,
                    "consented_at": c.consented_at,
                    "withdrawn_at": c.withdrawn_at,
                    "is_active": c.withdrawn_at is None
                }
                for c in consents
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching consent history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch consent history")


@router.post("/consent/{consent_type}/withdraw")
async def withdraw_consent(
    consent_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Withdraw consent for a specific type.
    
    Note: Withdrawing consent for essential services may result in restricted access.
    """
    try:
        from models.database import LegalConsent as LegalConsentModel
        
        # Find most recent active consent of this type
        query = select(LegalConsentModel).where(
            LegalConsentModel.user_id == current_user.id,
            LegalConsentModel.consent_type == consent_type,
            LegalConsentModel.withdrawn_at.is_(None)
        ).order_by(LegalConsentModel.consented_at.desc())
        
        result = await db.execute(query)
        consent = result.scalar_one_or_none()
        
        if not consent:
            raise HTTPException(
                status_code=404,
                detail=f"No active consent found for type: {consent_type}"
            )
        
        # Mark as withdrawn
        consent.withdrawn_at = datetime.utcnow()
        await db.commit()
        
        warning = None
        if consent_type in ['terms', 'privacy']:
            warning = "Withdrawing consent may restrict your access to certain features or services."
        
        return {
            "message": f"Consent to {consent_type} withdrawn successfully",
            "withdrawn_at": consent.withdrawn_at,
            "warning": warning
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error withdrawing consent: {e}")
        raise HTTPException(status_code=500, detail="Failed to withdraw consent")


@router.get("/policy/{policy_type}")
async def get_policy_document(policy_type: str):
    """
    Get the current version of a legal policy document.
    
    Available policies: terms, privacy, cookies
    """
    policy_files = {
        'terms': 'docs/legal/TERMS_OF_SERVICE.md',
        'privacy': 'docs/legal/PRIVACY_POLICY.md',
        'cookies': 'docs/legal/COOKIE_POLICY.md'
    }
    
    if policy_type not in policy_files:
        raise HTTPException(
            status_code=404,
            detail=f"Policy type not found. Available: {', '.join(policy_files.keys())}"
        )
    
    try:
        # Read policy file
        with open(policy_files[policy_type], 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "policy_type": policy_type,
            "version": "1.0.0",
            "last_updated": "2026-03-10",
            "content": content,
            "format": "markdown"
        }
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Policy document not found: {policy_type}"
        )
    except Exception as e:
        logger.error(f"Error reading policy document: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve policy document")
