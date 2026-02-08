"""Email template utilities for YatinVeda.

Provides HTML email templates for various notifications and communications.
Templates are responsive and styled with inline CSS for email client compatibility.
"""

from typing import Dict, Optional
from datetime import datetime


# Email styling constants
COLORS = {
    "primary": "#4F46E5",      # Indigo
    "secondary": "#EC4899",    # Pink
    "success": "#10B981",      # Green
    "warning": "#F59E0B",      # Amber
    "danger": "#EF4444",       # Red
    "dark": "#1F2937",         # Gray-800
    "light": "#F9FAFB",        # Gray-50
    "border": "#E5E7EB",       # Gray-200
}

# Base HTML template wrapper
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: {dark};
            background-color: {light};
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        .header {{
            background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .footer {{
            background-color: {light};
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #6B7280;
            border-top: 1px solid {border};
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: {primary};
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin: 10px 0;
        }}
        .button:hover {{
            background-color: #4338CA;
        }}
        .info-box {{
            background-color: {light};
            border-left: 4px solid {primary};
            padding: 15px;
            margin: 15px 0;
        }}
        .logo {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid {border};
        }}
        td:first-child {{
            font-weight: 600;
            width: 40%;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🌌 YatinVeda</div>
            <p style="margin: 0;">{header_text}</p>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p>© {year} YatinVeda. All rights reserved.</p>
            <p>Vedic Astrology Intelligence Platform</p>
            <p style="font-size: 10px; margin-top: 10px;">
                This email was sent to you as part of your YatinVeda account activity.
            </p>
        </div>
    </div>
</body>
</html>
"""


def render_template(subject: str, header_text: str, content: str) -> str:
    """Render email template with content.
    
    Args:
        subject: Email subject line
        header_text: Text to display in header section
        content: Main email content (HTML)
        
    Returns:
        Complete HTML email
    """
    return BASE_TEMPLATE.format(
        subject=subject,
        header_text=header_text,
        content=content,
        year=datetime.utcnow().year,
        **COLORS
    )


def welcome_email(username: str, email: str) -> Dict[str, str]:
    """Generate welcome email for new users.
    
    Args:
        username: User's username
        email: User's email address
        
    Returns:
        Dict with 'subject' and 'html' keys
    """
    content = f"""
    <h2>Welcome to YatinVeda, {username}! 🙏</h2>
    
    <p>Thank you for joining our Vedic Astrology community. We're excited to have you on this journey of self-discovery and cosmic wisdom.</p>
    
    <div class="info-box">
        <p><strong>Your Account Details:</strong></p>
        <p>Username: {username}<br>
        Email: {email}</p>
    </div>
    
    <h3>What's Next?</h3>
    <ul>
        <li>📊 Create your birth chart for personalized insights</li>
        <li>🤖 Chat with VedaMind AI for instant guidance</li>
        <li>👥 Connect with expert gurus for consultations</li>
        <li>🌟 Join our vibrant community discussions</li>
    </ul>
    
    <p style="text-align: center;">
        <a href="https://yatinveda.com/dashboard" class="button">Go to Dashboard</a>
    </p>
    
    <p>If you have any questions, our support team is here to help!</p>
    
    <p>Warm regards,<br>The YatinVeda Team</p>
    """
    
    return {
        "subject": f"Welcome to YatinVeda, {username}!",
        "html": render_template(
            subject="Welcome to YatinVeda",
            header_text="Welcome to Your Vedic Journey",
            content=content
        )
    }


def booking_confirmation_email(
    username: str,
    guru_name: str,
    booking_date: str,
    time_slot: str,
    meeting_link: Optional[str] = None,
    amount: int = 0
) -> Dict[str, str]:
    """Generate booking confirmation email.
    
    Args:
        username: User's name
        guru_name: Guru's name
        booking_date: Date of appointment
        time_slot: Time slot
        meeting_link: Optional video call link
        amount: Payment amount in paise
        
    Returns:
        Dict with 'subject' and 'html' keys
    """
    amount_rupees = amount / 100
    
    content = f"""
    <h2>Booking Confirmed! ✅</h2>
    
    <p>Hello {username},</p>
    
    <p>Your consultation with <strong>{guru_name}</strong> has been confirmed.</p>
    
    <div class="info-box">
        <h3 style="margin-top: 0;">Appointment Details</h3>
        <table>
            <tr>
                <td>Guru:</td>
                <td>{guru_name}</td>
            </tr>
            <tr>
                <td>Date:</td>
                <td>{booking_date}</td>
            </tr>
            <tr>
                <td>Time:</td>
                <td>{time_slot}</td>
            </tr>
            <tr>
                <td>Amount Paid:</td>
                <td>₹{amount_rupees:.2f}</td>
            </tr>
            {f'<tr><td>Meeting Link:</td><td><a href="{meeting_link}">Join Video Call</a></td></tr>' if meeting_link else ''}
        </table>
    </div>
    
    <h3>Preparation Tips:</h3>
    <ul>
        <li>Have your birth details ready (date, time, place)</li>
        <li>Prepare any specific questions you want to ask</li>
        <li>Join the call 5 minutes early</li>
        <li>Ensure good internet connection</li>
    </ul>
    
    <p style="text-align: center;">
        <a href="https://yatinveda.com/book-appointment" class="button">View Booking Details</a>
    </p>
    
    <p>We look forward to your session!</p>
    
    <p>Best regards,<br>The YatinVeda Team</p>
    """
    
    return {
        "subject": f"Booking Confirmed with {guru_name}",
        "html": render_template(
            subject="Booking Confirmation",
            header_text="Your Consultation is Confirmed",
            content=content
        )
    }


def password_reset_email(username: str, reset_token: str, reset_url: str) -> Dict[str, str]:
    """Generate password reset email.
    
    Args:
        username: User's username
        reset_token: Password reset token
        reset_url: Base URL for reset page
        
    Returns:
        Dict with 'subject' and 'html' keys
    """
    reset_link = f"{reset_url}?token={reset_token}"
    
    content = f"""
    <h2>Password Reset Request</h2>
    
    <p>Hello {username},</p>
    
    <p>We received a request to reset your password for your YatinVeda account.</p>
    
    <div class="info-box">
        <p><strong>⚠️ Security Notice:</strong></p>
        <p>If you didn't request this password reset, please ignore this email and your password will remain unchanged.</p>
    </div>
    
    <p>To reset your password, click the button below:</p>
    
    <p style="text-align: center;">
        <a href="{reset_link}" class="button">Reset Password</a>
    </p>
    
    <p style="color: #6B7280; font-size: 14px;">
        This link will expire in 1 hour for security reasons.<br>
        Link: {reset_link}
    </p>
    
    <p>If the button doesn't work, copy and paste the link above into your browser.</p>
    
    <p>Stay secure,<br>The YatinVeda Team</p>
    """
    
    return {
        "subject": "Reset Your YatinVeda Password",
        "html": render_template(
            subject="Password Reset",
            header_text="Reset Your Password",
            content=content
        )
    }


def prescription_ready_email(
    username: str,
    guru_name: str,
    prescription_url: str
) -> Dict[str, str]:
    """Generate prescription ready notification email.
    
    Args:
        username: User's name
        guru_name: Guru who created prescription
        prescription_url: URL to view prescription
        
    Returns:
        Dict with 'subject' and 'html' keys
    """
    content = f"""
    <h2>Your Prescription is Ready! 📋</h2>
    
    <p>Hello {username},</p>
    
    <p><strong>{guru_name}</strong> has prepared your personalized Vedic remedies and recommendations.</p>
    
    <div class="info-box">
        <p>Your prescription includes:</p>
        <ul style="margin: 10px 0;">
            <li>Customized remedial measures</li>
            <li>Mantra recommendations</li>
            <li>Gemstone suggestions (if applicable)</li>
            <li>Lifestyle guidance</li>
        </ul>
    </div>
    
    <p style="text-align: center;">
        <a href="{prescription_url}" class="button">View Your Prescription</a>
    </p>
    
    <p><strong>Note:</strong> Follow the remedies consistently for best results. You can set reminders in your YatinVeda dashboard.</p>
    
    <p>Wishing you well on your journey,<br>The YatinVeda Team</p>
    """
    
    return {
        "subject": f"Prescription Ready from {guru_name}",
        "html": render_template(
            subject="Prescription Ready",
            header_text="Your Personalized Prescription",
            content=content
        )
    }


def community_event_reminder(
    username: str,
    event_title: str,
    event_date: str,
    event_time: str,
    event_url: str,
    is_online: bool = False,
    meeting_link: Optional[str] = None
) -> Dict[str, str]:
    """Generate community event reminder email.
    
    Args:
        username: User's name
        event_title: Event title
        event_date: Event date
        event_time: Event time
        event_url: URL to event details
        is_online: Whether event is online
        meeting_link: Optional online meeting link
        
    Returns:
        Dict with 'subject' and 'html' keys
    """
    content = f"""
    <h2>Event Reminder: {event_title} 📅</h2>
    
    <p>Hello {username},</p>
    
    <p>This is a friendly reminder about the upcoming event you registered for:</p>
    
    <div class="info-box">
        <table>
            <tr>
                <td>Event:</td>
                <td><strong>{event_title}</strong></td>
            </tr>
            <tr>
                <td>Date:</td>
                <td>{event_date}</td>
            </tr>
            <tr>
                <td>Time:</td>
                <td>{event_time}</td>
            </tr>
            <tr>
                <td>Format:</td>
                <td>{'Online Event 💻' if is_online else 'In-Person Event 📍'}</td>
            </tr>
            {f'<tr><td>Join Link:</td><td><a href="{meeting_link}">Click to Join</a></td></tr>' if meeting_link else ''}
        </table>
    </div>
    
    <p style="text-align: center;">
        <a href="{event_url}" class="button">View Event Details</a>
    </p>
    
    <p>We look forward to seeing you there!</p>
    
    <p>Warm regards,<br>The YatinVeda Team</p>
    """
    
    return {
        "subject": f"Reminder: {event_title}",
        "html": render_template(
            subject="Event Reminder",
            header_text="Upcoming Event Reminder",
            content=content
        )
    }


__all__ = [
    "welcome_email",
    "booking_confirmation_email",
    "password_reset_email",
    "prescription_ready_email",
    "community_event_reminder",
    "render_template",
]
