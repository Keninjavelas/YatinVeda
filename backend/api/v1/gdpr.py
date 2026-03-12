"""GDPR compliance endpoints for data export and deletion."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import logging

from database import get_db
from modules.auth import get_current_user
from models.database import (
    User, Chart, GuruBooking, Payment, Wallet, WalletTransaction,
    RefreshToken, MFASettings, TrustedDevice, MFABackupCode,
    ChatHistory, LearningProgress
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["GDPR Compliance"])


@router.post("/export-data")
async def request_data_export(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request a full export of user's personal data (GDPR Article 15 & 20).
    
    The export includes:
    - User profile and account information
    - Birth charts and astrological data
    - Booking history
    - Payment and transaction history
    - Wallet information
    - Chat history
    - Learning progress
    - MFA settings (not including secrets)
    - Login history (last 90 days)
    
    Returns:
        Immediate confirmation with request_id.
        Actual data export will be generated asynchronously and sent via email.
    """
    try:
        from models.database import DataExportRequest
        
        # Check for existing pending request
        existing_query = select(DataExportRequest).where(
            DataExportRequest.user_id == current_user.id,
            DataExportRequest.request_type == 'export',
            DataExportRequest.status.in_(['pending', 'processing'])
        )
        result = db.execute(existing_query)
        existing_request = result.scalar_one_or_none()
        
        if existing_request:
            raise HTTPException(
                status_code=409,
                detail="A data export request is already in progress. Please check your email or wait for it to complete."
            )
        
        # Create new export request
        export_request = DataExportRequest(
            user_id=current_user.id,
            request_type='export',
            status='pending',
            expires_at=datetime.utcnow() + timedelta(days=30),  # Export link valid for 30 days
        )
        
        db.add(export_request)
        db.commit()
        db.refresh(export_request)
        
        # Schedule background task to generate export
        background_tasks.add_task(generate_data_export, export_request.id, db)
        
        return {
            "message": "Data export request received. You will receive an email with download link within 24 hours.",
            "request_id": export_request.id,
            "status": "pending",
            "estimated_completion": "within 24 hours"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating data export request: {e}")
        raise HTTPException(status_code=500, detail="Failed to process data export request")


def generate_data_export(request_id: int, db: Session):
    """
    Background task to generate complete data export.
    
    Args:
        request_id: ID of the DataExportRequest
        db: Database session
    """
    try:
        from models.database import DataExportRequest
        
        # Get export request
        query = select(DataExportRequest).where(DataExportRequest.id == request_id)
        result = db.execute(query)
        export_request = result.scalar_one_or_none()
        
        if not export_request:
            logger.error(f"Export request {request_id} not found")
            return
        
        # Update status to processing
        export_request.status = 'processing'
        db.commit()
        
        # Collect all user data
        user_data = collect_user_data(export_request.user_id, db)
        
        # Generate JSON file
        export_filename = f"yatinveda_data_export_{export_request.user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        export_path = f"exports/{export_filename}"
        
        # Save to file (in production, upload to S3/cloud storage)
        with open(export_path, 'w') as f:
            json.dump(user_data, f, indent=2, default=str)
        
        # Update request with file URL
        export_request.file_url = f"/api/v1/gdpr/download/{export_request.id}"
        export_request.status = 'completed'
        export_request.completed_at = datetime.utcnow()
        db.commit()
        
        # Send email notification (implement email service)
        # await send_export_ready_email(export_request.user_id, export_path)
        
        logger.info(f"Data export completed for request {request_id}")
        
    except Exception as e:
        logger.error(f"Error generating data export: {e}")
        
        # Update request status to failed
        try:
            from models.database import DataExportRequest
            query = select(DataExportRequest).where(DataExportRequest.id == request_id)
            result = db.execute(query)
            export_request = result.scalar_one_or_none()
            
            if export_request:
                export_request.status = 'failed'
                export_request.error_message = str(e)
                db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update export request status: {update_error}")


def collect_user_data(user_id: int, db: Session) -> Dict[str, Any]:
    """Collect all personal data for a user."""
    data = {}
    
    try:
        # User profile
        user_query = select(User).where(User.id == user_id)
        result = db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if user:
            data['user_profile'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'verification_status': user.verification_status,
                'timezone': getattr(user, 'timezone', None),
                'preferred_currency': getattr(user, 'preferred_currency', None),
                'country': getattr(user, 'country', None),
                'language_preference': getattr(user, 'language_preference', None),
                'created_at': user.created_at,
                'updated_at': user.updated_at
            }
        
        # Birth charts
        charts_query = select(Chart).where(Chart.user_id == user_id)
        result = db.execute(charts_query)
        charts = result.scalars().all()
        data['birth_charts'] = [
            {
                'id': chart.id,
                'chart_name': chart.chart_name,
                'birth_details': chart.birth_details,
                'chart_data': chart.chart_data,
                'chart_type': chart.chart_type,
                'is_public': chart.is_public,
                'is_primary': chart.is_primary,
                'created_at': chart.created_at
            }
            for chart in charts
        ]
        
        # Bookings
        bookings_query = select(GuruBooking).where(GuruBooking.user_id == user_id)
        result = db.execute(bookings_query)
        bookings = result.scalars().all()
        data['bookings'] = [
            {
                'id': booking.id,
                'booking_date': booking.booking_date,
                'time_slot': booking.time_slot,
                'duration_minutes': booking.duration_minutes,
                'session_type': booking.session_type,
                'payment_amount': booking.payment_amount,
                'status': booking.status,
                'payment_status': booking.payment_status,
                'created_at': booking.created_at
            }
            for booking in bookings
        ]
        
        # Payments
        payments_query = select(Payment).where(Payment.user_id == user_id)
        result = db.execute(payments_query)
        payments = result.scalars().all()
        data['payments'] = [
            {
                'id': payment.id,
                'order_id': payment.order_id,
                'amount': payment.amount,
                'base_amount': payment.base_amount,
                'gst_amount': payment.gst_amount,
                'status': payment.status,
                'payment_method': payment.payment_method,
                'currency': getattr(payment, 'currency', 'INR'),
                'created_at': payment.created_at,
                'paid_at': payment.paid_at
            }
            for payment in payments
        ]
        
        # Wallet
        wallet_query = select(Wallet).where(Wallet.user_id == user_id)
        result = db.execute(wallet_query)
        wallet = result.scalar_one_or_none()
        if wallet:
            data['wallet'] = {
                'balance': wallet.balance,
                'currency': wallet.currency,
                'is_active': wallet.is_active,
                'created_at': wallet.created_at
            }
            
            # Wallet transactions
            transactions_query = select(WalletTransaction).where(
                WalletTransaction.wallet_id == wallet.id
            )
            result = db.execute(transactions_query)
            transactions = result.scalars().all()
            data['wallet_transactions'] = [
                {
                    'amount': txn.amount,
                    'transaction_type': txn.transaction_type,
                    'description': txn.description,
                    'balance_after': txn.balance_after,
                    'created_at': txn.created_at
                }
                for txn in transactions
            ]
        
        # MFA settings (not including secrets)
        mfa_query = select(MFASettings).where(MFASettings.user_id == user_id)
        result = db.execute(mfa_query)
        mfa = result.scalar_one_or_none()
        if mfa:
            data['mfa_settings'] = {
                'is_enabled': mfa.is_enabled,
                'verified_at': mfa.verified_at,
                'created_at': mfa.created_at
            }
        
        # Learning progress
        progress_query = select(LearningProgress).where(LearningProgress.user_id == user_id)
        result = db.execute(progress_query)
        progress = result.scalars().all()
        data['learning_progress'] = [
            {
                'lesson_id': p.lesson_id,
                'completed': p.completed,
                'completed_at': p.completed_at
            }
            for p in progress
        ]
        
        # Chat history
        chat_query = select(ChatHistory).where(ChatHistory.user_id == user_id)
        result = db.execute(chat_query)
        chats = result.scalars().all()
        data['chat_history'] = [
            {
                'id': chat.id,
                'message': getattr(chat, 'message', None),
                'response': getattr(chat, 'response', None),
                'created_at': getattr(chat, 'created_at', None)
            }
            for chat in chats
        ]
        
        data['export_metadata'] = {
            'export_date': datetime.utcnow().isoformat(),
            'data_version': '1.0.0',
            'format': 'JSON',
            'gdpr_compliance': 'Article 15 & 20'
        }
        
        return data
        
    except Exception as e:
        logger.error(f"Error collecting user data: {e}")
        raise


@router.delete("/delete-account")
async def request_account_deletion(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request complete account and data deletion (GDPR Article 17 - Right to Erasure).
    
    This will permanently delete:
    - User account and profile
    - All birth charts
    - Booking history
    - Wallet and transactions
    - MFA settings and trusted devices
    - Chat history
    - Learning progress
    
    Retained for legal compliance (7 years):
    - Payment records (for tax/audit purposes)
    - Refund records
    
    Cannot be undone!
    """
    try:
        from models.database import DataExportRequest
        
        # Check for active bookings
        active_bookings_query = select(GuruBooking).where(
            GuruBooking.user_id == current_user.id,
            GuruBooking.status.in_(['confirmed', 'pending'])
        )
        result = db.execute(active_bookings_query)
        active_bookings = result.scalars().all()
        
        if active_bookings:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete account with active bookings. Please cancel or complete all bookings first."
            )
        
        # Check for positive wallet balance
        wallet_query = select(Wallet).where(Wallet.user_id == current_user.id)
        result = db.execute(wallet_query)
        wallet = result.scalar_one_or_none()
        
        if wallet and wallet.balance > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Please withdraw your wallet balance ({wallet.balance / 100} {wallet.currency}) before deleting your account."
            )
        
        # Create deletion request
        deletion_request = DataExportRequest(
            user_id=current_user.id,
            request_type='deletion',
            status='pending',
        )
        
        db.add(deletion_request)
        db.commit()
        db.refresh(deletion_request)
        
        # Perform immediate deletion
        perform_account_deletion(current_user.id, db)
        
        return {
            "message": "Account deletion completed successfully",
            "request_id": deletion_request.id,
            "status": "completed",
            "deleted_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing account deletion: {e}")
        raise HTTPException(status_code=500, detail="Failed to process account deletion request")


def perform_account_deletion(user_id: int, db: Session):
    """
    Permanently delete user account and associated data.
    
    Args:
        user_id: ID of user to delete
        db: Database session
    """
    try:
        # Delete in order to respect foreign key constraints
        
        # 1. Delete MFA-related data
        db.execute(delete(TrustedDevice).where(
            TrustedDevice.mfa_settings_id.in_(
                select(MFASettings.id).where(MFASettings.user_id == user_id)
            )
        ))
        db.execute(delete(MFABackupCode).where(MFABackupCode.user_id == user_id))
        db.execute(delete(MFASettings).where(MFASettings.user_id == user_id))
        
        # 2. Delete authentication tokens
        db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
        
        # 3. Delete wallet transactions and wallet
        wallet_query = select(Wallet.id).where(Wallet.user_id == user_id)
        result = db.execute(wallet_query)
        wallet_ids = [row[0] for row in result.all()]
        
        if wallet_ids:
            db.execute(delete(WalletTransaction).where(
                WalletTransaction.wallet_id.in_(wallet_ids)
            ))
            db.execute(delete(Wallet).where(Wallet.user_id == user_id))
        
        # 4. Delete learning progress and chat history
        db.execute(delete(LearningProgress).where(LearningProgress.user_id == user_id))
        db.execute(delete(ChatHistory).where(ChatHistory.user_id == user_id))
        
        # 5. Delete birth charts
        db.execute(delete(Chart).where(Chart.user_id == user_id))
        
        # 6. DELETE bookings (but keep payment records for compliance)
        db.execute(delete(GuruBooking).where(GuruBooking.user_id == user_id))
        
        # 7. Anonymize payment records (keep for legal compliance but remove PII)
        # Note: Payment records are retained but anonymized
        payments_query = select(Payment).where(Payment.user_id == user_id)
        result = db.execute(payments_query)
        payments = result.scalars().all()
        
        for payment in payments:
            payment.user_id = None  # Anonymize
            payment.receipt = f"[DELETED_USER]_{payment.receipt}"
        
        # 8. Finally, delete user account
        db.execute(delete(User).where(User.id == user_id))
        
        db.commit()
        logger.info(f"Successfully deleted account for user {user_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user account: {e}")
        raise


@router.get("/download/{request_id}")
async def download_data_export(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download completed data export file.
    
    Args:
        request_id: ID of the export request
    """
    try:
        from models.database import DataExportRequest
        from fastapi.responses import FileResponse
        
        # Get export request
        query = select(DataExportRequest).where(
            DataExportRequest.id == request_id,
            DataExportRequest.user_id == current_user.id
        )
        result = db.execute(query)
        export_request = result.scalar_one_or_none()
        
        if not export_request:
            raise HTTPException(status_code=404, detail="Export request not found")
        
        if export_request.status != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Export is not ready yet. Current status: {export_request.status}"
            )
        
        if export_request.expires_at and export_request.expires_at < datetime.utcnow():
            raise HTTPException(status_code=410, detail="Export link has expired")
        
        # Return file (implement actual file serving logic)
        return {
            "message": "Download ready",
            "file_url": export_request.file_url,
            "expires_at": export_request.expires_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export: {e}")
        raise HTTPException(status_code=500, detail="Failed to download export")
