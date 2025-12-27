"""Workflow delivery helpers."""
from contexts.workflow.models import WorkflowResult, EmailInquiry
import structlog

logger = structlog.get_logger()


async def deliver_workflow_via_email(
    result: WorkflowResult,
    inquiry: EmailInquiry,
    email_client,
    recipient: str = "pgallogumlog@gmail.com",
) -> bool:
    """
    Send workflow proposal via email.

    Args:
        result: Completed workflow result
        inquiry: Original email inquiry
        email_client: Email client for sending
        recipient: Email address to send to (default: pgallogumlog@gmail.com)

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        success = await email_client.send(
            to=recipient,
            subject=result.proposal.subject,
            body=result.proposal.html_body,
            html=True,
        )

        if success:
            logger.info(
                "workflow_delivered",
                to=recipient,
                run_id=result.run_id,
                business=result.business_name,
                client=result.client_name,
                tier=result.tier,
            )
        else:
            logger.warning(
                "workflow_delivery_failed",
                to=recipient,
                run_id=result.run_id,
                business=result.business_name,
            )

        return success

    except Exception as e:
        logger.error(
            "workflow_delivery_error",
            to=recipient,
            run_id=result.run_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        return False
