import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

async def send_verification_email(email: str, token: str):
    """Send email verification email"""
    if not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD:
        print(f"Email verification token for {email}: {token}")
        return
    
    subject = "Verify Your Email - ATS Checker Pro"
    body = f"""
    <html>
    <body>
        <h2>Welcome to ATS Checker Pro!</h2>
        <p>Please click the link below to verify your email address:</p>
        <a href="{settings.FRONTEND_URL}/auth/verify-email?token={token}" 
           style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Verify Email
        </a>
        <p>If the button doesn't work, copy and paste this link into your browser:</p>
        <p>{settings.FRONTEND_URL}/auth/verify-email?token={token}</p>
        <p>This link will expire in 1 hour.</p>
    </body>
    </html>
    """
    
    await send_email(email, subject, body)

async def send_password_reset_email(email: str, token: str):
    """Send password reset email"""
    if not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD:
        print(f"Password reset token for {email}: {token}")
        return
    
    subject = "Reset Your Password - ATS Checker Pro"
    body = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>You requested to reset your password. Click the link below to reset it:</p>
        <a href="{settings.FRONTEND_URL}/auth/reset-password?token={token}" 
           style="background-color: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Reset Password
        </a>
        <p>If the button doesn't work, copy and paste this link into your browser:</p>
        <p>{settings.FRONTEND_URL}/auth/reset-password?token={token}</p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request this, please ignore this email.</p>
    </body>
    </html>
    """
    
    await send_email(email, subject, body)

async def send_email(to_email: str, subject: str, body: str):
    """Send email using SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.EMAIL_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        if settings.EMAIL_USE_TLS:
            server.starttls()
        server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        # In production, you might want to log this error or queue it for retry
