"""
💳 Payment API Endpoints
Razorpay integration for consultations, subscriptions, and wallet management
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, UTC
import secrets
import os
import logging

from database import get_db
from models.database import (
    User, Payment, Refund, Wallet, WalletTransaction,
    GuruBooking, BillingWebhookEvent
)
from modules.auth import get_current_user
from modules.admin_auth import require_admin
from modules.razorpay_integration import RazorpayManager
from modules.billing_events import normalize_razorpay_event, verify_razorpay_webhook_signature

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Razorpay
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

razorpay_manager = RazorpayManager(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)


# ===== PYDANTIC SCHEMAS =====

class CreateOrderRequest(BaseModel):
    booking_id: int
    amount: int  # Amount in rupees
    notes: Optional[dict] = None


class VerifyPaymentRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str
    booking_id: int


class CreateRefundRequest(BaseModel):
    payment_id: int
    amount: Optional[int] = None  # Amount in rupees, None for full refund
    reason: str


class LoadWalletRequest(BaseModel):
    amount: int  # Amount in rupees


class CreateSubscriptionRequest(BaseModel):
    plan_type: str  # monthly, quarterly, yearly


class BillingWebhookEventResponse(BaseModel):
    id: int
    provider: str
    event_id: Optional[str] = None
    event_type: str
    idempotency_key: str
    status: str
    received_at: str
    processed_at: Optional[str] = None
    error_message: Optional[str] = None
    
    
# ===== HELPERS =====

def generate_meeting_link(booking_id: int, guru_id: int) -> str:
    """Generate a pseudo meeting link for a paid/confirmed session.

    This is a placeholder and should be replaced with real provider integration (e.g., Zoom/Meet).
    """
    token = secrets.token_urlsafe(16)
    return f"https://meet.yatinveda.com/session/{booking_id}-{guru_id}?t={token}"


# ===== ORDER CREATION =====

@router.post("/create-order")
async def create_payment_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Razorpay order for consultation payment
    """
    try:
        # Verify booking exists and belongs to user
        booking = db.query(GuruBooking).filter(
            GuruBooking.id == request.booking_id,
            GuruBooking.user_id == current_user.id
        ).first()
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Check if payment already exists
        existing_payment = db.query(Payment).filter(
            Payment.booking_id == request.booking_id,
            Payment.status.in_(["created", "authorized", "captured"])
        ).first()
        
        if existing_payment:
            raise HTTPException(status_code=400, detail="Payment already exists for this booking")
        
        # Calculate GST
        amount_paise = razorpay_manager.rupees_to_paise(request.amount)
        gst_breakdown = razorpay_manager.calculate_gst(amount_paise)
        
        # Create Razorpay order
        order = razorpay_manager.create_order(
            amount=amount_paise,
            receipt=f"booking_{request.booking_id}_{current_user.id}",
            notes=request.notes or {
                "booking_id": request.booking_id,
                "user_id": current_user.id,
                "username": current_user.username
            }
        )
        
        # Save payment record
        payment = Payment(
            user_id=current_user.id,
            booking_id=request.booking_id,
            order_id=order["id"],
            amount=amount_paise,
            base_amount=gst_breakdown["base_amount"],
            gst_amount=gst_breakdown["gst_amount"],
            status="created",
            receipt=order.get("receipt"),
            description=f"Consultation booking #{request.booking_id}"
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        return {
            "order_id": order["id"],
            "amount": amount_paise,
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID,
            "payment_id": payment.id,
            "receipt": order.get("receipt"),
            "notes": order.get("notes")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")


# ===== PAYMENT VERIFICATION =====

@router.post("/verify-payment")
async def verify_payment(
    request: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify Razorpay payment signature and update payment status
    """
    try:
        # Verify signature
        is_valid = razorpay_manager.verify_payment_signature(
            order_id=request.order_id,
            payment_id=request.payment_id,
            signature=request.signature
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
        
        # Get payment record
        payment = db.query(Payment).filter(
            Payment.order_id == request.order_id,
            Payment.user_id == current_user.id
        ).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Fetch payment details from Razorpay to verify it's captured
        razorpay_payment = razorpay_manager.fetch_payment(request.payment_id)
        
        # Verify the payment is captured (or authorize and capture)
        if not razorpay_payment.get("captured"):
            # Attempt to capture if not already captured
            try:
                razorpay_payment = razorpay_manager.capture_payment(
                    request.payment_id,
                    razorpay_payment["amount"]
                )
            except Exception as e:
                logger.warning(f"Failed to capture payment {request.payment_id}: {e}")
                raise HTTPException(status_code=400, detail="Payment could not be captured")
        
        # Update payment record
        payment.payment_id = request.payment_id
        payment.status = "captured"
        payment.payment_method = razorpay_payment.get("method", "card")
        payment.razorpay_signature = request.signature
        payment.razorpay_response = razorpay_payment
        payment.paid_at = datetime.now(UTC)
        
        # Update booking payment status
        if payment.booking_id:
            booking = db.query(GuruBooking).filter(
                GuruBooking.id == payment.booking_id
            ).first()
            if booking:
                booking.payment_status = "paid"
                booking.status = "confirmed"
                # Generate meeting link if not already present
                if not booking.meeting_link:
                    booking.meeting_link = generate_meeting_link(booking.id, booking.guru_id)
                # Ensure a meeting link exists for confirmed bookings
                if not booking.meeting_link:
                    booking.meeting_link = generate_meeting_link(booking.id, booking.guru_id)
        
        db.commit()
        
        return {
            "success": True,
            "payment_id": payment.id,
            "status": payment.status,
            "amount": razorpay_manager.paise_to_rupees(payment.amount),
            "method": payment.payment_method
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying payment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error verifying payment: {str(e)}")


# ===== REFUNDS =====

@router.post("/create-refund")
async def create_refund(
    request: CreateRefundRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a refund for a payment
    """
    try:
        # Get payment
        payment = db.query(Payment).filter(Payment.id == request.payment_id).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Verify ownership or admin rights
        if payment.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        if payment.status not in ["captured", "authorized"]:
            raise HTTPException(status_code=400, detail="Payment cannot be refunded")
        
        # Calculate refund amount
        refund_amount_paise = None
        if request.amount:
            refund_amount_paise = razorpay_manager.rupees_to_paise(request.amount)
        
        # Create refund in Razorpay
        razorpay_refund = razorpay_manager.create_refund(
            payment.payment_id,
            amount=refund_amount_paise,
            notes={"reason": request.reason}
        )
        
        # Save refund record
        refund = Refund(
            payment_id=payment.id,
            refund_id=razorpay_refund["id"],
            amount=razorpay_refund["amount"],
            status="processed" if razorpay_refund["status"] == "processed" else "pending",
            reason=request.reason,
            initiated_by=current_user.id,
            razorpay_response=razorpay_refund
        )
        
        db.add(refund)
        
        # Update payment status
        payment.status = "refunded"
        payment.refunded_at = datetime.now(UTC)
        
        # Update booking payment status
        if payment.booking_id:
            booking = db.query(GuruBooking).filter(
                GuruBooking.id == payment.booking_id
            ).first()
            if booking:
                booking.payment_status = "refunded"
                booking.status = "cancelled"
        
        db.commit()
        db.refresh(refund)
        
        return {
            "success": True,
            "refund_id": refund.id,
            "razorpay_refund_id": refund.refund_id,
            "amount": razorpay_manager.paise_to_rupees(refund.amount),
            "status": refund.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating refund: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating refund: {str(e)}")


# ===== WALLET =====

@router.get("/wallet/balance")
async def get_wallet_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's wallet balance
    """
    try:
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        
        if not wallet:
            # Create wallet if doesn't exist
            wallet = Wallet(user_id=current_user.id, balance=0)
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
        
        return {
            "balance": razorpay_manager.paise_to_rupees(wallet.balance),
            "currency": wallet.currency,
            "is_active": wallet.is_active
        }
        
    except Exception as e:
        logger.error(f"Error fetching wallet balance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching wallet balance")


@router.post("/wallet/load")
async def load_wallet(
    request: LoadWalletRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create order to load money into wallet
    """
    try:
        amount_paise = razorpay_manager.rupees_to_paise(request.amount)
        
        # Create Razorpay order
        order = razorpay_manager.create_order(
            amount=amount_paise,
            receipt=f"wallet_load_{current_user.id}_{datetime.now(UTC).timestamp()}",
            notes={
                "user_id": current_user.id,
                "type": "wallet_load"
            }
        )
        
        # Save payment record
        payment = Payment(
            user_id=current_user.id,
            order_id=order["id"],
            amount=amount_paise,
            base_amount=amount_paise,
            gst_amount=0,
            status="created",
            description="Wallet load",
            receipt=order.get("receipt")
        )
        
        db.add(payment)
        db.commit()
        
        return {
            "order_id": order["id"],
            "amount": amount_paise,
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID
        }
        
    except Exception as e:
        logger.error(f"Error loading wallet: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error loading wallet")


@router.get("/wallet/transactions")
async def get_wallet_transactions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get wallet transaction history
    """
    try:
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        
        if not wallet:
            return {"transactions": []}
        
        transactions = db.query(WalletTransaction).filter(
            WalletTransaction.wallet_id == wallet.id
        ).order_by(WalletTransaction.created_at.desc()).limit(limit).all()
        
        return {
            "transactions": [
                {
                    "id": t.id,
                    "amount": razorpay_manager.paise_to_rupees(abs(t.amount)),
                    "type": "credit" if t.amount > 0 else "debit",
                    "transaction_type": t.transaction_type,
                    "description": t.description,
                    "balance_after": razorpay_manager.paise_to_rupees(t.balance_after),
                    "created_at": t.created_at.isoformat()
                }
                for t in transactions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching wallet transactions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching transactions")


# ===== PAYMENT HISTORY =====

@router.get("/history")
async def get_payment_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's payment history
    """
    try:
        payments = db.query(Payment).filter(
            Payment.user_id == current_user.id
        ).order_by(Payment.created_at.desc()).limit(limit).all()
        
        return {
            "payments": [
                {
                    "id": p.id,
                    "order_id": p.order_id,
                    "payment_id": p.payment_id,
                    "amount": razorpay_manager.paise_to_rupees(p.amount),
                    "status": p.status,
                    "payment_method": p.payment_method,
                    "description": p.description,
                    "created_at": p.created_at.isoformat(),
                    "paid_at": p.paid_at.isoformat() if p.paid_at else None
                }
                for p in payments
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching payment history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching payment history")


# ===== WEBHOOKS =====

@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Handle Razorpay webhook events
    """
    event_record: BillingWebhookEvent | None = None
    try:
        # Get raw body
        body = await request.body()
        body_str = body.decode("utf-8")
        
        # Verify signature
        is_valid = verify_razorpay_webhook_signature(
            razorpay_manager,
            body_str,
            x_razorpay_signature,
            RAZORPAY_WEBHOOK_SECRET,
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        # Parse event
        import json
        event_data = json.loads(body_str)
        normalized = normalize_razorpay_event(event_data, body_str)

        # Idempotent persistence for webhook processing
        existing = db.query(BillingWebhookEvent).filter(
            BillingWebhookEvent.idempotency_key == normalized["idempotency_key"]
        ).first()
        if existing and existing.status == "processed":
            return {"success": True, "duplicate": True}

        if existing:
            event_record = existing
            event_record.payload = normalized["payload"]
            event_record.signature = x_razorpay_signature
            event_record.status = "received"
            event_record.error_message = None
        else:
            event_record = BillingWebhookEvent(
                provider=normalized["provider"],
                event_id=normalized["event_id"],
                event_type=normalized["event_type"],
                idempotency_key=normalized["idempotency_key"],
                signature=x_razorpay_signature,
                status="received",
                payload=normalized["payload"],
            )
            db.add(event_record)
        db.commit()

        event_type = event_data.get("event")
        payload = event_data.get("payload", {}).get("payment", {}).get("entity", {})
        
        logger.info(f"Received webhook event: {event_type}")
        
        # Handle different event types
        if event_type == "payment.captured":
            # Payment was captured successfully
            payment_id = payload.get("id")
            order_id = payload.get("order_id")
            
            payment = db.query(Payment).filter(Payment.order_id == order_id).first()
            if payment:
                payment.payment_id = payment_id
                payment.status = "captured"
                payment.payment_method = payload.get("method", "")
                payment.paid_at = datetime.now(UTC)
                payment.razorpay_response = payload
                db.commit()
                
                # If linked to a booking, mark booking as paid/confirmed and ensure meeting link
                if payment.booking_id:
                    booking = db.query(GuruBooking).filter(GuruBooking.id == payment.booking_id).first()
                    if booking:
                        booking.payment_status = "paid"
                        booking.status = "confirmed"
                        if not booking.meeting_link:
                            booking.meeting_link = generate_meeting_link(booking.id, booking.guru_id)
                        db.commit()
                else:
                    # Wallet top-up flow (no booking): credit user's wallet
                    wallet = db.query(Wallet).filter(Wallet.user_id == payment.user_id).first()
                    if not wallet:
                        wallet = Wallet(user_id=payment.user_id, balance=0)
                        db.add(wallet)
                        db.commit()
                        db.refresh(wallet)
                    wallet.balance += payment.amount
                    txn = WalletTransaction(
                        wallet_id=wallet.id,
                        amount=payment.amount,
                        transaction_type="load",
                        description="Wallet load via Razorpay",
                        reference_id=payment.payment_id,
                        balance_after=wallet.balance
                    )
                    db.add(txn)
                    db.commit()
                
        elif event_type == "payment.failed":
            # Payment failed
            order_id = payload.get("order_id")
            payment = db.query(Payment).filter(Payment.order_id == order_id).first()
            if payment:
                payment.status = "failed"
                payment.razorpay_response = payload
                db.commit()
                # If linked to a booking, mark booking as payment failed but keep status pending
                if payment.booking_id:
                    booking = db.query(GuruBooking).filter(GuruBooking.id == payment.booking_id).first()
                    if booking:
                        booking.payment_status = "pending"
                        db.commit()
        
        elif event_type == "refund.processed":
            # Refund was processed
            refund_id = payload.get("id")
            refund = db.query(Refund).filter(Refund.refund_id == refund_id).first()
            if refund:
                refund.status = "processed"
                refund.processed_at = datetime.now(UTC)
                db.commit()
        
        event_record.status = "processed"
        event_record.processed_at = datetime.utcnow()
        db.commit()

        return {"success": True}
        
    except HTTPException:
        if event_record is not None:
            event_record.status = "failed"
            event_record.error_message = "HTTP error while processing webhook"
            db.commit()
        raise
    except Exception as e:
        if event_record is not None:
            event_record.status = "failed"
            event_record.error_message = str(e)[:500]
            db.commit()
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing webhook")


@router.get("/admin/webhook-events", response_model=list[BillingWebhookEventResponse])
async def list_billing_webhook_events(
    provider: Optional[str] = None,
    status_filter: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only listing endpoint for webhook observability and troubleshooting."""
    query = db.query(BillingWebhookEvent)

    if provider:
        query = query.filter(BillingWebhookEvent.provider == provider)
    if status_filter:
        query = query.filter(BillingWebhookEvent.status == status_filter)
    if event_type:
        query = query.filter(BillingWebhookEvent.event_type == event_type)

    rows = (
        query
        .order_by(BillingWebhookEvent.received_at.desc())
        .offset(max(offset, 0))
        .limit(min(max(limit, 1), 500))
        .all()
    )

    return [
        BillingWebhookEventResponse(
            id=row.id,
            provider=row.provider,
            event_id=row.event_id,
            event_type=row.event_type,
            idempotency_key=row.idempotency_key,
            status=row.status,
            received_at=row.received_at.isoformat(),
            processed_at=row.processed_at.isoformat() if row.processed_at else None,
            error_message=row.error_message,
        )
        for row in rows
    ]
