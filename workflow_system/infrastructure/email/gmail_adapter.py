"""
Gmail Adapter.
Implements the EmailClient interface for Gmail API.
"""

from __future__ import annotations

import base64
from email.mime.text import MIMEText
from typing import Any

import structlog

logger = structlog.get_logger()


class GmailAdapter:
    """
    Adapter for Gmail API.

    Implements the EmailClient protocol for dependency injection.
    """

    def __init__(
        self,
        credentials_file: str,
        user_email: str,
    ):
        self._credentials_file = credentials_file
        self._user_email = user_email
        self._service = None

    def _get_service(self):
        """Lazy-load Gmail API service."""
        if self._service is None:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            import os
            import pickle

            SCOPES = [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.modify",
            ]

            creds = None
            token_file = "config/gmail_token.pickle"

            if os.path.exists(token_file):
                with open(token_file, "rb") as token:
                    creds = pickle.load(token)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self._credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                with open(token_file, "wb") as token:
                    pickle.dump(creds, token)

            self._service = build("gmail", "v1", credentials=creds)

        return self._service

    async def fetch_unread(self, label: str = "INBOX") -> list[dict]:
        """
        Fetch unread emails from Gmail.

        Args:
            label: Gmail label to search (default: INBOX)

        Returns:
            List of email dictionaries with id, from, subject, body
        """
        import asyncio

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
        import asyncio

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

            logger.info("email_sent", to=to, subject=subject)
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
        import asyncio

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
