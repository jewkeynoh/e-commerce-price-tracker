# -*- coding: utf-8 -*-
"""
Utility for sending email alerts.
Loads credentials securely using python-dotenv.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
from dotenv import load_dotenv
from pathlib import Path

# Determine project root assuming this file is in the root
PROJECT_ROOT = Path(__file__).parent.resolve()

# Load .env file
dotenv_path = PROJECT_ROOT / ".env"
if dotenv_path.is_file():
    load_dotenv(dotenv_path=dotenv_path)
else:
    # Logging might not be set up yet if called standalone
    print(f"Warning: .env file not found at {dotenv_path}")

# Get logger (assuming basicConfig is called in the main script)
logger = logging.getLogger(__name__)

# Load credentials (allow fallback to None if not set)
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
# Sender email can be defined in .env or config.yaml
ENV_EMAIL_SENDER = os.getenv("EMAIL_SENDER")

def send_email_alert(subject, body, config):
    """Sends an email alert using Gmail SMTP."""
    alert_config = config.get('alert_settings', {})
    if not alert_config.get('enabled', False):
        logger.info("Email alert is disabled in config.")
        return False

    # Determine sender email (prioritize config, then .env)
    sender_email = alert_config.get('sender_email', ENV_EMAIL_SENDER)
    recipient_email = alert_config.get('recipient_email')

    if not all([sender_email, GMAIL_APP_PASSWORD, recipient_email]):
        logger.error("Email configuration incomplete in config.yaml/.env (sender, password, receiver). Cannot send email.")
        return False

    logger.info(f"Preparing email alert: '{subject}' for {recipient_email}...")
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
    message.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    try:
        # Using Port 465 (SSL)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, GMAIL_APP_PASSWORD)
            server.sendmail(sender_email, recipient_email, message.as_string())
            logger.info(f"Email alert successfully sent to {recipient_email}.")
            return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication Error: Check EMAIL_SENDER and GMAIL_APP_PASSWORD in .env/config.")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {e}", exc_info=True)
        return False