"""Stripe payment gateway endpoints.

Provides checkout session creation, payment intent management,
webhook handling, and refund processing for international markets.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from database import get_db
from models.database import Payment, User
from modules.auth import get_current_user
from modules.stripe_integration import get_stripe_manager

router = APIRouter(prefix="/stripe", tags=["Stripe Payments"])
logger = logging.getLogger(__name__)


class CheckoutSessionRequest(BaseModel):
    amount: int  # in smallest currency unit (cents for USD)
    currency: str = "usd"
    booking_id: Optional[int] = None
    description: Optional[str] = None


class PaymentIntentRequest(BaseModel):
    amount: int
    currency: str = "usd"
    metadata: Optional[Dict[str, str]] = None


class RefundRequest(BaseModel):
    payment_intent_id: str
    amount: Optional[int] = None
    reason: str = "requested_by_customer"


class CheckoutSessionResponse(BaseModel):
    session_id: str
    url: str
    amount: int
    currency: str
    status: str


class PaymentIntentResponse(BaseModel):
    payment_intent_id: str
    client_secret: str
    amount: int
    currency: str
    status: str


class RefundResponse(BaseModel):
    refund_id: str
    amount: int
    status: str
    payment_intent: str


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a Stripe Checkout Session for payment."""
    try:
        manager = get_stripe_manager()

        base_url = "http://localhost:3000"
        session = manager.create_checkout_session(
            amount=request.amount,
            currency=request.currency,
            success_url=f"{base_url}/wallet?payment=success",
            cancel_url=f"{base_url}/wallet?payment=cancelled",
            metadata={
                "user_id": str(current_user["user_id"]),
                "booking_id": str(request.booking_id) if request.booking_id else "",
            },
        )

        return CheckoutSessionResponse(
            session_id=session["id"],
            url=session.get("url", ""),
            amount=session.get("amount_total", request.amount),
            currency=request.currency,
            status=session.get("status", "open"),
        )
    except Exception as e:
        logger.error("Stripe checkout error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a Payment Intent for in-app payment flows."""
    try:
        manager = get_stripe_manager()
        metadata = request.metadata or {}
        metadata["user_id"] = str(current_user["user_id"])

        intent = manager.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            metadata=metadata,
        )

        return PaymentIntentResponse(
            payment_intent_id=intent["id"],
            client_secret=intent.get("client_secret", ""),
            amount=intent["amount"],
            currency=request.currency,
            status=intent["status"],
        )
    except Exception as e:
        logger.error("Stripe payment intent error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create payment intent")


@router.post("/refund", response_model=RefundResponse)
async def create_refund(
    request: RefundRequest,
    current_user: dict = Depends(get_current_user),
):
    """Process a refund for a Stripe payment."""
    try:
        manager = get_stripe_manager()
        refund = manager.create_refund(
            payment_intent=request.payment_intent_id,
            amount=request.amount,
            reason=request.reason,
        )

        return RefundResponse(
            refund_id=refund["id"],
            amount=refund["amount"],
            status=refund["status"],
            payment_intent=request.payment_intent_id,
        )
    except Exception as e:
        logger.error("Stripe refund error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to process refund")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature", "")

        manager = get_stripe_manager()
        event = manager.verify_webhook(payload, sig_header)

        event_type = event.get("type", "")
        logger.info("Stripe webhook received: %s", event_type)

        if event_type == "checkout.session.completed":
            logger.info("Payment completed via Stripe checkout")
        elif event_type == "payment_intent.succeeded":
            logger.info("Payment intent succeeded")
        elif event_type == "charge.refunded":
            logger.info("Charge refunded")

        return {"received": True}
    except Exception as e:
        logger.error("Stripe webhook error: %s", e)
        raise HTTPException(status_code=400, detail="Webhook processing failed")


@router.get("/payment/{payment_intent_id}")
async def get_payment_status(
    payment_intent_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retrieve the status of a Stripe payment intent."""
    try:
        manager = get_stripe_manager()
        intent = manager.retrieve_payment_intent(payment_intent_id)
        return {
            "payment_intent_id": intent["id"],
            "amount": intent["amount"],
            "currency": intent.get("currency", "usd"),
            "status": intent["status"],
        }
    except Exception as e:
        logger.error("Stripe payment status error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve payment status")
