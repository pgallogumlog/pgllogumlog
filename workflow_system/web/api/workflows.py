"""
Workflow API endpoints.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import structlog

from config import get_container
from contexts.workflow import WorkflowEngine
from contexts.workflow.models import EmailInquiry
from contexts.qa import QAAuditor

logger = structlog.get_logger()
router = APIRouter()


class WorkflowRequest(BaseModel):
    """Request to process a workflow."""

    prompt: str
    client_name: str = "API User"
    client_email: str = "api@example.com"
    tier: str = "Standard"
    run_qa: bool = True
    send_email: bool = False


class WorkflowResponse(BaseModel):
    """Response from workflow processing."""

    run_id: str
    client_name: str
    business_name: str
    consensus_strength: str
    confidence_percent: int
    workflow_count: int
    phase_count: int
    proposal_subject: str
    proposal_html: str
    qa_score: Optional[int] = None
    qa_passed: Optional[bool] = None


@router.post("/process", response_model=WorkflowResponse)
async def process_workflow(request: WorkflowRequest):
    """
    Process a workflow request.

    This endpoint:
    1. Normalizes the input prompt
    2. Runs research engine
    3. Runs self-consistency voting (5 parallel calls)
    4. Groups workflows into phases
    5. Generates HTML proposal
    6. Optionally runs QA audit
    """
    container = get_container()

    try:
        # Create workflow engine
        engine = WorkflowEngine(
            ai_provider=container.ai_provider(),
            temperatures=container.settings.temperatures,
            min_consensus_votes=container.settings.sc_min_consensus_votes,
        )

        # Create inquiry from request
        inquiry = EmailInquiry(
            message_id=f"api-{request.client_name}",
            from_email=request.client_email,
            from_name=request.client_name,
            subject="API Request",
            body=request.prompt,
        )

        # Process the workflow
        result = await engine.process_inquiry(
            inquiry=inquiry,
            tier=request.tier,
        )

        # Build response
        response = WorkflowResponse(
            run_id=result.run_id,
            client_name=result.client_name,
            business_name=result.business_name,
            consensus_strength=result.consensus.consensus_strength,
            confidence_percent=result.consensus.confidence_percent,
            workflow_count=len(result.consensus.all_workflows),
            phase_count=len(result.proposal.phases),
            proposal_subject=result.proposal.subject,
            proposal_html=result.proposal.html_body,
        )

        # Run QA if requested
        if request.run_qa:
            qa_auditor = QAAuditor(ai_provider=container.ai_provider())
            qa_result = await qa_auditor.audit(result)
            response.qa_score = qa_result.score
            response.qa_passed = qa_result.passed

        # Send email if requested
        if request.send_email:
            try:
                email_client = container.email_client()
                email_sent = await email_client.send(
                    to=request.client_email,
                    subject=result.proposal.subject,
                    body=result.proposal.html_body,
                    html=True,
                )
                if email_sent:
                    logger.info(
                        "proposal_email_sent",
                        to=request.client_email,
                        run_id=result.run_id,
                    )
                else:
                    logger.warning(
                        "proposal_email_send_failed",
                        to=request.client_email,
                        run_id=result.run_id,
                    )
            except Exception as e:
                logger.error(
                    "proposal_email_error",
                    to=request.client_email,
                    run_id=result.run_id,
                    error=str(e),
                )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{run_id}")
async def get_workflow_status(run_id: str):
    """Get the status of a workflow run."""
    # TODO: Implement status tracking
    return {"run_id": run_id, "status": "not_implemented"}
