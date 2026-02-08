"""
Comprehensive Email Service for YatinVeda
Supports both SMTP and SendGrid with graceful fallback
"""

import os
import logging
import asyncio
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    """Supported email providers"""
    SENDGRID = "sendgrid"
    SMTP = "smtp"
    MOCK = "mock"  # For testing


@dataclass
class EmailMessage:
    """Email message structure"""
    to_email: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    reply_to: Optional[str] = None


class BaseEmailClient(ABC):
    """Abstract base class for email clients"""
    
    @abstractmethod
    async def send(self, message: EmailMessage) -> bool:
        """Send email message"""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if client is properly configured"""
        pass


class SendGridClient(BaseEmailClient):
    """SendGrid email client"""
    
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY", "")
        self.from_email = os.getenv("EMAIL_FROM", "noreply@yatinveda.com")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "YatinVeda")
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def send(self, message: EmailMessage) -> bool:
        """Send email via SendGrid API"""
        if not self.is_configured():
            logger.warning("SendGrid API key not configured")
            return False
        
        try:
            # Use urllib to avoid additional dependencies
            import json
            from urllib import request, error as urllib_error
            
            payload = {
                "personalizations": [
                    {
                        "to": [{"email": message.to_email}],
                        "cc": [{"email": cc} for cc in (message.cc or [])] if message.cc else [],
                        "bcc": [{"email": bcc} for bcc in (message.bcc or [])] if message.bcc else [],
                    }
                ],
                "from": {"email": self.from_email, "name": self.from_name},
                "reply_to": {"email": message.reply_to} if message.reply_to else None,
                "subject": message.subject,
                "content": [
                    {"type": "text/html", "value": message.html_content},
                ]
            }
            
            # Remove None values
            if payload["personalizations"][0]["reply_to"] is None:
                del payload["personalizations"][0]["reply_to"]
            
            data = json.dumps(payload).encode("utf-8")
            
            req = request.Request(
                "https://api.sendgrid.com/v3/mail/send",
                data=data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            
            with request.urlopen(req, timeout=10) as resp:
                if resp.status == 202:
                    logger.info(f"Email sent via SendGrid to {message.to_email}")
                    return True
                else:
                    logger.error(f"SendGrid returned status {resp.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {e}")
            return False


class SMTPClient(BaseEmailClient):
    """SMTP email client"""
    
    def __init__(self):
        self.server = os.getenv("SMTP_SERVER", "")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("EMAIL_FROM", "noreply@yatinveda.com")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    def is_configured(self) -> bool:
        return bool(self.server and self.username and self.password)
    
    async def send(self, message: EmailMessage) -> bool:
        """Send email via SMTP"""
        if not self.is_configured():
            logger.warning("SMTP not configured")
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = self.from_email
            msg["To"] = message.to_email
            
            if message.cc:
                msg["Cc"] = ", ".join(message.cc)
            
            if message.reply_to:
                msg["Reply-To"] = message.reply_to
            
            # Add text and HTML parts
            if message.text_content:
                msg.attach(MIMEText(message.text_content, "plain"))
            msg.attach(MIMEText(message.html_content, "html"))
            
            # Connect and send
            with smtplib.SMTP(self.server, self.port) as server:
                if self.use_tls:
                    server.starttls()
                
                server.login(self.username, self.password)
                
                recipients = [message.to_email]
                if message.cc:
                    recipients.extend(message.cc)
                if message.bcc:
                    recipients.extend(message.bcc)
                
                server.sendmail(self.from_email, recipients, msg.as_string())
            
            logger.info(f"Email sent via SMTP to {message.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False


class MockClient(BaseEmailClient):
    """Mock client for testing - logs instead of sending"""
    
    def is_configured(self) -> bool:
        return True
    
    async def send(self, message: EmailMessage) -> bool:
        logger.info(f"[MOCK EMAIL] To: {message.to_email}, Subject: {message.subject}")
        return True


class EmailService:
    """Main email service with provider abstraction"""
    
    def __init__(self, provider: Optional[str] = None):
        """Initialize email service with specified provider"""
        provider = provider or os.getenv("EMAIL_PROVIDER", "sendgrid")
        
        if provider == "smtp":
            self.client = SMTPClient()
        elif provider == "sendgrid":
            self.client = SendGridClient()
        else:
            self.client = MockClient()
        
        # Fallback chain
        self.sendgrid_client = SendGridClient()
        self.smtp_client = SMTPClient()
        self.mock_client = MockClient()
    
    async def send(self, message: EmailMessage) -> bool:
        """Send email with fallback"""
        # Try primary client
        if self.client.is_configured():
            success = await self.client.send(message)
            if success:
                return True
        
        # Fallback to SendGrid if configured
        if self.sendgrid_client.is_configured() and not isinstance(self.client, SendGridClient):
            success = await self.sendgrid_client.send(message)
            if success:
                return True
        
        # Fallback to SMTP if configured
        if self.smtp_client.is_configured() and not isinstance(self.client, SMTPClient):
            success = await self.smtp_client.send(message)
            if success:
                return True
        
        # Finally fallback to mock
        logger.warning(f"No email provider configured, using mock for {message.to_email}")
        return await self.mock_client.send(message)
    
    async def send_verification_email(
        self,
        to_email: str,
        verification_code: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send OTP/verification code email"""
        user_display = user_name or to_email.split('@')[0]
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                    <h2 style="color: #333; text-align: center;">Verify Your YatinVeda Account</h2>
                    
                    <p>Hello {user_display},</p>
                    
                    <p>Your verification code is:</p>
                    
                    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0;">
                        <span style="font-size: 24px; font-weight: bold; letter-spacing: 2px; color: #4F46E5;">
                            {verification_code}
                        </span>
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        This code will expire in 15 minutes. If you didn't request this code, please ignore this email.
                    </p>
                    
                    <p>With gratitude,<br>Team YatinVeda</p>
                </div>
            </body>
        </html>
        """
        
        message = EmailMessage(
            to_email=to_email,
            subject="🔐 YatinVeda Verification Code",
            html_content=html_content
        )
        
        return await self.send(message)
    
    async def send_welcome_email(
        self,
        to_email: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send welcome email to new users"""
        user_display = user_name or to_email.split('@')[0]
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                    <h1 style="color: #4F46E5; text-align: center;">🌌 Welcome to YatinVeda</h1>
                    
                    <p>Dear {user_display},</p>
                    
                    <p>Welcome to YatinVeda - Your Personal Vedic Astrology Intelligence Platform!</p>
                    
                    <p>Your account has been successfully created. You can now:</p>
                    <ul style="line-height: 1.8;">
                        <li>📊 Generate your Vedic birth chart</li>
                        <li>💬 Chat with our AI Vedic astrology assistant</li>
                        <li>👨‍🏫 Book sessions with expert gurus</li>
                        <li>💊 Receive personalized remedy prescriptions</li>
                        <li>🌙 Explore lunar mansions and planetary influences</li>
                    </ul>
                    
                    <p style="margin-top: 20px;">
                        <a href="https://yatinveda.com/login" style="
                            display: inline-block;
                            background-color: #4F46E5;
                            color: white;
                            padding: 12px 30px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                        ">Sign In to Your Account</a>
                    </p>
                    
                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        If you have any questions, our support team is here to help.
                    </p>
                    
                    <p>With gratitude,<br><strong>Team YatinVeda</strong></p>
                </div>
            </body>
        </html>
        """
        
        message = EmailMessage(
            to_email=to_email,
            subject="🌟 Welcome to YatinVeda!",
            html_content=html_content
        )
        
        return await self.send(message)
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send password reset email"""
        user_display = user_name or to_email.split('@')[0]
        reset_link = f"https://yatinveda.com/reset-password?token={reset_token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                    <h2 style="color: #333; text-align: center;">Reset Your Password</h2>
                    
                    <p>Hello {user_display},</p>
                    
                    <p>We received a request to reset your YatinVeda password. Click the button below to set a new password:</p>
                    
                    <p style="text-align: center; margin: 25px 0;">
                        <a href="{reset_link}" style="
                            display: inline-block;
                            background-color: #EF4444;
                            color: white;
                            padding: 12px 30px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                        ">Reset Password</a>
                    </p>
                    
                    <p style="color: #666; font-size: 14px;">
                        Or copy this link: <br><code>{reset_link}</code>
                    </p>
                    
                    <p style="color: #999; font-size: 13px; margin-top: 20px;">
                        This link will expire in 1 hour. If you didn't request this, please ignore this email 
                        and your password will remain unchanged.
                    </p>
                    
                    <p>Best regards,<br>Team YatinVeda</p>
                </div>
            </body>
        </html>
        """
        
        message = EmailMessage(
            to_email=to_email,
            subject="🔐 Reset Your YatinVeda Password",
            html_content=html_content
        )
        
        return await self.send(message)
    
    async def send_booking_confirmation_email(
        self,
        to_email: str,
        user_name: str,
        guru_name: str,
        booking_date: str,
        booking_time: str,
        booking_id: str
    ) -> bool:
        """Send guru booking confirmation email"""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                    <h2 style="color: #10B981; text-align: center;">✅ Booking Confirmed</h2>
                    
                    <p>Dear {user_name},</p>
                    
                    <p>Your consultation with <strong>{guru_name}</strong> has been confirmed!</p>
                    
                    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Booking Details:</strong></p>
                        <p>📅 Date: <strong>{booking_date}</strong></p>
                        <p>⏰ Time: <strong>{booking_time}</strong></p>
                        <p>🎫 Booking ID: <strong>{booking_id}</strong></p>
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        A meeting link will be sent to you 15 minutes before the scheduled time.
                    </p>
                    
                    <p>With blessings,<br>Team YatinVeda</p>
                </div>
            </body>
        </html>
        """
        
        message = EmailMessage(
            to_email=to_email,
            subject=f"✅ Confirmed: Consultation with {guru_name}",
            html_content=html_content
        )
        
        return await self.send(message)
    
    async def send_prescription_email(
        self,
        to_email: str,
        user_name: str,
        guru_name: str,
        prescription_id: str,
        prescription_title: str,
        pdf_url: str
    ) -> bool:
        """Send prescription notification email"""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                    <h2 style="color: #4F46E5; text-align: center;">💊 Your Remedy Prescription</h2>
                    
                    <p>Dear {user_name},</p>
                    
                    <p><strong>{guru_name}</strong> has prepared a remedy prescription for you:</p>
                    
                    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>{prescription_title}</strong></p>
                        <p>Prescription ID: {prescription_id}</p>
                    </div>
                    
                    <p style="text-align: center; margin: 25px 0;">
                        <a href="{pdf_url}" style="
                            display: inline-block;
                            background-color: #10B981;
                            color: white;
                            padding: 12px 30px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                        ">Download Prescription PDF</a>
                    </p>
                    
                    <p style="color: #666; font-size: 14px;">
                        Your prescription includes detailed remedies, duration, and frequency of practice.
                        Follow the guidance carefully for best results.
                    </p>
                    
                    <p>With blessings,<br>Team YatinVeda</p>
                </div>
            </body>
        </html>
        """
        
        message = EmailMessage(
            to_email=to_email,
            subject=f"💊 Your Remedy Prescription: {prescription_title}",
            html_content=html_content
        )
        
        return await self.send(message)


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create global email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def get_email_service_async() -> EmailService:
    """Async helper for email service"""
    return get_email_service()
