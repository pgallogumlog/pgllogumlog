"""
Compass Engine - Main orchestrator for AI Readiness Compass.

Coordinates the full pipeline:
1. Self-assessment scoring (30%)
2. Parallel research agents (70%)
3. Hybrid AI Readiness Score calculation
4. Priority analysis with solutions
5. Report generation
6. QA validation
7. Payment capture/cancel
"""

from __future__ import annotations

import uuid
import structlog
from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

from contexts.compass.models import (
    CompassRequest,
    AIReadinessScore,
    CompassReport,
)
from contexts.compass.scoring import SelfAssessmentScorer
from contexts.compass.agents.orchestrator import ResearchOrchestrator
from contexts.compass.analyzer import PriorityAnalyzer
from contexts.compass.generator import CompassReportGenerator

logger = structlog.get_logger()


@runtime_checkable
class AIProvider(Protocol):
    """Protocol for AI provider dependency."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 4096,
    ) -> str:
        ...

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 4096,
    ) -> dict:
        ...


@runtime_checkable
class PaymentClient(Protocol):
    """Protocol for payment operations."""

    async def capture_payment(self, payment_intent_id: str) -> object:
        ...

    async def cancel_payment(self, payment_intent_id: str) -> object:
        ...


@runtime_checkable
class EmailClient(Protocol):
    """Protocol for email operations."""

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True,
    ) -> bool:
        ...


@dataclass
class CompassResult:
    """Result from compass processing."""

    report: Optional[CompassReport]
    qa_passed: bool
    qa_score: Optional[int] = None
    payment_captured: bool = False
    email_sent: bool = False
    error: Optional[str] = None


class CompassEngine:
    """
    Main orchestrator for AI Readiness Compass pipeline.

    Flow:
    1. Score self-assessment (30% of overall)
    2. Run 3 research agents in parallel (70% of overall)
    3. Calculate hybrid AI Readiness Score
    4. Analyze to get priorities, anti-recommendations, roadmap
    5. Generate premium HTML report
    6. Run QA validation
    7. If QA passes: capture payment, send email
    8. If QA fails: cancel payment, notify
    """

    # Weighting for hybrid score
    SELF_ASSESSMENT_WEIGHT = 0.30
    RESEARCH_WEIGHT = 0.70

    def __init__(
        self,
        ai_provider: AIProvider,
        payment_client: Optional[PaymentClient] = None,
        email_client: Optional[EmailClient] = None,
    ):
        self._ai = ai_provider
        self._payment = payment_client
        self._email = email_client

        # Initialize sub-components
        self._scorer = SelfAssessmentScorer()
        self._research = ResearchOrchestrator(ai_provider)
        self._analyzer = PriorityAnalyzer(ai_provider)
        self._generator = CompassReportGenerator(ai_provider)

    async def process(
        self,
        request: CompassRequest,
        payment_intent_id: Optional[str] = None,
    ) -> CompassResult:
        """
        Process a compass request through the full pipeline.

        Args:
            request: Compass submission request
            payment_intent_id: Optional Stripe payment intent ID

        Returns:
            CompassResult with report and status
        """
        run_id = f"compass-{uuid.uuid4().hex[:12]}"

        logger.info(
            "compass_processing_started",
            run_id=run_id,
            company_name=request.company_name,
            has_payment=bool(payment_intent_id),
        )

        try:
            # Step 1: Score self-assessment (30%)
            logger.info("compass_step", run_id=run_id, step="self_assessment")
            self_assessment_score = self._scorer.score(request.self_assessment)

            # Step 2: Run research agents in parallel (70%)
            logger.info("compass_step", run_id=run_id, step="research")
            research_insights, research_score = await self._research.run_research(
                request
            )

            # Step 3: Calculate hybrid AI Readiness Score
            logger.info("compass_step", run_id=run_id, step="calculate_score")
            overall_score = (
                self_assessment_score * self.SELF_ASSESSMENT_WEIGHT
                + research_score * self.RESEARCH_WEIGHT
            )

            ai_readiness = AIReadinessScore(
                self_assessment_score=self_assessment_score,
                research_score=research_score,
                overall_score=overall_score,
                breakdown=self._scorer.get_breakdown(request.self_assessment),
            )

            # Step 4: Analyze priorities, anti-recommendations, roadmap
            logger.info("compass_step", run_id=run_id, step="analyze")
            priorities, avoid, roadmap = await self._analyzer.analyze(
                request=request,
                research_insights=research_insights.to_dict(),
                ai_readiness=ai_readiness,
            )

            # Step 5: Generate premium report
            logger.info("compass_step", run_id=run_id, step="generate_report")
            report = await self._generator.generate(
                request=request,
                score=ai_readiness,
                research_insights=research_insights.to_dict(),
                priorities=priorities,
                avoid=avoid,
                roadmap=roadmap,
                run_id=run_id,
            )

            # Step 6: QA validation
            logger.info("compass_step", run_id=run_id, step="qa_validation")
            qa_passed, qa_score = await self._run_qa(report)

            # Step 7: Payment and delivery
            payment_captured = False
            email_sent = False

            if qa_passed:
                # Capture payment if we have one
                if payment_intent_id and self._payment:
                    logger.info("compass_step", run_id=run_id, step="capture_payment")
                    try:
                        await self._payment.capture_payment(payment_intent_id)
                        payment_captured = True
                    except Exception as e:
                        logger.error(
                            "compass_payment_capture_failed",
                            run_id=run_id,
                            error=str(e),
                        )

                # Send email
                if self._email:
                    logger.info("compass_step", run_id=run_id, step="send_email")
                    try:
                        await self._send_report_email(request, report)
                        email_sent = True
                    except Exception as e:
                        logger.error(
                            "compass_email_failed",
                            run_id=run_id,
                            error=str(e),
                        )
            else:
                # QA failed - cancel payment
                if payment_intent_id and self._payment:
                    logger.info("compass_step", run_id=run_id, step="cancel_payment")
                    try:
                        await self._payment.cancel_payment(payment_intent_id)
                    except Exception as e:
                        logger.error(
                            "compass_payment_cancel_failed",
                            run_id=run_id,
                            error=str(e),
                        )

            result = CompassResult(
                report=report,
                qa_passed=qa_passed,
                qa_score=qa_score,
                payment_captured=payment_captured,
                email_sent=email_sent,
            )

            logger.info(
                "compass_processing_completed",
                run_id=run_id,
                company_name=request.company_name,
                overall_score=ai_readiness.overall_score,
                qa_passed=qa_passed,
                payment_captured=payment_captured,
                email_sent=email_sent,
            )

            return result

        except Exception as e:
            logger.error(
                "compass_processing_failed",
                run_id=run_id,
                company_name=request.company_name,
                error=str(e),
            )

            # Cancel payment on error
            if payment_intent_id and self._payment:
                try:
                    await self._payment.cancel_payment(payment_intent_id)
                except Exception:
                    pass

            # Return error result
            return CompassResult(
                report=None,
                qa_passed=False,
                error=str(e),
            )

    async def _run_qa(self, report: CompassReport) -> tuple[bool, int | None]:
        """
        Run QA validation on the report.

        Returns:
            Tuple of (passed, score)
        """
        # TODO: Implement proper QA auditor for compass
        # For now, do basic validation

        try:
            # Basic checks
            checks = [
                bool(report.html_content),
                len(report.html_content) > 1000,  # Minimum length
                len(report.priorities) >= 1,
                len(report.roadmap) >= 1,
                report.ai_readiness_score.overall_score > 0,
            ]

            passed = all(checks)
            score = sum(checks) * 2  # Max 10

            logger.info(
                "compass_qa_completed",
                run_id=report.run_id,
                passed=passed,
                score=score,
            )

            return passed, score

        except Exception as e:
            logger.error(
                "compass_qa_failed",
                run_id=report.run_id,
                error=str(e),
            )
            return False, None

    async def _send_report_email(
        self,
        request: CompassRequest,
        report: CompassReport,
    ) -> bool:
        """Send the report to the customer."""
        subject = f"Your AI Readiness Compass Report - {request.company_name}"

        # Create email body
        body = f"""
        <html>
        <body>
        <h2>Your AI Readiness Compass Report is Ready!</h2>
        <p>Dear {request.contact_name},</p>
        <p>Thank you for your purchase. Your AI Readiness Compass report for <strong>{request.company_name}</strong> is attached below.</p>
        <h3>Key Highlights:</h3>
        <ul>
            <li><strong>AI Readiness Score:</strong> {report.ai_readiness_score.overall_score:.0f}/100</li>
            <li><strong>Top Priority:</strong> {report.priorities[0].problem_name if report.priorities else 'N/A'}</li>
            <li><strong>Recommended Solution:</strong> {report.priorities[0].solution.name if report.priorities else 'N/A'}</li>
        </ul>
        <hr>
        {report.html_content}
        </body>
        </html>
        """

        return await self._email.send(
            to=request.email,
            subject=subject,
            body=body,
            html=True,
        )
