# -*- coding: utf-8 -*-
"""
alert_utils.py

Utility functions for sending email alerts for the Price Tracker.

This module:
- Loads credentials securely using python-dotenv from a .env file.
- Sends emails using Gmail SMTP over SSL.
- Relies on external configuration passed from the main tracker script.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
import sys  # May be used for safe exits or debugging

# ----------------------------
# Project Root Detection
# ----------------------------

# Attempt to locate the directory where this script is located
try:
    PROJECT_ROOT = Path(__file__).parent.resolve()
except NameError:
    # Fallback in environments where __file__ is not defined (e.g., REPL)
    PROJECT_ROOT = Path.cwd()

# ----------------------------
# Load Environment Variables
# ----------------------------

# Look for .env file in the project root
dotenv_path = PROJECT_ROOT / ".env"
if dotenv_path.is_file():
    print(f"Found .env file at: {dotenv_path}. Loading environment variables.")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}. Ensure it exists for credentials.")

# ----------------------------
# Logger Setup
# ----------------------------

logger = logging.getLogger(__name__)  # Uses root logger from main script

# ----------------------------
# Load Credentials from .env
# ----------------------------

# Gmail App Password and sender email should be defined in the .env file
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
ENV_EMAIL_SENDER = os.getenv("EMAIL_SENDER")  # Used if not specified in config

# ----------------------------
# Email Sending Function
# ----------------------------

def send_email_alert(subject, body, config_data):
    """
    Sends an email alert using Gmail's SMTP over SSL.

    Args:
        subject (str): Email subject line.
        body (str): Plain text body content.
        config_data (dict): Configuration dictionary with 'alert_settings'.

    Returns:
        bool: True if sent successfully or disabled; False on failure.
    """
    alert_config = config_data.get('alert_settings', {})

    # 1. Check if alerts are enabled
    if not alert_config.get('enabled', False):
        logger.info("Email alert is disabled in config. Skipping send.")
        return True  # Nothing to do if alerts are disabled

    # 2. Load config values (prefer config.yaml over .env for sender)
    sender_email = alert_config.get('sender_email', ENV_EMAIL_SENDER)
    recipient_email = alert_config.get('recipient_email')
    smtp_server = alert_config.get('smtp_server', "smtp.gmail.com")
    smtp_port = alert_config.get('smtp_port', 465)

    # 3. Validate required fields
    if not sender_email:
        logger.error("EMAIL_SENDER not found in config.yaml or .env.")
        return False
    if not GMAIL_APP_PASSWORD:
        logger.error("GMAIL_APP_PASSWORD not found in .env.")
        return False
    if not recipient_email:
        logger.error("recipient_email not defined in config.yaml.")
        return False

    # 4. Construct the email message
    logger.info(f"Preparing email alert for {recipient_email} | Subject: '{subject}'")
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
    message.attach(MIMEText(body, "plain", "utf-8"))

    # 5. Send email using SMTP over SSL
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            logger.debug("Connecting to SMTP server...")
            server.login(sender_email, GMAIL_APP_PASSWORD)
            logger.debug("Login successful. Sending email...")
            server.sendmail(sender_email, recipient_email, message.as_string())
            logger.info(f"Email sent to {recipient_email}.")
            return True

    # ----------------------------
    # Error Handling
    # ----------------------------
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication failed. Verify EMAIL_SENDER and GMAIL_APP_PASSWORD.")
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP connection failed: {e}")
        return False
    except smtplib.SMTPSenderRefused as e:
        logger.error(f"SMTP sender address rejected: {e}")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Recipient address rejected: {recipient_email}")
        logger.error(f"Details: {e.recipients}")
        return False
    except ssl.SSLError as e:
        logger.error(f"SSL error during SMTP communication: {e}")
        return False
    except Exception as e:
        logger.error("Unexpected error during email sending", exc_info=True)
        return False

# ----------------------------
# Future Expansion: Notification Triggers
# ----------------------------

# Placeholder for future alert methods:
# def send_sms_alert(message_body, config_data): ...
# def send_pushover_notification(title, message, config_data): ...
# def send_ntfy_notification(title, message, config_data): ...

# Unified interface example:
# def trigger_notifications(subject, body, sms_text, config_data):
#     logger.info("Triggering notifications...")
#     # Launch threads for each type of alert
#     # Join all threads and optionally handle image cleanup, etc.