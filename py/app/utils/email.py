import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template, current_app
from datetime import datetime, timedelta
import jwt
from ..models import User

def send_email(recipient, subject, html_content, text_content=None):
    """Send an email to the specified recipient.
    
    Args:
        recipient (str): Email address of the recipient
        subject (str): Email subject
        html_content (str): HTML content of the email
        text_content (str, optional): Plain text version of the email. If not provided,
                                     a simple text version will be generated from the HTML.
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    # Get email configuration
    smtp_server = current_app.config.get('SMTP_SERVER')
    smtp_port = current_app.config.get('SMTP_PORT', 587)
    smtp_username = current_app.config.get('SMTP_USERNAME')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    email_from = current_app.config.get('EMAIL_FROM')
    email_from_name = current_app.config.get('EMAIL_FROM_NAME', 'Moneda App')
    
    if not all([smtp_server, smtp_username, smtp_password, email_from]):
        current_app.logger.error("Email configuration is incomplete. Cannot send email.")
        return False
    
    # Create message container
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f'"{email_from_name}" <{email_from}>'
    msg['To'] = recipient
    
    # Create the body of the message (a plain-text and an HTML version)
    text = text_content or ""
    html = html_content
    
    # Record the MIME types of both parts - text/plain and text/html
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    
    # Attach parts into message container
    msg.attach(part1)
    msg.attach(part2)
    
    try:
        # Create secure connection with server and send email
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        current_app.logger.info(f"Email sent to {recipient}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {recipient}: {str(e)}")
        return False

def send_verification_email(user):
    """Send an email verification link to the user.
    
    Args:
        user (User): The user to send the verification email to
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    # Generate verification token
    token = jwt.encode(
        {
            'user_id': str(user.id),
            'exp': datetime.utcnow() + timedelta(days=1)
        },
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    # Create verification URL
    verify_url = f"{current_app.config['FRONTEND_URL']}/verify-email/{token}"
    
    # Render email template
    html = render_template('emails/verify_email.html', 
                         user=user, 
                         verify_url=verify_url)
    
    # Send email
    return send_email(
        recipient=user.email,
        subject="Verify Your Email Address",
        html_content=html
    )

def send_password_reset_email(user):
    """Send a password reset email to the user.
    
    Args:
        user (User): The user to send the password reset email to
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    # Generate password reset token
    token = user.generate_reset_token()
    
    # Create reset URL
    reset_url = f"{current_app.config['FRONTEND_URL']}/reset-password/{token}"
    
    # Render email template
    html = render_template('emails/reset_password.html',
                         user=user,
                         reset_url=reset_url)
    
    # Send email
    return send_email(
        recipient=user.email,
        subject="Password Reset Request",
        html_content=html
    )

def send_welcome_email(user):
    """Send a welcome email to a new user.
    
    Args:
        user (User): The new user to welcome
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    # Render email template
    html = render_template('emails/welcome.html', user=user)
    
    # Send email
    return send_email(
        recipient=user.email,
        subject="Welcome to Moneda App!",
        html_content=html
    )

def send_order_confirmation(order):
    """Send an order confirmation email to the user.
    
    Args:
        order (Order): The order to confirm
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    # Get user
    user = User.objects(id=order.user.id).first()
    if not user:
        current_app.logger.error(f"User not found for order {order.id}")
        return False
    
    # Render email template
    html = render_template('emails/order_confirmation.html',
                         user=user,
                         order=order)
    
    # Send email
    return send_email(
        recipient=user.email,
        subject=f"Order Confirmation - {order.order_number}",
        html_content=html
    )

def send_admin_alert(subject, message):
    """Send an alert email to the admin.
    
    Args:
        subject (str): The subject of the alert
        message (str): The message content of the alert
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    admin_email = current_app.config.get('ADMIN_ALERT_EMAIL')
    if not admin_email:
        current_app.logger.error("No admin email configured for alerts")
        return False
    
    # Render email template
    html = render_template('emails/admin_alert.html',
                         subject=subject,
                         message=message)
    
    # Send email
    return send_email(
        recipient=admin_email,
        subject=f"[Admin Alert] {subject}",
        html_content=html
    )
