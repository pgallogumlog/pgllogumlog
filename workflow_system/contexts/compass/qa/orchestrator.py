"""
Compass QA Orchestrator - Coordinates post-generation quality validation.

Phase 1 MVP: Sequential execution of validators
Phase 2: Parallel execution with asyncio
"""

import structlog
from datetime import datetime
from typing import Protocol, runtime_checkable

from contexts.compass.models import CompassRequest
from contexts.compass.qa_models import CompassQAReport, ClientSatisfactionQAResult
from contexts.compass.qa.validators.client_satisfaction_validator import (
    ClientSatisfactionValidator,
)

logger = structlog.get_logger()


@runtime_checkable
class AIProvider(Protocol):
    """Protocol for AI provider dependency."""

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> dict:
        ...


class CompassQAOrchestrator:
    """
    Orchestrator for Compass QA validation.

    Phase 1 (MVP): Runs Client Satisfaction validator only (sequential)
    Phase 2: Adds Research and Synthesis validators (parallel execution)

    Responsibilities:
    - Coordinate validator execution
    - Aggregate results
    - Handle failures gracefully
    - Never block report delivery
    """

    def __init__(self, ai_provider: AIProvider):
        """
        Initialize QA orchestrator.

        Args:
            ai_provider: AI provider for validators
        """
        self._ai = ai_provider
        self._client_validator = ClientSatisfactionValidator(ai_provider)

    async def review(
        self,
        run_id: str,
        request: CompassRequest,
        final_report_html: str,
    ) -> CompassQAReport:
        """
        Run QA validation on generated Compass report.

        Phase 1 MVP: Client Satisfaction validator only

        Args:
            run_id: Unique identifier for this report
            request: Original client request
            final_report_html: Generated HTML report

        Returns:
            CompassQAReport with validation results
        """
        start_time = datetime.utcnow()

        logger.info(
            "compass_qa_review_started",
            run_id=run_id,
            company=request.company_name,
            phase="mvp_phase1",
        )

        # Initialize QA report
        qa_report = CompassQAReport(
            run_id=run_id,
            company_name=request.company_name,
        )

        try:
            # Phase 1: Client Satisfaction Validator only
            logger.info(
                "qa_validator_started",
                run_id=run_id,
                validator="client_satisfaction",
            )

            client_qa = await self._client_validator.validate(
                request=request,
                final_report_html=final_report_html,
            )

            qa_report.client_satisfaction_qa = client_qa

            logger.info(
                "qa_validator_completed",
                run_id=run_id,
                validator="client_satisfaction",
                score=client_qa.overall_score,
                passed=client_qa.passed,
            )

            # Calculate overall scores
            qa_report.aggregate_scores()

            # Calculate duration
            end_time = datetime.utcnow()
            qa_report.qa_duration_seconds = (end_time - start_time).total_seconds()

            logger.info(
                "compass_qa_review_completed",
                run_id=run_id,
                company=request.company_name,
                overall_score=qa_report.overall_score,
                passed=qa_report.passed,
                duration_seconds=qa_report.qa_duration_seconds,
                failures=qa_report.validator_failures,
            )

            return qa_report

        except Exception as e:
            # Handle catastrophic failure
            end_time = datetime.utcnow()
            qa_report.qa_duration_seconds = (end_time - start_time).total_seconds()
            qa_report.validator_failures.append(f"orchestrator_error: {str(e)}")
            qa_report.passed = False

            logger.error(
                "compass_qa_review_failed",
                run_id=run_id,
                company=request.company_name,
                error=str(e),
                duration_seconds=qa_report.qa_duration_seconds,
            )

            return qa_report
