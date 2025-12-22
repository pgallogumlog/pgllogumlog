"""
Gmail Adapter with Service Account Authentication.

Uses Service Account with domain-wide delegation (no browser required).

IMPORTANT: This requires:
1. A Google Workspace account (not regular Gmail)
2. Service account with domain-wide delegation enabled
3. Gmail API enabled in Google Cloud Console

For setup instructions, see:
https://developers.google.com/admin-sdk/directory/v1/guides/delegation
"""

from __future__ import annotations

import asyncio
import base64
from email.mime.text import MIMEText

import structlog

logger = structlog.get_logger()


class GmailAdapterService:
    """
    Gmail adapter using Service Account authentication.

    Requires Google Workspace with domain-wide delegation.
    """

    def __init__(
        self,
        credentials_file: str,
        user_email: str,
    ):
        """
        Initialize Gmail adapter with service account.

        Args:
            credentials_file: Path to service account JSON file
            user_email: Email address to impersonate (must be in same domain)
        """
        self._credentials_file = credentials_file
        self._user_email = user_email
        self._service = None

    def _get_service(self):
        """Lazy-load Gmail API service with service account."""
        if self._service is None:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            SCOPES = [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.modify",
            ]

            # Load service account credentials
            creds = Credentials.from_service_account_file(
                self._credentials_file,
                scopes=SCOPES
            )

            # Delegate to user email (domain-wide delegation)
            delegated_creds = creds.with_subject(self._user_email)

            self._service = build("gmail", "v1", credentials=delegated_creds)
            logger.info(
                "gmail_service_initialized",
                credentials_file=self._credentials_file,
                user_email=self._user_email
            )

        return self._service

    async def fetch_unread(self, label: str = "INBOX") -> list[dict]:
        """
        Fetch unread emails from Gmail.

        Args:
            label: Gmail label to search (default: INBOX)

        Returns:
            List of email dictionaries with id, from, subject, body
        """
        def _fetch():
            service = self._get_service()
            results = (
                service.users()
                .messages()
                .list(userId="me", labelIds=[label], q="is:unread")
                .execute()
            )

            messages = results.get("messages", [])
            emails = []

            for msg in messages:
                msg_data = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )

                headers = {
                    h["name"]: h["value"]
                    for h in msg_data.get("payload", {}).get("headers", [])
                }

                # Extract body
                body = self._extract_body(msg_data.get("payload", {}))

                emails.append({
                    "id": msg["id"],
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "body": body,
                    "snippet": msg_data.get("snippet", ""),
                })

            return emails

        return await asyncio.to_thread(_fetch)

    def _extract_body(self, payload: dict) -> str:
        """Extract plain text body from email payload."""
        if "body" in payload and payload["body"].get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    if part.get("body", {}).get("data"):
                        return base64.urlsafe_b64decode(
                            part["body"]["data"]
                        ).decode("utf-8")
                # Recurse into nested parts
                if "parts" in part:
                    result = self._extract_body(part)
                    if result:
                        return result

        return ""

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True,
        bcc: str | None = None,
    ) -> bool:
        """
        Send an email via Gmail.

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
            service = self._get_service()

            mime_type = "html" if html else "plain"
            message = MIMEText(body, mime_type)
            message["to"] = to
            message["from"] = self._user_email
            message["subject"] = subject

            if bcc:
                message["bcc"] = bcc

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()

            logger.info("email_sent", to=to, subject=subject, from_email=self._user_email)
            return True

        try:
            return await asyncio.to_thread(_send)
        except Exception as e:
            logger.error("email_send_failed", to=to, error=str(e))
            return False

    async def mark_read(self, message_id: str) -> bool:
        """
        Mark an email as read.

        Args:
            message_id: Gmail message ID

        Returns:
            True if successful
        """
        def _mark():
            service = self._get_service()
            service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
            return True

        try:
            return await asyncio.to_thread(_mark)
        except Exception as e:
            logger.error("mark_read_failed", message_id=message_id, error=str(e))
            return False
