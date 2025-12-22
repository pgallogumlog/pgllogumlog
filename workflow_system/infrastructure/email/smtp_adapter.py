"""
SMTP Email Adapter.

Simple SMTP-based email sending that works with any email provider.
For Gmail, requires an "App Password" from Google Account settings.

Setup for Gmail:
1. Go to https://myaccount.google.com/security
2. Enable 2-Factor Authentication
3. Generate an App Password (select "Mail" and your device)
4. Use that app password in SMTP_PASSWORD env variable
"""

from __future__ import annotations

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog

logger = structlog.get_logger()


class SMTPAdapter:
    """
    SMTP-based email adapter.

    Works with Gmail, Outlook, or any SMTP server.
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str | None = None,
        use_tls: bool = True,
    ):
        """
        Initialize SMTP adapter.

        Args:
            smtp_host: SMTP server hostname (e.g., smtp.gmail.com)
            smtp_port: SMTP server port (465 for SSL, 587 for TLS)
            smtp_user: SMTP username (usually your email)
            smtp_password: SMTP password (for Gmail, use App Password)
            from_email: Email address to send from (defaults to smtp_user)
            use_tls: Whether to use TLS (True for port 587, False for port 465)
        """
        self._host = smtp_host
        self._port = smtp_port
        self._user = smtp_user
        self._password = smtp_password
        self._from_email = from_email or smtp_user
        self._use_tls = use_tls

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True,
        bcc: str | None = None,
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            html: Whether body is HTML
            bcc: Optional BCC address

        Returns:
            True if sent successfully
        """
        def _send():
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self._from_email
            msg["To"] = to
            msg["Subject"] = subject

            if bcc:
                msg["Bcc"] = bcc

            # Attach body
            mime_type = "html" if html else "plain"
            msg.attach(MIMEText(body, mime_type))

            # Connect and send
            if self._use_tls:
                # Use TLS (port 587)
                with smtplib.SMTP(self._host, self._port) as server:
                    server.starttls()
                    server.login(self._user, self._password)
                    server.send_message(msg)
            else:
                # Use SSL (port 465)
                with smtplib.SMTP_SSL(self._host, self._port) as server:
                    server.login(self._user, self._password)
                    server.send_message(msg)

            logger.info(
                "email_sent",
                to=to,
                subject=subject,
                from_email=self._from_email,
                via="smtp"
            )
            return True

        try:
            return await asyncio.to_thread(_send)
        except Exception as e:
            logger.error(
                "email_send_failed",
                to=to,
                error=str(e),
                smtp_host=self._host,
                smtp_port=self._port,
            )
            return False

    async def fetch_unread(self, label: str = "INBOX") -> list[dict]:
        """
        Fetch unread emails (not supported via SMTP).

        Note: SMTP is for sending only. Use IMAP for reading emails.
        """
        logger.warning("fetch_unread_not_supported_via_smtp")
        return []

    async def mark_read(self, message_id: str) -> bool:
        """
        Mark email as read (not supported via SMTP).

        Note: SMTP is for sending only. Use IMAP for email management.
        """
        logger.warning("mark_read_not_supported_via_smtp", message_id=message_id)
        return False
