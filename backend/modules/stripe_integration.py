"""Stripe payment gateway integration for international markets.

Provides Checkout Session creation, payment intent management,
webhook verification, and refund handling.

Set PAYMENT_STRIPE_MOCK_MODE=true (or leave STRIPE_SECRET_KEY empty) to run in
mock mode — all calls return realistic fake responses without hitting Stripe APIs.
"""

import hashlib
import hmac
import json
import os
import secrets as _secrets
import time
from typing import Any, Dict, Optional

try:
    import stripe as _stripe_lib
except ImportError:
    _stripe_lib = None

_STRIPE_MOCK = (
    os.getenv("PAYMENT_STRIPE_MOCK_MODE", "").lower() in ("1", "true", "yes")
    or not os.getenv("STRIPE_SECRET_KEY", "").strip()
)


class _MockStripeClient:
    """Returns plausible fake responses when Stripe SDK is not configured."""

    @staticmethod
    def _fake_id(prefix: str) -> str:
        return f"{prefix}_{_secrets.token_hex(12)}"

    def create_checkout_session(self, *, amount: int, currency: str = "usd",
                                 success_url: str, cancel_url: str,
                                 metadata: Optional[Dict] = None) -> Dict:
        return {
            "id": self._fake_id("cs"),
            "object": "checkout.session",
            "amount_total": amount,
            "currency": currency,
            "payment_status": "unpaid",
            "status": "open",
            "url": f"https://checkout.stripe.com/mock/{self._fake_id('cs')}",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata or {},
        }

    def create_payment_intent(self, *, amount: int, currency: str = "usd",
                               metadata: Optional[Dict] = None) -> Dict:
        return {
            "id": self._fake_id("pi"),
            "object": "payment_intent",
            "amount": amount,
            "currency": currency,
            "status": "requires_payment_method",
            "client_secret": f"{self._fake_id('pi')}_secret_{_secrets.token_hex(8)}",
            "metadata": metadata or {},
        }

    def retrieve_payment_intent(self, payment_intent_id: str) -> Dict:
        return {
            "id": payment_intent_id,
            "object": "payment_intent",
            "amount": 5000,
            "currency": "usd",
            "status": "succeeded",
            "metadata": {},
        }

    def create_refund(self, *, payment_intent: str, amount: Optional[int] = None,
                      reason: str = "requested_by_customer") -> Dict:
        return {
            "id": self._fake_id("re"),
            "object": "refund",
            "amount": amount or 5000,
            "currency": "usd",
            "payment_intent": payment_intent,
            "status": "succeeded",
            "reason": reason,
        }

    def verify_webhook(self, payload: bytes, sig_header: str, endpoint_secret: str) -> Dict:
        return {"type": "checkout.session.completed", "data": {"object": {}}}


class StripeManager:
    """Production Stripe client with real API integration and mock dev mode."""

    def __init__(self, secret_key: str, webhook_secret: str = "") -> None:
        self.mock_mode = _STRIPE_MOCK
        self.webhook_secret = webhook_secret or os.getenv("STRIPE_WEBHOOK_SECRET", "")

        if self.mock_mode:
            self._mock = _MockStripeClient()
        else:
            if _stripe_lib is None:
                raise RuntimeError("stripe package is not installed. Run: pip install stripe")
            _stripe_lib.api_key = secret_key

    # ------------------------------------------------------------------
    # Checkout Sessions
    # ------------------------------------------------------------------
    def create_checkout_session(self, *, amount: int, currency: str = "usd",
                                 success_url: str, cancel_url: str,
                                 metadata: Optional[Dict] = None) -> Dict:
        if self.mock_mode:
            return self._mock.create_checkout_session(
                amount=amount, currency=currency,
                success_url=success_url, cancel_url=cancel_url,
                metadata=metadata,
            )
        session = _stripe_lib.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "unit_amount": amount,
                    "product_data": {"name": "YatinVeda Consultation"},
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata or {},
        )
        return dict(session)

    # ------------------------------------------------------------------
    # Payment Intents
    # ------------------------------------------------------------------
    def create_payment_intent(self, *, amount: int, currency: str = "usd",
                               metadata: Optional[Dict] = None) -> Dict:
        if self.mock_mode:
            return self._mock.create_payment_intent(
                amount=amount, currency=currency, metadata=metadata,
            )
        intent = _stripe_lib.PaymentIntent.create(
            amount=amount, currency=currency, metadata=metadata or {},
        )
        return dict(intent)

    def retrieve_payment_intent(self, payment_intent_id: str) -> Dict:
        if self.mock_mode:
            return self._mock.retrieve_payment_intent(payment_intent_id)
        return dict(_stripe_lib.PaymentIntent.retrieve(payment_intent_id))

    # ------------------------------------------------------------------
    # Refunds
    # ------------------------------------------------------------------
    def create_refund(self, *, payment_intent: str, amount: Optional[int] = None,
                      reason: str = "requested_by_customer") -> Dict:
        if self.mock_mode:
            return self._mock.create_refund(
                payment_intent=payment_intent, amount=amount, reason=reason,
            )
        params: Dict[str, Any] = {"payment_intent": payment_intent, "reason": reason}
        if amount is not None:
            params["amount"] = amount
        return dict(_stripe_lib.Refund.create(**params))

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------
    def verify_webhook(self, payload: bytes, sig_header: str) -> Dict:
        if self.mock_mode:
            return self._mock.verify_webhook(payload, sig_header, self.webhook_secret)
        event = _stripe_lib.Webhook.construct_event(payload, sig_header, self.webhook_secret)
        return dict(event)


# Module-level singleton
_manager: Optional[StripeManager] = None


def get_stripe_manager() -> StripeManager:
    global _manager
    if _manager is None:
        _manager = StripeManager(
            secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
            webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
        )
    return _manager
