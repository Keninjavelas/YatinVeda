# Email Service Integration Guide

## Overview

YatinVeda includes a comprehensive email service supporting multiple providers for sending transactional emails such as:
- Account verification codes
- Welcome emails
- Password reset instructions
- Booking confirmations
- Prescription notifications

## Architecture

### Components

1. **Email Service Module** (`backend/modules/email_service.py`)
   - Provider abstraction (SendGrid, SMTP, Mock)
   - Async-first design
   - Graceful fallback chain
   - Pre-built email templates

2. **Email Templates** (`backend/modules/email_templates.py`)
   - HTML email templates
   - Responsive design
   - Themed with YatinVeda branding

3. **Email Utils** (`backend/modules/email_utils.py`)
   - Legacy SendGrid integration
   - Used for basic email sending

## Configuration

### Environment Variables

```env
# Email Provider (sendgrid, smtp, or mock)
EMAIL_PROVIDER=sendgrid

# SendGrid Configuration
SENDGRID_API_KEY=sg-your-api-key-here

# SMTP Configuration (alternative)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Sender Information
EMAIL_FROM=noreply@yatinveda.com
EMAIL_FROM_NAME=YatinVeda
```

## Setup Instructions

### Option 1: SendGrid (Recommended for Production)

**Why SendGrid?**
- Reliable delivery (99.9% uptime)
- Built-in bounce/complaint handling
- Template support
- Analytics and tracking
- Cost-effective at scale

**Setup Steps:**

1. **Create SendGrid Account**
   - Go to https://sendgrid.com
   - Sign up and create a free account

2. **Generate API Key**
   - Navigate to Settings → API Keys
   - Create new API Key
   - Copy the key

3. **Configure Environment**
   ```env
   EMAIL_PROVIDER=sendgrid
   SENDGRID_API_KEY=sg-your-key-here
   EMAIL_FROM=noreply@yatinveda.com
   EMAIL_FROM_NAME=YatinVeda
   ```

4. **Verify Sender Identity**
   - SendGrid requires sender verification
   - Go to Settings → Sender Authentication
   - Verify your domain or single sender email

5. **Test Sending**
   ```python
   from modules.email_service import EmailService, EmailMessage
   
   service = EmailService(provider="sendgrid")
   message = EmailMessage(
       to_email="test@example.com",
       subject="Test Email",
       html_content="<h1>Hello!</h1>"
   )
   success = await service.send(message)
   ```

### Option 2: SMTP (Self-Hosted or Gmail)

**For Gmail:**

1. **Enable Less Secure Apps**
   - Go to https://myaccount.google.com/lesssecureapps
   - Enable "Less secure app access"

2. **Generate App Password** (if 2FA enabled)
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Copy the generated password

3. **Configure Environment**
   ```env
   EMAIL_PROVIDER=smtp
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_USE_TLS=true
   EMAIL_FROM=your-email@gmail.com
   ```

**For Other SMTP Services:**

| Provider | Server | Port | TLS |
|----------|--------|------|-----|
| Gmail | smtp.gmail.com | 587 | Yes |
| Outlook | smtp-mail.outlook.com | 587 | Yes |
| AWS SES | email-smtp.REGION.amazonaws.com | 587 | Yes |
| Mailgun | smtp.mailgun.org | 587 | Yes |
| MailChimp | smtp.mandrillapp.com | 587 | Yes |

4. **Test Connection**
   ```python
   from modules.email_service import SMTPClient
   
   client = SMTPClient()
   if client.is_configured():
       print("SMTP configured correctly")
   ```

### Option 3: Mock (Development Only)

```env
EMAIL_PROVIDER=mock
```

Emails will be logged instead of sent. Perfect for development/testing.

## Usage Examples

### Send Verification Email

```python
from modules.email_service import get_email_service

async def send_otp():
    service = get_email_service()
    success = await service.send_verification_email(
        to_email="user@example.com",
        verification_code="123456",
        user_name="John Doe"
    )
    if success:
        print("Verification email sent")
```

### Send Welcome Email

```python
async def welcome_new_user(user_email: str, user_name: str):
    service = get_email_service()
    await service.send_welcome_email(
        to_email=user_email,
        user_name=user_name
    )
```

### Send Password Reset Email

```python
async def reset_password(user_email: str, reset_token: str):
    service = get_email_service()
    await service.send_password_reset_email(
        to_email=user_email,
        reset_token=reset_token,
        user_name="John Doe"
    )
```

### Send Booking Confirmation

```python
async def confirm_booking(user_email: str, booking_data: dict):
    service = get_email_service()
    await service.send_booking_confirmation_email(
        to_email=user_email,
        user_name=booking_data['user_name'],
        guru_name=booking_data['guru_name'],
        booking_date=booking_data['date'],
        booking_time=booking_data['time'],
        booking_id=booking_data['id']
    )
```

### Send Prescription Notification

```python
async def notify_prescription(user_email: str, prescription_data: dict):
    service = get_email_service()
    await service.send_prescription_email(
        to_email=user_email,
        user_name=prescription_data['user_name'],
        guru_name=prescription_data['guru_name'],
        prescription_id=prescription_data['id'],
        prescription_title=prescription_data['title'],
        pdf_url=prescription_data['pdf_url']
    )
```

## Integration with FastAPI

### In Authentication Endpoints

```python
# backend/api/v1/auth.py
from modules.email_service import get_email_service

@router.post("/register")
async def register(user: RegisterRequest, db: Session = Depends(get_db)):
    # ... create user ...
    
    # Send welcome email (fire-and-forget)
    try:
        service = get_email_service()
        asyncio.create_task(
            service.send_welcome_email(
                to_email=new_user.email,
                user_name=new_user.full_name
            )
        )
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
    
    return {"success": True, "user_id": new_user.id}
```

### In Booking Endpoints

```python
# backend/api/v1/guru_booking.py
from modules.email_service import get_email_service

@router.post("/book")
async def book_guru(booking: BookingRequest, current_user: User = Depends(get_current_user)):
    # ... create booking ...
    
    # Send confirmation emails
    service = get_email_service()
    
    # To user
    asyncio.create_task(
        service.send_booking_confirmation_email(
            to_email=current_user.email,
            user_name=current_user.full_name,
            guru_name=booking.guru.name,
            booking_date=booking.date.strftime("%B %d, %Y"),
            booking_time=booking.time.strftime("%I:%M %p"),
            booking_id=str(booking.id)
        )
    )
    
    # To guru
    if booking.guru.user.email:
        asyncio.create_task(
            service.send_booking_confirmation_email(
                to_email=booking.guru.user.email,
                user_name=booking.guru.name,
                guru_name=current_user.full_name,
                booking_date=booking.date.strftime("%B %d, %Y"),
                booking_time=booking.time.strftime("%I:%M %p"),
                booking_id=str(booking.id)
            )
        )
    
    return {"success": True, "booking_id": booking.id}
```

### In Prescription Endpoints

```python
# backend/api/v1/prescriptions.py
from modules.email_service import get_email_service

@router.post("/create")
async def create_prescription(prescription: PrescriptionRequest, current_user: User = Depends(get_current_user)):
    # ... create prescription and PDF ...
    
    # Send prescription notification
    service = get_email_service()
    asyncio.create_task(
        service.send_prescription_email(
            to_email=patient.email,
            user_name=patient.full_name,
            guru_name=guru.name,
            prescription_id=str(prescription.id),
            prescription_title=prescription.title,
            pdf_url=prescription.pdf_url
        )
    )
    
    return {"success": True, "prescription_id": prescription.id}
```

## Email Templates

### Verification Code Email

```
┌──────────────────────────────────────────┐
│   Verify Your YatinVeda Account          │
├──────────────────────────────────────────┤
│                                          │
│  Hello [User Name],                      │
│                                          │
│  Your verification code is:              │
│                                          │
│  ┌────────────────────────────┐          │
│  │  1 2 3 4 5 6               │          │
│  └────────────────────────────┘          │
│                                          │
│  This code will expire in 15 minutes.    │
│                                          │
│  Team YatinVeda                          │
└──────────────────────────────────────────┘
```

### Welcome Email

```
┌──────────────────────────────────────────┐
│   🌌 Welcome to YatinVeda                │
├──────────────────────────────────────────┤
│                                          │
│  Dear [User Name],                       │
│                                          │
│  Your account has been created!          │
│                                          │
│  You can now:                            │
│  • 📊 Generate birth charts              │
│  • 💬 Chat with AI astrology assistant   │
│  • 👨‍🏫 Book guru sessions                  │
│  • 💊 Get remedy prescriptions           │
│                                          │
│  [Sign In to Account]                    │
│                                          │
│  Team YatinVeda                          │
└──────────────────────────────────────────┘
```

## Error Handling & Fallback

The email service includes intelligent fallback:

```python
# Try primary provider (e.g., SendGrid)
# → Fall back to SMTP if configured
# → Fall back to Mock for logging
# → Log warning about missing provider
```

Example:

```python
# Config says use SendGrid, but API key is invalid
# Service will:
# 1. Attempt SendGrid (fails)
# 2. Check if SMTP configured (if yes, use it)
# 3. Check if Mock available (yes)
# 4. Use Mock and log warning
```

## Troubleshooting

### "SendGrid API key not configured"

```bash
# Check environment variable
echo $SENDGRID_API_KEY

# If empty, update .env
SENDGRID_API_KEY=sg-your-actual-key
```

### "Failed to authenticate" (SMTP)

- Verify username/password
- Check if Less Secure Apps is enabled (Gmail)
- Verify app-specific password if using 2FA
- Ensure server and port are correct

### "Email not received"

- Check spam/junk folder
- Verify sender is authorized with SendGrid
- Check SendGrid dashboard for bounces
- Test with Mock provider to see if email was processed

### "Timeout sending email"

- Check network connectivity
- Verify SMTP server is accessible
- Increase timeout in SMTP client
- Check if firewall is blocking SMTP port

## Cost Estimation

### SendGrid
- **Free Tier**: 100 emails/day, unlimited duration
- **Paid**: $9.95-$24.95/month
- **Cost per 100K emails**: ~$10-20

### SMTP (Gmail)
- **Cost**: Free (use personal Gmail account)
- **Limits**: 500/day for business account
- **Notes**: Not recommended for production

### SMTP (AWS SES)
- **Cost**: $0.10 per 1,000 emails
- **Limits**: 14 per second initially
- **Best for**: High volume, AWS infrastructure

## Best Practices

1. **Fire-and-Forget**: Use `asyncio.create_task()` to send emails without blocking
   ```python
   asyncio.create_task(service.send_email(...))
   ```

2. **Retry Logic**: Add exponential backoff for retries
   ```python
   @retry(wait=wait_exponential(multiplier=1, min=2, max=10))
   async def send_with_retry(self, message):
       return await self.send(message)
   ```

3. **Rate Limiting**: Implement per-user rate limits
   ```python
   # Max 1 verification email per user per 5 minutes
   ```

4. **Logging**: Always log email activity
   ```python
   logger.info(f"Email sent to {to_email}", extra={
       "email_type": "verification",
       "user_id": user_id
   })
   ```

5. **Monitoring**: Track email delivery metrics
   - Sent count
   - Bounce rate
   - Spam complaint rate

6. **Testing**: Use Mock provider in tests
   ```python
   import os
   os.environ["EMAIL_PROVIDER"] = "mock"
   ```

## Production Checklist

- [ ] Choose email provider (SendGrid recommended)
- [ ] Create account and API key
- [ ] Configure environment variables
- [ ] Verify sender identity
- [ ] Test all email types
- [ ] Set up email logging/monitoring
- [ ] Configure error handling/fallback
- [ ] Test with real email addresses
- [ ] Monitor bounce and complaint rates
- [ ] Set up email templates in provider dashboard (optional)

## Next Steps

1. Choose email provider (SendGrid or SMTP)
2. Set up account and API credentials
3. Update `.env` configuration
4. Test email sending
5. Integrate with auth/booking/prescription endpoints
6. Monitor delivery and adjust as needed
