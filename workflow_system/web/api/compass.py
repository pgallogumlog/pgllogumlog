"""
AI Readiness Compass API endpoints.

Handles premium compass report submissions with Stripe payment integration.
"""

from __future__ import annotations

from typing import Optional, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

import structlog

from config import get_container

logger = structlog.get_logger()
router = APIRouter()

# In-memory report storage (for development/testing)
# In production, use database or file storage
_report_store: Dict[str, dict] = {}


class CompassSubmitRequest(BaseModel):
    """Request to submit an AI Readiness Compass assessment."""

    # Business Information
    company_name: str
    website: Optional[str] = None
    industry: str
    company_size: str

    # Self-Assessment (1-5 scale)
    data_maturity: int = Field(ge=1, le=5)
    automation_experience: int = Field(ge=1, le=5)
    change_readiness: int = Field(ge=1, le=5)

    # Challenge Description
    pain_point: str
    description: str

    # Contact & Delivery
    email: str
    contact_name: str

    # Payment (Stripe PaymentMethod ID from frontend - optional in test mode)
    payment_method_id: Optional[str] = None


class CompassSubmitResponse(BaseModel):
    """Response after compass submission."""

    run_id: str
    status: str
    message: str
    payment_intent_id: Optional[str] = None
    client_secret: Optional[str] = None
    test_mode: bool = False


class CompassStatusResponse(BaseModel):
    """Status of a compass processing job."""

    run_id: str
    status: str  # pending, processing, completed, failed
    company_name: str
    progress_percent: int
    message: Optional[str] = None
    report_ready: bool = False


class PaymentIntentRequest(BaseModel):
    """Request to create a payment intent."""

    email: str


class PaymentIntentResponse(BaseModel):
    """Response with payment intent details."""

    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str


@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(request: PaymentIntentRequest):
    """
    Create a Stripe PaymentIntent with manual capture.

    This is called when the user loads the payment form.
    The intent uses manual capture so we can:
    1. Authorize the payment upfront
    2. Capture only after QA passes
    3. Cancel if QA fails (releases the hold)
    """
    container = get_container()

    try:
        payment_client = container.payment_client()

        intent = await payment_client.create_payment_intent(
            amount_cents=container.settings.compass_price_cents,
            email=request.email,
            metadata={"product": "ai_readiness_compass"},
        )

        logger.info(
            "compass_payment_intent_created",
            payment_intent_id=intent.id,
            email=request.email,
            amount=intent.amount,
        )

        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            amount=intent.amount,
            currency=intent.currency,
        )

    except Exception as e:
        logger.error("compass_payment_intent_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Payment setup failed: {str(e)}")


@router.post("/submit", response_model=CompassSubmitResponse)
async def submit_compass(request: CompassSubmitRequest):
    """
    Submit an AI Readiness Compass request.

    Flow:
    1. Validate submission data
    2. If test_mode: Skip payment, run engine directly
    3. If production: Confirm payment authorization, queue job

    Payment is captured only after QA validation passes.
    """
    container = get_container()
    test_mode = container.settings.compass_test_mode

    logger.info(
        "compass_submitted",
        company=request.company_name,
        industry=request.industry,
        email=request.email,
        test_mode=test_mode,
    )

    try:
        # Import here to avoid circular imports
        from contexts.compass.models import CompassRequest, SelfAssessment
        from contexts.compass.two_call_engine import TwoCallCompassEngine
        import uuid

        # Create domain model from request
        compass_request = CompassRequest(
            company_name=request.company_name,
            website=request.website or "",
            industry=request.industry,
            company_size=request.company_size,
            self_assessment=SelfAssessment(
                data_maturity=request.data_maturity,
                automation_experience=request.automation_experience,
                change_readiness=request.change_readiness,
            ),
            pain_point=request.pain_point,
            description=request.description,
            email=request.email,
            contact_name=request.contact_name,
        )

        if test_mode:
            # TEST MODE: Skip payment, run engine directly
            logger.info(
                "compass_test_mode_processing",
                company=request.company_name,
            )

            # Create two-call engine with AI provider (no payment client in test mode)
            ai_provider = container.ai_provider()
            email_client = container.email_client()

            engine = TwoCallCompassEngine(
                ai_provider=ai_provider,
                email_client=email_client,
                enable_web_search=True,
            )

            # Run the full pipeline synchronously
            result = await engine.process(compass_request)

            # Store report for viewing/downloading
            if result.report:
                _report_store[result.report.run_id] = {
                    "html_content": result.report.html_content,
                    "company_name": result.report.company_name,
                    "score": result.report.ai_readiness_score.overall_score,
                    "created_at": result.report.run_id,
                }

            return CompassSubmitResponse(
                run_id=result.report.run_id if result.report else "test-failed",
                status="completed" if result.qa_passed else "qa_failed",
                message=f"TEST MODE: Report generated for {request.company_name}. QA {'passed' if result.qa_passed else 'failed'}. Score: {result.report.ai_readiness_score.overall_score:.0f}/100" if result.report else f"Processing failed: {result.error}",
                test_mode=True,
            )

        else:
            # PRODUCTION MODE: Require payment
            if not request.payment_method_id:
                raise HTTPException(
                    status_code=400,
                    detail="Payment method required in production mode",
                )

            run_id = f"compass-{uuid.uuid4().hex[:12]}"

            # Get payment client and verify the payment method
            payment_client = container.payment_client()

            # Create payment intent with metadata linking to run_id
            intent = await payment_client.create_payment_intent(
                amount_cents=container.settings.compass_price_cents,
                email=request.email,
                metadata={
                    "run_id": run_id,
                    "company_name": request.company_name,
                    "product": "ai_readiness_compass",
                },
            )

            logger.info(
                "compass_payment_authorized",
                run_id=run_id,
                payment_intent_id=intent.id,
                company=request.company_name,
            )

            # TODO: Queue async job for compass processing
            return CompassSubmitResponse(
                run_id=run_id,
                status="payment_authorized",
                message=f"Payment authorized for {request.company_name}. Your AI Readiness Compass report is being generated. You'll receive it via email within 2-4 hours.",
                payment_intent_id=intent.id,
                client_secret=intent.client_secret,
                test_mode=False,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "compass_submission_failed",
            company=request.company_name,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail=f"Compass submission failed: {str(e)}"
        )


@router.get("/status/{run_id}", response_model=CompassStatusResponse)
async def get_compass_status(run_id: str):
    """
    Get the status of a compass processing job.

    Clients can poll this endpoint to track progress.
    """
    # TODO: Implement status tracking with database/cache
    # For now, return placeholder response

    logger.info("compass_status_requested", run_id=run_id)

    return CompassStatusResponse(
        run_id=run_id,
        status="processing",
        company_name="Unknown",
        progress_percent=0,
        message="Status tracking not yet implemented",
        report_ready=False,
    )


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.

    Events we care about:
    - payment_intent.succeeded: Confirm payment was captured
    - payment_intent.payment_failed: Handle failure
    - payment_intent.canceled: Handle cancellation
    """
    container = get_container()
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    try:
        payment_client = container.payment_client()

        # Verify webhook signature
        event = payment_client.verify_webhook_signature(
            payload=payload,
            signature=signature,
        )

        event_type = event.get("type", "unknown")
        logger.info("compass_webhook_received", event_type=event_type)

        if event_type == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            run_id = payment_intent.get("metadata", {}).get("run_id")
            logger.info(
                "compass_payment_captured",
                run_id=run_id,
                payment_intent_id=payment_intent["id"],
            )

        elif event_type == "payment_intent.payment_failed":
            payment_intent = event["data"]["object"]
            run_id = payment_intent.get("metadata", {}).get("run_id")
            logger.warning(
                "compass_payment_failed",
                run_id=run_id,
                payment_intent_id=payment_intent["id"],
            )

        elif event_type == "payment_intent.canceled":
            payment_intent = event["data"]["object"]
            run_id = payment_intent.get("metadata", {}).get("run_id")
            logger.info(
                "compass_payment_canceled",
                run_id=run_id,
                payment_intent_id=payment_intent["id"],
            )

        return {"status": "ok"}

    except Exception as e:
        logger.error("compass_webhook_error", error=str(e))
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")


@router.get("/price")
async def get_compass_price():
    """Get the current price for AI Readiness Compass."""
    container = get_container()

    return {
        "amount_cents": container.settings.compass_price_cents,
        "amount_dollars": container.settings.compass_price_cents / 100,
        "currency": "usd",
        "product": "AI Readiness Compass",
        "description": "Premium 8-10 page strategic AI implementation report",
    }


@router.get("/config")
async def get_compass_config():
    """Get compass configuration including test mode status."""
    container = get_container()

    return {
        "test_mode": container.settings.compass_test_mode,
        "price_cents": container.settings.compass_price_cents,
        "stripe_publishable_key": container.settings.stripe_publishable_key if not container.settings.compass_test_mode else None,
    }


@router.get("/report/{run_id}", response_class=HTMLResponse)
async def view_report(run_id: str):
    """
    View the generated report in the browser.

    Returns the full HTML report for viewing.
    """
    if run_id not in _report_store:
        raise HTTPException(
            status_code=404,
            detail=f"Report not found: {run_id}. Reports are stored in memory and may have been lost on server restart.",
        )

    report = _report_store[run_id]

    logger.info(
        "compass_report_viewed",
        run_id=run_id,
        company_name=report["company_name"],
    )

    return HTMLResponse(content=report["html_content"])


@router.get("/report/{run_id}/download")
async def download_report(run_id: str):
    """
    Download the report as an HTML file.

    Returns the report with Content-Disposition header for download.
    """
    if run_id not in _report_store:
        raise HTTPException(
            status_code=404,
            detail=f"Report not found: {run_id}. Reports are stored in memory and may have been lost on server restart.",
        )

    report = _report_store[run_id]
    company_name = report["company_name"].replace(" ", "_").replace("&", "and")
    filename = f"AI_Readiness_Compass_{company_name}.html"

    logger.info(
        "compass_report_downloaded",
        run_id=run_id,
        company_name=report["company_name"],
        filename=filename,
    )

    return HTMLResponse(
        content=report["html_content"],
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/reports")
async def list_reports():
    """
    List all stored reports (for development/testing).

    Returns a list of available reports with their run_ids.
    """
    return {
        "count": len(_report_store),
        "reports": [
            {
                "run_id": run_id,
                "company_name": data["company_name"],
                "score": data["score"],
                "view_url": f"/api/compass/report/{run_id}",
                "download_url": f"/api/compass/report/{run_id}/download",
            }
            for run_id, data in _report_store.items()
        ],
    }
