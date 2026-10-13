import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from app.core.exceptions import AppException, ResponseCode

logger = logging.getLogger(__name__)

def send_email(to_email: str, subject: str, html_content: str):
    """
    Sends an email using the SMTP settings defined in the configuration.
    
    Args:
        to_email (str): The recipient's email address.
        subject (str): The subject of the email.
        html_content (str): The HTML content of the email body.
        
    Raises:
        AppException: If sending the email fails.
    """
    try:
        # Create the email message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.MAIL_FROM_ADDRESS
        message["To"] = to_email

        # Attach the HTML content
        part = MIMEText(html_content, "html")
        message.attach(part)

        # Connect to the SMTP server
        if settings.MAIL_ENCRYPTION == "ssl":
            server = smtplib.SMTP_SSL(settings.MAIL_HOST, settings.MAIL_PORT)
        else:
            server = smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT)
            if settings.MAIL_ENCRYPTION == "tls":
                server.starttls()

        # Login and send the email
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.sendmail(settings.MAIL_FROM_ADDRESS, to_email, message.as_string())
        server.quit()
        
        return True

    except Exception as e:
        # Log the error here if logging is configured
        logger.exception("Failed to send email")
        raise AppException(
            ResponseCode.INTERNAL_SERVER_ERROR,
            f"Failed to send email: {str(e)}"
        )
