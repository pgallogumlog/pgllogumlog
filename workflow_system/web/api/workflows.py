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
from shared.delivery import deliver_workflow_via_email

logger = structlog.get_logger()
router = APIRouter()


class WorkflowRequest(BaseModel):
    """Request to process a workflow."""

    prompt: str
    client_name: str = "API User"
    client_email: str = "api@example.com"
    tier: str = "Standard"
    run_qa: bool = True
    send_email: bool = True


class SubmitRequest(BaseModel):
    """Request from the AI Readiness Compass submission form."""

    company_name: str
    website: Optional[str] = None
    industry: str
    company_size: str
    pain_point: str
    prompt: str
    tier: str = "Standard"
    email: str
    contact_name: str


class SubmitResponse(BaseModel):
    """Response from form submission."""

    run_id: str
    status: str
    message: str
    tier: str
    email: str


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
        result, _ = await engine.process_inquiry(
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
            email_client = container.email_client()
            await deliver_workflow_via_email(
                result=result,
                inquiry=inquiry,
                email_client=email_client,
                recipient="pgallogumlog@gmail.com",
            )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{run_id}")
async def get_workflow_status(run_id: str):
    """Get the status of a workflow run."""
    # TODO: Implement status tracking
    return {"run_id": run_id, "status": "not_implemented"}


@router.post("/submit", response_model=SubmitResponse)
async def submit_assessment(request: SubmitRequest):
    """
    Submit an AI Readiness Assessment request.

    This endpoint handles submissions from the public form:
    1. Validates the submission
    2. Builds a comprehensive prompt from business context
    3. Processes through the WorkflowEngine
    4. Sends results via email
    5. Returns confirmation
    """
    container = get_container()

    logger.info(
        "assessment_submitted",
        company=request.company_name,
        industry=request.industry,
        tier=request.tier,
        email=request.email,
    )

    try:
        # Build comprehensive prompt from form data
        full_prompt = f"""Company: {request.company_name}
Industry: {request.industry}
Company Size: {request.company_size}
Website: {request.website or 'Not provided'}

Primary Pain Point: {request.pain_point}

Detailed Description:
{request.prompt}

Please analyze this business and recommend the top AI automation workflows that would provide the most value. Focus on practical, implementable solutions using tools like n8n, Zapier, or Make."""

        # Create workflow engine
        engine = WorkflowEngine(
            ai_provider=container.ai_provider(),
            temperatures=container.settings.temperatures,
            min_consensus_votes=container.settings.sc_min_consensus_votes,
        )

        # Create inquiry from submission
        inquiry = EmailInquiry(
            message_id=f"submit-{request.company_name.lower().replace(' ', '-')}",
            from_email=request.email,
            from_name=request.contact_name,
            subject=f"AI Assessment: {request.company_name}",
            body=full_prompt,
        )

        # Process the workflow
        result, qa_result = await engine.process_inquiry(
            inquiry=inquiry,
            tier=request.tier,
        )

        logger.info(
            "assessment_processed",
            run_id=result.run_id,
            company=request.company_name,
            consensus=result.consensus.consensus_strength,
            workflow_count=len(result.consensus.all_workflows),
        )

        # Send results via email
        try:
            email_client = container.email_client()
            await deliver_workflow_via_email(
                result=result,
                inquiry=inquiry,
                email_client=email_client,
                recipient=request.email,
            )
            logger.info(
                "assessment_email_sent",
                run_id=result.run_id,
                recipient=request.email,
            )
        except Exception as email_error:
            logger.error(
                "assessment_email_failed",
                run_id=result.run_id,
                error=str(email_error),
            )
            # Don't fail the request if email fails - still return success

        return SubmitResponse(
            run_id=result.run_id,
            status="processing_complete",
            message=f"Your AI Readiness Assessment for {request.company_name} has been processed. Check your email for results.",
            tier=request.tier,
            email=request.email,
        )

    except Exception as e:
        logger.error(
            "assessment_failed",
            company=request.company_name,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Assessment processing failed: {str(e)}"
        )
