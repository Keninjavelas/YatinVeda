"""
Tests for payment API endpoints
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch
from models.database import Guru, GuruBooking, Payment, Wallet, WalletTransaction


@pytest.fixture
def test_guru(db_session):
    """Create a test guru"""
    guru = Guru(
        name="Astrologer Sharma",
        title="Premium Vedic Consultant",
        bio="Expert in Kundli and remedies",
        specializations=["Vedic Astrology"],
        languages=["Hindi", "English"],
        experience_years=15,
        rating=5,
        total_sessions=100,
        price_per_hour=5000,
        is_active=True
    )
    db_session.add(guru)
    db_session.commit()
    db_session.refresh(guru)
    return guru


@pytest.fixture
def test_booking(db_session, test_user, test_guru):
    """Create a test booking"""
    tomorrow = datetime.now() + timedelta(days=1)
    booking = GuruBooking(
        user_id=test_user.id,
        guru_id=test_guru.id,
        booking_date=tomorrow,
        time_slot="10:00-11:00",
        duration_minutes=60,
        session_type="video_call",
        payment_amount=5000,
        status="pending",
        payment_status="pending"
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


class TestPaymentOrderCreation:
    """Test payment order creation"""
    
    @patch('api.v1.payments.razorpay_manager.create_order')
    def test_create_order_success(self, mock_create_order, client, test_user, test_booking, auth_headers):
        """Test successful payment order creation"""
        # Mock Razorpay response
        mock_create_order.return_value = {
            "id": "order_test123",
            "entity": "order",
            "amount": 500000,
            "currency": "INR",
            "receipt": f"booking_{test_booking.id}_{test_user.id}",
            "status": "created"
        }
        
        order_data = {
            "booking_id": test_booking.id,
            "amount": 5000,
            "notes": {"custom": "data"}
        }
        
        response = client.post(
            "/api/v1/payments/create-order",
            json=order_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == "order_test123"
        assert data["amount"] == 500000  # In paise
        assert data["currency"] == "INR"
    
    def test_create_order_nonexistent_booking(self, client, auth_headers):
        """Test order creation for non-existent booking"""
        order_data = {
            "booking_id": 99999,
            "amount": 5000
        }
        
        response = client.post(
            "/api/v1/payments/create-order",
            json=order_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch('api.v1.payments.razorpay_manager.create_order')
    def test_create_order_duplicate_payment(self, mock_create_order, client, db_session, test_user, test_booking, auth_headers):
        """Test cannot create duplicate order for same booking"""
        # Create existing payment
        existing_payment = Payment(
            user_id=test_user.id,
            booking_id=test_booking.id,
            order_id="order_existing",
            amount=500000,
            base_amount=500000,
            status="created"
        )
        db_session.add(existing_payment)
        db_session.commit()
        
        order_data = {
            "booking_id": test_booking.id,
            "amount": 5000
        }
        
        response = client.post(
            "/api/v1/payments/create-order",
            json=order_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()


class TestPaymentVerification:
    """Test payment verification"""
    
    @patch('api.v1.payments.razorpay_manager.fetch_payment')
    @patch('api.v1.payments.razorpay_manager.verify_payment_signature')
    def test_verify_payment_success(
        self, mock_verify, mock_fetch, client, db_session, test_user, test_booking, auth_headers
    ):
        """Test successful payment verification updates booking and generates meeting link"""
        # Create payment record
        payment = Payment(
            user_id=test_user.id,
            booking_id=test_booking.id,
            order_id="order_verify123",
            amount=500000,
            base_amount=500000,
            status="created"
        )
        db_session.add(payment)
        db_session.commit()
        
        # Mock responses
        mock_verify.return_value = True
        mock_fetch.return_value = {
            "id": "pay_test123",
            "status": "captured",
            "captured": True,
            "method": "upi",
            "amount": 500000
        }
        
        verify_data = {
            "order_id": "order_verify123",
            "payment_id": "pay_test123",
            "signature": "test_signature",
            "booking_id": test_booking.id
        }
        
        response = client.post(
            "/api/v1/payments/verify-payment",
            json=verify_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "captured"
        
        # Verify booking updated
        db_session.refresh(test_booking)
        assert test_booking.payment_status == "paid"
        assert test_booking.status == "confirmed"
        assert test_booking.meeting_link is not None
        assert "meet.yatinveda.com" in test_booking.meeting_link
    
    @patch('api.v1.payments.razorpay_manager.verify_payment_signature')
    def test_verify_payment_invalid_signature(self, mock_verify, client, auth_headers):
        """Test payment verification with invalid signature"""
        mock_verify.return_value = False
        
        verify_data = {
            "order_id": "order_fake",
            "payment_id": "pay_fake",
            "signature": "invalid_signature",
            "booking_id": 1
        }
        
        response = client.post(
            "/api/v1/payments/verify-payment",
            json=verify_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


class TestPaymentWebhook:
    """Test Razorpay webhook handling"""
    
    @patch('api.v1.payments.razorpay_manager.verify_webhook_signature')
    def test_webhook_payment_captured(self, mock_verify, client, db_session, test_user, test_booking):
        """Test webhook for payment.captured event"""
        # Create payment record
        payment = Payment(
            user_id=test_user.id,
            booking_id=test_booking.id,
            order_id="order_webhook123",
            amount=500000,
            base_amount=500000,
            status="created"
        )
        db_session.add(payment)
        db_session.commit()
        
        mock_verify.return_value = True
        
        webhook_payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_webhook123",
                        "order_id": "order_webhook123",
                        "status": "captured",
                        "method": "card",
                        "amount": 500000
                    }
                }
            }
        }
        
        response = client.post(
            "/api/v1/payments/webhook",
            content=json.dumps(webhook_payload),
            headers={"x-razorpay-signature": "test_signature"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify payment updated
        db_session.refresh(payment)
        assert payment.status == "captured"
        assert payment.payment_id == "pay_webhook123"
        assert payment.payment_method == "card"
        
        # Verify booking updated with meeting link
        db_session.refresh(test_booking)
        assert test_booking.payment_status == "paid"
        assert test_booking.status == "confirmed"
        assert test_booking.meeting_link is not None
    
    @patch('api.v1.payments.razorpay_manager.verify_webhook_signature')
    def test_webhook_payment_failed(self, mock_verify, client, db_session, test_user, test_booking):
        """Test webhook for payment.failed event"""
        payment = Payment(
            user_id=test_user.id,
            booking_id=test_booking.id,
            order_id="order_failed123",
            amount=500000,
            base_amount=500000,
            status="created"
        )
        db_session.add(payment)
        db_session.commit()
        
        mock_verify.return_value = True
        
        webhook_payload = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_failed123",
                        "order_id": "order_failed123",
                        "status": "failed"
                    }
                }
            }
        }
        
        response = client.post(
            "/api/v1/payments/webhook",
            content=json.dumps(webhook_payload),
            headers={"x-razorpay-signature": "test_signature"}
        )
        
        assert response.status_code == 200
        
        # Verify payment marked as failed
        db_session.refresh(payment)
        assert payment.status == "failed"
        
        # Booking should remain pending
        db_session.refresh(test_booking)
        assert test_booking.payment_status == "pending"
        assert test_booking.meeting_link is None
    
    @patch('api.v1.payments.razorpay_manager.verify_webhook_signature')
    def test_webhook_invalid_signature(self, mock_verify, client):
        """Test webhook with invalid signature"""
        mock_verify.return_value = False
        
        webhook_payload = {
            "event": "payment.captured",
            "payload": {}
        }
        
        response = client.post(
            "/api/v1/payments/webhook",
            content=json.dumps(webhook_payload),
            headers={"x-razorpay-signature": "invalid_signature"}
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


class TestRefunds:
    """Test refund creation"""
    
    @patch('api.v1.payments.razorpay_manager.create_refund')
    def test_create_refund_success(self, mock_create_refund, client, db_session, test_user, test_booking, auth_headers):
        """Test successful refund creation"""
        # Create captured payment
        payment = Payment(
            user_id=test_user.id,
            booking_id=test_booking.id,
            order_id="order_refund123",
            payment_id="pay_refund123",
            amount=500000,
            base_amount=500000,
            status="captured"
        )
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        # Mock Razorpay refund
        mock_create_refund.return_value = {
            "id": "rfnd_test123",
            "amount": 500000,
            "status": "processed"
        }
        
        refund_data = {
            "payment_id": payment.id,
            "reason": "User requested cancellation"
        }
        
        response = client.post(
            "/api/v1/payments/create-refund",
            json=refund_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "refund_id" in data
        
        # Verify booking cancelled
        db_session.refresh(test_booking)
        assert test_booking.payment_status == "refunded"
        assert test_booking.status == "cancelled"
    
    def test_create_refund_unauthorized(self, client, db_session, test_user, second_test_user, test_booking, second_auth_headers):
        """Test cannot refund another user's payment"""
        # Create payment for first user
        payment = Payment(
            user_id=test_user.id,
            booking_id=test_booking.id,
            order_id="order_other123",
            payment_id="pay_other123",
            amount=500000,
            base_amount=500000,
            status="captured"
        )
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        # Try to refund as second user
        refund_data = {
            "payment_id": payment.id,
            "reason": "Test"
        }
        
        response = client.post(
            "/api/v1/payments/create-refund",
            json=refund_data,
            headers=second_auth_headers
        )
        
        assert response.status_code == 403


class TestWallet:
    """Test wallet operations"""
    
    def test_get_wallet_balance_creates_wallet(self, client, auth_headers, db_session, test_user):
        """Test getting wallet balance creates wallet if not exists"""
        response = client.get(
            "/api/v1/payments/wallet/balance",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 0
        assert data["currency"] == "INR"
        
        # Verify wallet created
        wallet = db_session.query(Wallet).filter(Wallet.user_id == test_user.id).first()
        assert wallet is not None
    
    @patch('api.v1.payments.razorpay_manager.create_order')
    def test_load_wallet(self, mock_create_order, client, auth_headers):
        """Test wallet load order creation"""
        mock_create_order.return_value = {
            "id": "order_wallet123",
            "amount": 1000000,
            "currency": "INR",
            "status": "created"
        }
        
        load_data = {
            "amount": 10000
        }
        
        response = client.post(
            "/api/v1/payments/wallet/load",
            json=load_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == "order_wallet123"
        assert data["amount"] == 1000000  # In paise
    
    @patch('api.v1.payments.razorpay_manager.verify_webhook_signature')
    def test_webhook_wallet_load_creates_transaction(
        self, mock_verify, client, db_session, test_user
    ):
        """Test webhook for wallet load creates wallet transaction"""
        # Create wallet
        wallet = Wallet(user_id=test_user.id, balance=0)
        db_session.add(wallet)
        db_session.commit()
        db_session.refresh(wallet)
        
        # Create payment record for wallet load
        payment = Payment(
            user_id=test_user.id,
            order_id="order_wallet_load",
            amount=1000000,
            base_amount=1000000,
            status="created",
            description="Wallet load"
        )
        db_session.add(payment)
        db_session.commit()
        
        mock_verify.return_value = True
        
        webhook_payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_wallet123",
                        "order_id": "order_wallet_load",
                        "status": "captured",
                        "amount": 1000000
                    }
                }
            }
        }
        
        response = client.post(
            "/api/v1/payments/webhook",
            content=json.dumps(webhook_payload),
            headers={"x-razorpay-signature": "test_signature"}
        )
        
        assert response.status_code == 200
        
        # Verify wallet balance increased
        db_session.refresh(wallet)
        assert wallet.balance == 1000000
        
        # Verify transaction created
        transaction = db_session.query(WalletTransaction).filter(
            WalletTransaction.wallet_id == wallet.id
        ).first()
        assert transaction is not None
        assert transaction.amount == 1000000
        assert transaction.transaction_type == "load"


class TestPaymentHistory:
    """Test payment history retrieval"""
    
    def test_get_payment_history(self, client, db_session, test_user, test_booking, auth_headers):
        """Test retrieving payment history"""
        # Create some payments
        payment1 = Payment(
            user_id=test_user.id,
            booking_id=test_booking.id,
            order_id="order_hist1",
            payment_id="pay_hist1",
            amount=500000,
            base_amount=500000,
            status="captured",
            description="Consultation payment"
        )
        payment2 = Payment(
            user_id=test_user.id,
            order_id="order_hist2",
            payment_id="pay_hist2",
            amount=1000000,
            base_amount=1000000,
            status="captured",
            description="Wallet load"
        )
        db_session.add(payment1)
        db_session.add(payment2)
        db_session.commit()
        
        response = client.get(
            "/api/v1/payments/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "payments" in data
        assert len(data["payments"]) == 2
        assert data["payments"][0]["status"] == "captured"
