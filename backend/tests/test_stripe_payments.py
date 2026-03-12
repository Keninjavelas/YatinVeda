"""
Tests for Stripe payment endpoints (/api/v1/stripe)
"""

import pytest
import json


class TestCheckoutSession:
    def test_create_checkout_session(self, client, auth_headers):
        r = client.post("/api/v1/stripe/checkout", json={
            "amount": 5000,
            "currency": "usd",
        }, headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "session_id" in body
        assert body["amount"] == 5000
        assert body["currency"] == "usd"

    def test_checkout_with_booking_id(self, client, auth_headers):
        r = client.post("/api/v1/stripe/checkout", json={
            "amount": 10000,
            "currency": "inr",
            "booking_id": 42,
            "description": "Astrology consultation",
        }, headers=auth_headers)
        assert r.status_code == 200

    def test_checkout_unauthenticated(self, client):
        r = client.post("/api/v1/stripe/checkout", json={"amount": 1000})
        assert r.status_code in (401, 403)


class TestPaymentIntent:
    def test_create_payment_intent(self, client, auth_headers):
        r = client.post("/api/v1/stripe/payment-intent", json={
            "amount": 2500,
            "currency": "usd",
        }, headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "payment_intent_id" in body
        assert "client_secret" in body
        assert body["amount"] == 2500

    def test_payment_intent_with_metadata(self, client, auth_headers):
        r = client.post("/api/v1/stripe/payment-intent", json={
            "amount": 3000,
            "metadata": {"order": "123"},
        }, headers=auth_headers)
        assert r.status_code == 200

    def test_payment_intent_unauthenticated(self, client):
        r = client.post("/api/v1/stripe/payment-intent", json={"amount": 1000})
        assert r.status_code in (401, 403)


class TestRefund:
    def test_create_refund(self, client, auth_headers):
        r = client.post("/api/v1/stripe/refund", json={
            "payment_intent_id": "pi_test_123",
            "reason": "requested_by_customer",
        }, headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "refund_id" in body
        assert body["status"] == "succeeded"

    def test_partial_refund(self, client, auth_headers):
        r = client.post("/api/v1/stripe/refund", json={
            "payment_intent_id": "pi_test_456",
            "amount": 500,
        }, headers=auth_headers)
        assert r.status_code == 200

    def test_refund_unauthenticated(self, client):
        r = client.post("/api/v1/stripe/refund", json={
            "payment_intent_id": "pi_test_789",
        })
        assert r.status_code in (401, 403)


class TestWebhook:
    def test_webhook_checkout_completed(self, client):
        payload = json.dumps({"type": "checkout.session.completed"})
        r = client.post(
            "/api/v1/stripe/webhook",
            content=payload.encode(),
            headers={"stripe-signature": "test_sig"},
        )
        assert r.status_code == 200
        assert r.json()["received"] is True

    def test_webhook_no_signature(self, client):
        # Even without signature, mock mode accepts it
        r = client.post(
            "/api/v1/stripe/webhook",
            content=b'{"type":"payment_intent.succeeded"}',
        )
        assert r.status_code == 200


class TestPaymentStatus:
    def test_get_payment_status(self, client, auth_headers):
        r = client.get(
            "/api/v1/stripe/payment/pi_test_123",
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["payment_intent_id"] == "pi_test_123"
        assert "status" in body

    def test_payment_status_unauthenticated(self, client):
        r = client.get("/api/v1/stripe/payment/pi_test_123")
        assert r.status_code in (401, 403)
