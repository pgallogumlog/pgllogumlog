"""
Email Poller - Background task for monitoring inbox.

This can be run as part of the main process or as a separate worker.
"""

import asyncio
from datetime import datetime

import structlog

from config import get_container, get_settings
from contexts.workflow import WorkflowEngine
from contexts.workflow.models import EmailInquiry
from contexts.qa import QAAuditor
from shared.delivery import deliver_workflow_via_email

logger = structlog.get_logger()


class EmailPoller:
    """
    Background email poller.

    Monitors Gmail inbox for new inquiries and processes them
    through the workflow engine.
    """

    def __init__(self):
        self._container = get_container()
        self._settings = get_settings()
        self._running = False
        self._workflow_tag = "195371.10WGem"  # Tag to identify workflow emails

    async def start(self):
        """Start the email polling loop."""
        self._running = True
        logger.info(
            "email_poller_started",
            poll_interval=self._settings.gmail_poll_interval_seconds,
        )

        while self._running:
            try:
                await self._poll_once()
            except Exception as e:
                logger.error("email_poll_error", error=str(e))

            await asyncio.sleep(self._settings.gmail_poll_interval_seconds)

    async def stop(self):
        """Stop the email polling loop."""
        self._running = False
        logger.info("email_poller_stopped")

    async def _poll_once(self):
        """Poll inbox once and process any matching emails."""
        email_client = self._container.email_client()
        unread = await email_client.fetch_unread()

        for email in unread:
            # Check if this is a workflow email
            if self._workflow_tag in email.get("subject", ""):
                await self._process_email(email)
                await email_client.mark_read(email["id"])

    async def _process_email(self, email: dict):
        """Process a single email through the workflow."""
        logger.info(
            "processing_email",
            from_email=email.get("from", ""),
            subject=email.get("subject", ""),
        )

        # Extract sender info
        from_str = email.get("from", "")
        from_email = ""
        from_name = ""

        if "<" in from_str and ">" in from_str:
            # Format: "Name" <email@example.com>
            parts = from_str.split("<")
            from_name = parts[0].strip().strip('"')
            from_email = parts[1].rstrip(">")
        else:
            from_email = from_str

        # Create inquiry
        inquiry = EmailInquiry(
            message_id=email.get("id", ""),
            from_email=from_email,
            from_name=from_name,
            subject=email.get("subject", ""),
            body=email.get("body", "") or email.get("snippet", ""),
        )

        # Process through workflow engine
        engine = WorkflowEngine(
            ai_provider=self._container.ai_provider(),
            temperatures=self._settings.temperatures,
            min_consensus_votes=self._settings.sc_min_consensus_votes,
        )

        result = await engine.process_inquiry(inquiry)

        # Run QA audit
        qa_auditor = QAAuditor(
            ai_provider=self._container.ai_provider(),
            sheets_client=self._container.sheets_client(),
            qa_spreadsheet_id=self._settings.google_sheets_qa_log_id,
        )
        qa_result = await qa_auditor.audit(result)
        await qa_auditor.log_to_sheets(qa_result)

        # Send the proposal email using centralized delivery helper
        email_client = self._container.email_client()
        await deliver_workflow_via_email(
            result=result,
            inquiry=inquiry,
            email_client=email_client,
            recipient=inquiry.reply_to,
        )

        logger.info(
            "email_processed",
            run_id=result.run_id,
            qa_score=qa_result.score,
            qa_passed=qa_result.passed,
        )


async def run_poller():
    """Run the email poller (standalone function)."""
    poller = EmailPoller()
    await poller.start()


if __name__ == "__main__":
    asyncio.run(run_poller())
