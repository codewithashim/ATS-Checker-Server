import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_verification_email(email: str, token: str):
    """Send email verification email"""
    if not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD:
        logger.info(f"Email verification token for {email}: {settings.FRONTEND_URL}/auth/verify-email?token={token}")
        return
    
    subject = "Verify Your Email - ATS Checker Pro"
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your Email</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px; text-align: center;">
            <h1 style="color: #2563eb; margin-bottom: 20px;">Welcome to ATS Checker Pro!</h1>
            <p style="font-size: 16px; margin-bottom: 30px;">Thank you for signing up! Please verify your email address to complete your registration.</p>
            
            <a href="{settings.FRONTEND_URL}/auth/verify-email?token={token}" 
               style="display: inline-block; background-color: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-bottom: 20px;">
                Verify Email Address
            </a>
            
            <div style="background-color: #e5e7eb; padding: 20px; border-radius: 8px; margin-top: 20px;">
                <p style="font-size: 14px; margin: 0;"><strong>If the button doesn't work:</strong></p>
                <p style="font-size: 14px; margin: 10px 0 0 0; word-break: break-all; color: #6b7280;">
                    {settings.FRONTEND_URL}/auth/verify-email?token={token}
                </p>
            </div>
            
            <p style="font-size: 14px; color: #6b7280; margin-top: 30px;">
                This verification link will expire in 1 hour for security reasons.
            </p>
            
            <p style="font-size: 14px; color: #6b7280; margin-top: 20px;">
                If you didn't create an account with ATS Checker Pro, please ignore this email.
            </p>
        </div>
    </body>
    </html>
    """
    
    await send_email(email, subject, body)

async def send_password_reset_email(email: str, token: str):
    """Send password reset email"""
    if not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD:
        logger.info(f"Password reset token for {email}: {settings.FRONTEND_URL}/auth/reset-password?token={token}")
        return
    
    subject = "Reset Your Password - ATS Checker Pro"
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Your Password</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px; text-align: center;">
            <h1 style="color: #dc2626; margin-bottom: 20px;">Password Reset Request</h1>
            <p style="font-size: 16px; margin-bottom: 30px;">You requested to reset your password for your ATS Checker Pro account.</p>
            
            <a href="{settings.FRONTEND_URL}/auth/reset-password?token={token}" 
               style="display: inline-block; background-color: #dc2626; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-bottom: 20px;">
                Reset Password
            </a>
            
            <div style="background-color: #e5e7eb; padding: 20px; border-radius: 8px; margin-top: 20px;">
                <p style="font-size: 14px; margin: 0;"><strong>If the button doesn't work:</strong></p>
                <p style="font-size: 14px; margin: 10px 0 0 0; word-break: break-all; color: #6b7280;">
                    {settings.FRONTEND_URL}/auth/reset-password?token={token}
                </p>
            </div>
            
            <p style="font-size: 14px; color: #6b7280; margin-top: 30px;">
                This password reset link will expire in 1 hour for security reasons.
            </p>
            
            <p style="font-size: 14px; color: #6b7280; margin-top: 20px;">
                If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
            </p>
        </div>
    </body>
    </html>
    """
    
    await send_email(email, subject, body)

async def send_email(to_email: str, subject: str, body: str):
    """Send email using SMTP"""
    try:
        # Validate email address
        if not to_email or '@' not in to_email:
            raise ValueError(f"Invalid email address: {to_email}")
        
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("ATS Checker Pro", settings.EMAIL_USERNAME))
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add both plain text and HTML versions
        text_part = MIMEText("Please enable HTML to view this email.", 'plain')
        html_part = MIMEText(body, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Create SMTP connection with timeout
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=30)
        
        try:
            # Enable debug mode if in development
            if settings.DEBUG:
                server.set_debuglevel(1)
            
            if settings.EMAIL_USE_TLS:
                server.starttls()
            
            # Login to the server
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            
            # Send the email
            server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            
        finally:
            # Always close the connection
            server.quit()
            
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed for {to_email}: {str(e)}")
        raise Exception("Email service authentication failed")
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Recipient refused for {to_email}: {str(e)}")
        raise Exception("Invalid email address")
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"SMTP server disconnected for {to_email}: {str(e)}")
        raise Exception("Email service temporarily unavailable")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error for {to_email}: {str(e)}")
        raise Exception("Email service error")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        raise Exception(f"Failed to send email: {str(e)}")
