"""
Two-Call Compass Engine - Simplified architecture for better quality.

ARCHITECTURE:
Call 1: Deep Research - Gather comprehensive data with web search
Call 2: Strategic Synthesis - Generate recommendations from full research context

BENEFITS:
- Better quality: Synthesis has complete research context
- Lower cost: 2 calls vs 4+ agent calls
- Simpler: Easier to maintain and debug
- Cacheable: Research context can be cached for prompt caching savings
"""

from __future__ import annotations

import json
import uuid
import structlog
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Protocol, runtime_checkable, TYPE_CHECKING

from contexts.compass.models import (
    CompassRequest,
    AIReadinessScore,
    CompassReport,
    BusinessPriority,
    AISolution,
    AntiRecommendation,
    RoadmapPhase,
)
from contexts.compass.scoring import SelfAssessmentScorer
from contexts.compass.generator import CompassReportGenerator
from contexts.compass.prompts import (
    DEEP_RESEARCH_SYSTEM,
    DEEP_RESEARCH_USER_TEMPLATE,
    DEEP_RESEARCH_TEMPERATURE,
    STRATEGIC_SYNTHESIS_SYSTEM,
    STRATEGIC_SYNTHESIS_USER_TEMPLATE,
    STRATEGIC_SYNTHESIS_TEMPERATURE,
    get_readiness_tier,
)
from contexts.compass.validators import (
    Call1Validator,
    Call2Validator,
    CrossCallValidator,
    CallQAResult,
    CrossCallQAResult,
    CompassQASummary,
)
from contexts.compass.validators.research_quality_gate import (
    ResearchQualityGate,
    ResearchQualityResult,
    ResearchFailedError,
)

if TYPE_CHECKING:
    from contexts.compass.sheets_logger import CompassQASheetsLogger
    from contexts.compass.qa.orchestrator import CompassQAOrchestrator
    from contexts.compass.qa.sheets_logger import CompassQASheetsLogger as QASheetsLogger

logger = structlog.get_logger()


@runtime_checkable
class AIProvider(Protocol):
    """Protocol for AI provider dependency."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        ...

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> dict:
        ...

    async def generate_json_with_web_search(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 8192,
        max_searches: int = 15,
        model: str | None = None,
    ) -> tuple[dict, dict, list[dict]]:
        """Generate JSON with Claude's native web search enabled."""
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
class TwoCallResult:
    """Result from two-call compass processing."""

    report: Optional[CompassReport]
    research_findings: Optional[dict] = None
    synthesis_output: Optional[dict] = None
    qa_passed: bool = False
    qa_score: Optional[int] = None
    payment_captured: bool = False
    email_sent: bool = False
    error: Optional[str] = None
    call_1_tokens: int = 0
    call_2_tokens: int = 0

    # New QA validation results
    call_1_qa: Optional[CallQAResult] = None
    call_2_qa: Optional[CallQAResult] = None
    cross_call_qa: Optional[CrossCallQAResult] = None
    qa_issues: list[str] = field(default_factory=list)

    # Research quality gate results
    research_quality: Optional[ResearchQualityResult] = None
    citations: list[dict] = field(default_factory=list)


class TwoCallCompassEngine:
    """
    Two-call architecture for AI Readiness Compass.

    Call 1: Deep Research
    - Uses Claude's native web search to gather comprehensive data
    - Company analysis, industry intelligence, implementation patterns
    - Returns structured JSON with citations

    Call 2: Strategic Synthesis
    - Receives complete research context + company profile
    - Generates prioritized recommendations
    - Creates 90-day roadmap and anti-recommendations
    """

    SELF_ASSESSMENT_WEIGHT = 0.30
    RESEARCH_WEIGHT = 0.70

    def __init__(
        self,
        ai_provider: AIProvider,
        payment_client: Optional[PaymentClient] = None,
        email_client: Optional[EmailClient] = None,
        sheets_logger: Optional[CompassQASheetsLogger] = None,
        enable_web_search: bool = True,
        enable_post_generation_qa: bool = False,
        qa_sheets_logger: Optional["QASheetsLogger"] = None,
    ):
        self._ai = ai_provider
        self._payment = payment_client
        self._email = email_client
        self._sheets_logger = sheets_logger
        self._enable_web_search = enable_web_search
        self._enable_post_generation_qa = enable_post_generation_qa
        self._qa_sheets_logger = qa_sheets_logger

        # Initialize sub-components
        self._scorer = SelfAssessmentScorer()
        self._generator = CompassReportGenerator(ai_provider)

        # Initialize QA validators
        self._call_1_validator = Call1Validator()
        self._call_2_validator = Call2Validator()
        self._cross_call_validator = CrossCallValidator()

        # Initialize research quality gate (HARD blocker)
        self._quality_gate = ResearchQualityGate()

        # Initialize post-generation QA orchestrator (Phase 1 MVP)
        if self._enable_post_generation_qa:
            from contexts.compass.qa.orchestrator import CompassQAOrchestrator
            self._qa_orchestrator = CompassQAOrchestrator(ai_provider)
        else:
            self._qa_orchestrator = None

    async def process(
        self,
        request: CompassRequest,
        payment_intent_id: Optional[str] = None,
    ) -> TwoCallResult:
        """
        Process compass request using two-call architecture.

        Args:
            request: Compass submission request
            payment_intent_id: Optional Stripe payment intent ID

        Returns:
            TwoCallResult with report and metadata
        """
        run_id = f"compass-2c-{uuid.uuid4().hex[:12]}"

        logger.info(
            "two_call_compass_started",
            run_id=run_id,
            company_name=request.company_name,
            has_payment=bool(payment_intent_id),
        )

        try:
            # Step 1: Score self-assessment (30%)
            logger.info("two_call_step", run_id=run_id, step="self_assessment")
            self_assessment_score = self._scorer.score(request.self_assessment)

            # Step 2: CALL 1 - Deep Research with REAL web search
            logger.info("two_call_step", run_id=run_id, step="call_1_research")
            start_call_1 = datetime.now()
            research_findings, call_1_tokens, citations = await self._call_1_deep_research(request)
            call_1_duration = (datetime.now() - start_call_1).total_seconds() * 1000

            # Step 2b: QUALITY GATE - HARD blocker before proceeding
            # This validates that real web research was performed
            logger.info("two_call_step", run_id=run_id, step="quality_gate")
            quality_result = await self._quality_gate.validate(
                research_findings=research_findings,
                citations=citations,
                company_name=request.company_name,
                industry=request.industry,
            )

            if not quality_result.passed:
                # BLOCK - Do not proceed with synthesis or report generation
                logger.error(
                    "quality_gate_blocked",
                    run_id=run_id,
                    company_name=request.company_name,
                    issues=quality_result.issues,
                    verified_sources=quality_result.verified_source_count,
                    unique_domains=quality_result.unique_domain_count,
                )

                # Cancel payment authorization (customer NOT charged)
                if payment_intent_id and self._payment:
                    try:
                        await self._payment.cancel_payment(payment_intent_id)
                        logger.info(
                            "quality_gate_payment_cancelled",
                            run_id=run_id,
                            payment_intent_id=payment_intent_id,
                        )
                    except Exception as e:
                        logger.error(
                            "quality_gate_payment_cancel_failed",
                            run_id=run_id,
                            error=str(e),
                        )

                return TwoCallResult(
                    report=None,
                    research_findings=research_findings,
                    qa_passed=False,
                    error=f"Research insufficient: {'; '.join(quality_result.issues)}",
                    qa_issues=quality_result.issues,
                    research_quality=quality_result,
                    citations=citations,
                    call_1_tokens=call_1_tokens,
                )

            logger.info(
                "quality_gate_passed",
                run_id=run_id,
                verified_sources=quality_result.verified_source_count,
                unique_domains=quality_result.unique_domain_count,
            )

            # Step 2c: Validate Call 1 output (semantic checks)
            logger.info("two_call_step", run_id=run_id, step="validate_call_1")
            call_1_qa = self._call_1_validator.validate(
                request=request,
                research_findings=research_findings,
                call_id=f"{run_id}-call-1",
            )
            call_1_qa.run_id = run_id
            call_1_qa.duration_ms = call_1_duration
            logger.info(
                "call_1_validation_complete",
                run_id=run_id,
                passed=call_1_qa.passed,
                score=call_1_qa.score,
                is_relevant=call_1_qa.is_relevant,
            )

            # Calculate research score from findings quality
            research_score = self._score_research_quality(research_findings)

            # Step 3: Calculate hybrid AI Readiness Score
            logger.info("two_call_step", run_id=run_id, step="calculate_score")
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

            # Step 4: CALL 2 - Strategic Synthesis
            logger.info("two_call_step", run_id=run_id, step="call_2_synthesis")
            start_call_2 = datetime.now()
            synthesis_output, call_2_tokens = await self._call_2_synthesis(
                request=request,
                ai_readiness=ai_readiness,
                research_findings=research_findings,
            )
            call_2_duration = (datetime.now() - start_call_2).total_seconds() * 1000

            # Step 4b: Validate Call 2 output
            logger.info("two_call_step", run_id=run_id, step="validate_call_2")
            call_2_qa = self._call_2_validator.validate(
                request=request,
                synthesis_output=synthesis_output,
                call_id=f"{run_id}-call-2",
            )
            call_2_qa.run_id = run_id
            call_2_qa.duration_ms = call_2_duration
            logger.info(
                "call_2_validation_complete",
                run_id=run_id,
                passed=call_2_qa.passed,
                score=call_2_qa.score,
                is_specific=call_2_qa.is_specific,
            )

            # Step 4c: Cross-call validation (does synthesis use research?)
            logger.info("two_call_step", run_id=run_id, step="validate_cross_call")
            cross_call_qa = self._cross_call_validator.validate(
                research_findings=research_findings,
                synthesis_output=synthesis_output,
            )
            logger.info(
                "cross_call_validation_complete",
                run_id=run_id,
                passed=cross_call_qa.passed,
                score=cross_call_qa.score,
                research_used_percent=f"{cross_call_qa.research_used_percent:.0f}%",
            )

            # Step 5: Validate synthesis for hallucinations
            logger.info("two_call_step", run_id=run_id, step="validate_synthesis")
            synthesis_valid, synthesis_issues = self._validate_synthesis_quality(
                synthesis_output, request
            )

            # Step 5b: AI-powered grounding check (hallucination detection)
            logger.info("two_call_step", run_id=run_id, step="grounding_check")
            is_grounded, grounding_issues = await self._check_synthesis_grounding(
                research_findings, synthesis_output
            )
            hallucination_count = len([i for i in grounding_issues if "HALLUCINATION" in i])

            # Step 5c: RETRY synthesis if too many hallucinations (max 1 retry)
            if hallucination_count >= 3:
                logger.warning(
                    "synthesis_retry_triggered",
                    run_id=run_id,
                    hallucination_count=hallucination_count,
                    reason="Too many hallucinations detected, retrying with stricter prompt",
                )

                # Retry synthesis with stricter instructions
                readiness_tier = get_readiness_tier(ai_readiness.overall_score)
                retry_prompt = (
                    "RETRY: Your previous synthesis contained hallucinations. "
                    "This is your FINAL attempt. Follow these rules EXACTLY:\n\n"
                    "1. DO NOT include ANY statistics unless they appear VERBATIM in the research\n"
                    "2. DO NOT mention ANY company names unless they appear in the research\n"
                    "3. For impact metrics, say 'Impact varies - recommend pilot' instead of making up numbers\n"
                    "4. For pricing, say 'Contact vendor for quote'\n"
                    "5. It is BETTER to have fewer statistics than to invent them\n\n"
                    + STRATEGIC_SYNTHESIS_USER_TEMPLATE.format(
                        company_name=request.company_name,
                        website=request.website or "Not provided",
                        industry=request.industry,
                        company_size=request.company_size,
                        pain_point=request.pain_point,
                        description=request.description,
                        overall_score=ai_readiness.overall_score,
                        self_assessment_score=ai_readiness.self_assessment_score,
                        research_score=ai_readiness.research_score,
                        readiness_tier=readiness_tier,
                        data_maturity=request.self_assessment.data_maturity,
                        automation_experience=request.self_assessment.automation_experience,
                        change_readiness=request.self_assessment.change_readiness,
                        research_findings=json.dumps(research_findings, indent=2),
                    )
                )

                synthesis_output, retry_metadata = await self._ai.generate_json_with_metadata(
                    prompt=retry_prompt,
                    system_prompt=STRATEGIC_SYNTHESIS_SYSTEM,
                    temperature=0.1,  # Even lower temperature for retry
                    max_tokens=8192,
                )
                call_2_tokens += retry_metadata.get("input_tokens", 0) + retry_metadata.get("output_tokens", 0)

                # Re-check grounding after retry
                is_grounded, grounding_issues = await self._check_synthesis_grounding(
                    research_findings, synthesis_output
                )
                hallucination_count = len([i for i in grounding_issues if "HALLUCINATION" in i])
                logger.info(
                    "synthesis_retry_completed",
                    run_id=run_id,
                    hallucination_count_after_retry=hallucination_count,
                    is_grounded=is_grounded,
                )

            synthesis_issues.extend(grounding_issues)

            if not synthesis_valid or not is_grounded:
                logger.warning(
                    "synthesis_validation_failed",
                    run_id=run_id,
                    issues=synthesis_issues,
                    is_grounded=is_grounded,
                    hallucination_count=hallucination_count,
                )
                # Add issues to metadata for transparency
                if "synthesis_metadata" not in synthesis_output:
                    synthesis_output["synthesis_metadata"] = {}
                synthesis_output["synthesis_metadata"]["validation_issues"] = synthesis_issues
                synthesis_output["synthesis_metadata"]["grounding_passed"] = is_grounded
                synthesis_output["synthesis_metadata"]["hallucination_count"] = hallucination_count

            # Step 6: Parse synthesis into domain models
            logger.info("two_call_step", run_id=run_id, step="parse_synthesis")
            priorities, avoid, roadmap = self._parse_synthesis(synthesis_output)

            # Step 7: Generate premium report
            logger.info("two_call_step", run_id=run_id, step="generate_report")
            report = await self._generator.generate(
                request=request,
                score=ai_readiness,
                research_insights=research_findings,
                priorities=priorities,
                avoid=avoid,
                roadmap=roadmap,
                run_id=run_id,
            )

            # Step 7.5: Post-Generation QA (Phase 1 MVP - optional)
            if self._qa_orchestrator:
                logger.info("two_call_step", run_id=run_id, step="post_generation_qa")
                try:
                    qa_report = await self._qa_orchestrator.review(
                        run_id=run_id,
                        request=request,
                        final_report_html=report.html_content,
                    )
                    report.qa_report = qa_report

                    # Log to Google Sheets if logger available
                    if self._qa_sheets_logger:
                        await self._qa_sheets_logger.log_qa_report(qa_report)

                    logger.info(
                        "post_generation_qa_completed",
                        run_id=run_id,
                        overall_score=qa_report.overall_score,
                        passed=qa_report.passed,
                    )
                except Exception as e:
                    logger.error(
                        "post_generation_qa_failed",
                        run_id=run_id,
                        error=str(e),
                    )
                    # Don't fail the whole report if QA fails

            # Step 8: Aggregate QA validation
            logger.info("two_call_step", run_id=run_id, step="qa_validation")
            # Combine all QA results
            all_qa_issues = (
                call_1_qa.issues +
                call_2_qa.issues +
                cross_call_qa.issues +
                synthesis_issues
            )

            # QA passes if all validators pass AND hallucinations are minimal
            # Penalize QA score for each hallucination after retry
            grounding_penalty = min(hallucination_count, 3)  # Max 3 point penalty
            qa_passed = (
                call_1_qa.passed and
                call_2_qa.passed and
                cross_call_qa.passed and
                hallucination_count <= 2  # Allow up to 2 minor hallucinations
            )
            qa_score = max(1, min(call_1_qa.score, call_2_qa.score, cross_call_qa.score) - grounding_penalty)

            logger.info(
                "qa_validation_aggregate",
                run_id=run_id,
                qa_passed=qa_passed,
                qa_score=qa_score,
                call_1_passed=call_1_qa.passed,
                call_2_passed=call_2_qa.passed,
                cross_call_passed=cross_call_qa.passed,
                total_issues=len(all_qa_issues),
            )

            # Step 9: Payment and delivery
            payment_captured = False
            email_sent = False

            if qa_passed:
                if payment_intent_id and self._payment:
                    logger.info("two_call_step", run_id=run_id, step="capture_payment")
                    try:
                        await self._payment.capture_payment(payment_intent_id)
                        payment_captured = True
                    except Exception as e:
                        logger.error(
                            "two_call_payment_capture_failed",
                            run_id=run_id,
                            error=str(e),
                        )

                if self._email:
                    logger.info("two_call_step", run_id=run_id, step="send_email")
                    try:
                        await self._send_report_email(request, report)
                        email_sent = True
                    except Exception as e:
                        logger.error(
                            "two_call_email_failed",
                            run_id=run_id,
                            error=str(e),
                        )
            else:
                if payment_intent_id and self._payment:
                    logger.info("two_call_step", run_id=run_id, step="cancel_payment")
                    try:
                        await self._payment.cancel_payment(payment_intent_id)
                    except Exception as e:
                        logger.error(
                            "two_call_payment_cancel_failed",
                            run_id=run_id,
                            error=str(e),
                        )

            result = TwoCallResult(
                report=report,
                research_findings=research_findings,
                synthesis_output=synthesis_output,
                qa_passed=qa_passed,
                qa_score=qa_score,
                payment_captured=payment_captured,
                email_sent=email_sent,
                call_1_tokens=call_1_tokens,
                call_2_tokens=call_2_tokens,
                call_1_qa=call_1_qa,
                call_2_qa=call_2_qa,
                cross_call_qa=cross_call_qa,
                qa_issues=all_qa_issues,
                research_quality=quality_result,
                citations=citations,
            )

            # Step 10: Log QA results to Google Sheets
            if self._sheets_logger:
                logger.info("two_call_step", run_id=run_id, step="log_qa_to_sheets")
                try:
                    # Build summary for sheets
                    total_tokens = call_1_tokens + call_2_tokens
                    qa_summary = CompassQASummary(
                        run_id=run_id,
                        timestamp=datetime.now(),
                        company_name=request.company_name,
                        industry=request.industry,
                        pain_point=request.pain_point,
                        ai_readiness_score=ai_readiness.overall_score,
                        call_1_qa=call_1_qa,
                        call_2_qa=call_2_qa,
                        cross_call_qa=cross_call_qa,
                        overall_qa_passed=qa_passed,
                        total_tokens=total_tokens,
                        duration_seconds=(datetime.now() - start_call_1).total_seconds(),
                        email_sent=email_sent,
                        payment_captured=payment_captured,
                        top_issues=all_qa_issues[:3],
                    )

                    await self._sheets_logger.log_complete_run(qa_summary)
                except Exception as e:
                    logger.error(
                        "two_call_sheets_logging_failed",
                        run_id=run_id,
                        error=str(e),
                    )

            logger.info(
                "two_call_compass_completed",
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
                "two_call_compass_failed",
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

            return TwoCallResult(
                report=None,
                qa_passed=False,
                error=str(e),
            )

    async def _call_1_deep_research(
        self, request: CompassRequest
    ) -> tuple[dict, int, list[dict]]:
        """
        CALL 1: Deep Research with REAL web search.

        Gathers comprehensive data about the company, industry, and
        implementation patterns. Uses Claude's native web_search_20250305 tool.

        Returns:
            Tuple of (research_findings, total_tokens, citations)
        """
        user_prompt = DEEP_RESEARCH_USER_TEMPLATE.format(
            company_name=request.company_name,
            website=request.website or "Not provided",
            industry=request.industry,
            company_size=request.company_size,
            pain_point=request.pain_point,
            description=request.description,
            data_maturity=request.self_assessment.data_maturity,
            automation_experience=request.self_assessment.automation_experience,
            change_readiness=request.self_assessment.change_readiness,
        )

        try:
            # Use generate_json_with_web_search for REAL web research
            # This enables Claude's native web search tool
            research, metadata, citations = await self._ai.generate_json_with_web_search(
                prompt=user_prompt,
                system_prompt=DEEP_RESEARCH_SYSTEM,
                max_tokens=8192,  # Allow comprehensive research
                max_searches=15,  # Allow up to 15 web searches
            )

            # Calculate total tokens from metadata
            input_tokens = metadata.get("input_tokens", 0)
            output_tokens = metadata.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens

            # Inject citations into research findings
            if "_citations" not in research:
                research["_citations"] = citations
            if "research_metadata" not in research:
                research["research_metadata"] = {}
            research["research_metadata"]["citation_count"] = len(citations)
            research["research_metadata"]["web_searches_performed"] = metadata.get(
                "web_searches_performed", len(citations)
            )

            logger.info(
                "call_1_research_completed",
                company_name=request.company_name,
                total_findings=research.get("research_metadata", {}).get("total_findings", 0),
                sources_consulted=len(citations),
                citation_count=len(citations),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            return research, total_tokens, citations

        except Exception as e:
            logger.error("call_1_research_failed", error=str(e))
            # Return minimal structure on failure with empty citations
            return {
                "company_analysis": {},
                "industry_intelligence": {},
                "implementation_patterns": {},
                "research_metadata": {
                    "total_findings": 0,
                    "high_confidence_findings": 0,
                    "sources_consulted": 0,
                    "citation_count": 0,
                    "research_gaps": [f"Research failed: {str(e)}"],
                },
            }, 0, []

    async def _call_2_synthesis(
        self,
        request: CompassRequest,
        ai_readiness: AIReadinessScore,
        research_findings: dict,
    ) -> tuple[dict, int]:
        """
        CALL 2: Strategic Synthesis.

        Uses complete research context to generate prioritized recommendations,
        anti-recommendations, and 90-day roadmap.

        Returns:
            Tuple of (synthesis_output, total_tokens)
        """
        readiness_tier = get_readiness_tier(ai_readiness.overall_score)

        user_prompt = STRATEGIC_SYNTHESIS_USER_TEMPLATE.format(
            company_name=request.company_name,
            website=request.website or "Not provided",
            industry=request.industry,
            company_size=request.company_size,
            pain_point=request.pain_point,
            description=request.description,
            overall_score=f"{ai_readiness.overall_score:.1f}",
            self_assessment_score=f"{ai_readiness.self_assessment_score:.1f}",
            research_score=f"{ai_readiness.research_score:.1f}",
            readiness_tier=readiness_tier,
            data_maturity=request.self_assessment.data_maturity,
            automation_experience=request.self_assessment.automation_experience,
            change_readiness=request.self_assessment.change_readiness,
            research_findings=json.dumps(research_findings, indent=2),
        )

        try:
            # Use generate_json_with_metadata for token tracking
            # Moderate temperature (0.4) for balanced strategic thinking
            synthesis, metadata = await self._ai.generate_json_with_metadata(
                prompt=user_prompt,
                system_prompt=STRATEGIC_SYNTHESIS_SYSTEM,
                temperature=STRATEGIC_SYNTHESIS_TEMPERATURE,  # 0.4 - balanced creativity with grounding
                max_tokens=8192,
            )

            # Calculate total tokens from metadata
            input_tokens = metadata.get("input_tokens", 0)
            output_tokens = metadata.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens

            logger.info(
                "call_2_synthesis_completed",
                company_name=request.company_name,
                priorities_count=len(synthesis.get("priorities", [])),
                avoid_count=len(synthesis.get("avoid", [])),
                roadmap_months=len(synthesis.get("roadmap", [])),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            return synthesis, total_tokens

        except Exception as e:
            logger.error("call_2_synthesis_failed", error=str(e))
            raise

    def _validate_synthesis_quality(
        self, synthesis: dict, request: CompassRequest
    ) -> tuple[bool, list[str]]:
        """
        Validate synthesis output for hallucinations and semantic relevance.

        Checks:
        1. Suspicious patterns (placeholders, fake data)
        2. Research support citations
        3. Semantic relevance to client's pain point and industry

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for suspicious patterns that indicate hallucination
        suspicious_patterns = [
            "example.com",
            "placeholder",
            "lorem ipsum",
            "TBD",
            "XXX",
            "FIXME",
            "$999,999",  # Suspiciously round numbers
            "100% guaranteed",
            "unprecedented",
        ]

        # Convert synthesis to string for pattern checking
        synthesis_str = json.dumps(synthesis).lower()

        for pattern in suspicious_patterns:
            if pattern.lower() in synthesis_str:
                issues.append(f"Suspicious pattern found: '{pattern}'")

        # SEMANTIC RELEVANCE VALIDATION
        # Check that priorities relate to the client's pain point
        client_pain_point = request.pain_point.lower()
        client_industry = request.industry.lower()
        client_description = request.description.lower()

        # Extract key terms from client input
        pain_keywords = set(client_pain_point.split()) | set(client_description.split())
        # Remove common words
        stop_words = {"the", "a", "an", "is", "are", "we", "our", "to", "and", "of", "in", "for", "with", "on", "at"}
        pain_keywords = {w for w in pain_keywords if len(w) > 2 and w not in stop_words}

        # Check if priorities mention the client's industry or pain point
        priorities = synthesis.get("priorities", [])
        relevance_score = 0
        for priority in priorities:
            priority_text = json.dumps(priority).lower()
            # Check for industry mention
            if client_industry in priority_text:
                relevance_score += 1
            # Check for pain point keywords
            matching_keywords = [kw for kw in pain_keywords if kw in priority_text]
            if matching_keywords:
                relevance_score += len(matching_keywords)

        # If no priorities mention the pain point or industry, flag it
        if len(priorities) > 0 and relevance_score == 0:
            issues.append(
                f"SEMANTIC MISMATCH: Priorities don't reference client's pain point '{request.pain_point}' or industry '{request.industry}'"
            )

        # Check executive summary mentions company or pain point
        exec_summary = synthesis.get("executive_summary", {})
        if exec_summary:
            summary_text = json.dumps(exec_summary).lower()
            if request.company_name.lower() not in summary_text and client_industry not in summary_text:
                issues.append(
                    f"Executive summary doesn't mention company '{request.company_name}' or industry"
                )

        # Check priorities have research support
        for i, priority in enumerate(synthesis.get("priorities", [])):
            if not priority.get("research_support") and not priority.get("supporting_evidence"):
                issues.append(f"Priority {i+1} lacks research support citations")

            solution = priority.get("solution", {})
            # Check for made-up specific pricing without source
            pricing_str = str(solution.get("recommended_tools", []))
            if "$" in pricing_str and "Contact vendor" not in pricing_str and "estimate" not in pricing_str.lower():
                tools = solution.get("recommended_tools", [])
                for tool in tools:
                    if tool.get("pricing") and not tool.get("source"):
                        issues.append(f"Tool '{tool.get('name')}' has pricing without source - possible hallucination")

        # Check metadata acknowledges research gaps
        metadata = synthesis.get("synthesis_metadata", {})
        if not metadata.get("research_gaps_encountered") and not metadata.get("confidence_level"):
            issues.append("Synthesis metadata missing - may not reflect research quality")

        is_valid = len(issues) == 0
        if issues:
            logger.warning(
                "synthesis_quality_issues",
                issue_count=len(issues),
                issues=issues[:5],  # Log first 5 issues
            )

        return is_valid, issues

    async def _check_synthesis_grounding(
        self,
        research_findings: dict,
        synthesis_output: dict,
    ) -> tuple[bool, list[str]]:
        """
        AI-powered check that synthesis recommendations are grounded in research.

        Uses Claude to verify that priority recommendations and claims are
        actually supported by the research findings, not hallucinated.

        Returns:
            Tuple of (is_grounded, list_of_hallucination_issues)
        """
        # Build a focused prompt for grounding check
        # Use larger limits to avoid false positives from truncation
        research_summary = json.dumps(research_findings, indent=2)[:15000]
        synthesis_summary = json.dumps(synthesis_output, indent=2)[:8000]

        check_prompt = f"""Analyze if the SYNTHESIS recommendations are properly grounded in the RESEARCH findings.

RESEARCH FINDINGS:
{research_summary}

SYNTHESIS OUTPUT:
{synthesis_summary}

Check for:
1. Are the priority recommendations based on actual research findings?
2. Are any statistics, percentages, or specific claims fabricated (not from research)?
3. Are tool recommendations grounded in industry patterns from research?
4. Does the synthesis make claims that go beyond what the research supports?

Respond with valid JSON only:
{{
    "grounded": true/false,
    "confidence": 0.0-1.0,
    "hallucinations": ["list of specific ungrounded claims found"],
    "well_grounded_claims": ["list of claims properly supported by research"],
    "explanation": "brief explanation"
}}"""

        grounding_system = """You are a QA validator checking if AI recommendations are grounded in research.
A claim is grounded if it's directly supported by the research findings provided.
A claim is a hallucination if it makes up facts, statistics, or recommendations not in the research.

IMPORTANT - DO NOT FLAG THESE AS HALLUCINATIONS:
1. AI Readiness Score/Tier (e.g., "87.4/100", "Leading tier") - this is CALCULATED from user input, not from research
2. Company name and basic profile data - this comes from user input
3. Self-assessment scores (data_maturity, automation_experience, change_readiness) - user-provided
4. General strategic advice that doesn't cite specific statistics

ONLY FLAG AS HALLUCINATIONS:
1. Specific statistics with percentages (e.g., "reduces costs by 40%") that aren't in research
2. Case studies or company examples not mentioned in research
3. Industry reports or analyst quotes not in research (e.g., "According to McKinsey...")
4. Specific dollar figures or ROI claims not supported by research

Be strict but fair - flag only clear hallucinations, not reasonable inferences or calculated values."""

        try:
            result = await self._ai.generate_json(
                prompt=check_prompt,
                system_prompt=grounding_system,
                temperature=0.0,  # Deterministic for consistency
                max_tokens=1000,
            )

            is_grounded = result.get("grounded", True)
            hallucinations = result.get("hallucinations", [])
            confidence = result.get("confidence", 1.0)

            logger.info(
                "synthesis_grounding_check",
                is_grounded=is_grounded,
                confidence=confidence,
                hallucination_count=len(hallucinations),
            )

            issues = []
            if not is_grounded and hallucinations:
                for h in hallucinations[:5]:  # Limit to 5
                    issues.append(f"HALLUCINATION: {h}")

            return is_grounded, issues

        except Exception as e:
            logger.warning(
                "grounding_check_failed",
                error=str(e),
            )
            # Don't fail validation if grounding check fails
            return True, [f"Grounding check skipped: {e}"]

    def _score_research_quality(self, research: dict) -> float:
        """
        Score research quality (0-100) based on completeness and depth.
        """
        score = 0.0
        metadata = research.get("research_metadata", {})

        # Base score from findings count
        total_findings = metadata.get("total_findings", 0)
        if total_findings >= 20:
            score += 40
        elif total_findings >= 10:
            score += 30
        elif total_findings >= 5:
            score += 20
        elif total_findings > 0:
            score += 10

        # Bonus for high confidence findings
        high_confidence = metadata.get("high_confidence_findings", 0)
        if high_confidence >= 10:
            score += 20
        elif high_confidence >= 5:
            score += 10

        # Bonus for sources consulted
        sources = metadata.get("sources_consulted", 0)
        if sources >= 10:
            score += 20
        elif sources >= 5:
            score += 10

        # Bonus for complete sections
        if research.get("company_analysis"):
            score += 5
        if research.get("industry_intelligence"):
            score += 5
        if research.get("implementation_patterns"):
            score += 10

        return min(100.0, score)

    def _parse_synthesis(
        self, synthesis: dict
    ) -> tuple[list[BusinessPriority], list[AntiRecommendation], list[RoadmapPhase]]:
        """
        Parse synthesis JSON into domain models.
        """
        priorities = []
        for p in synthesis.get("priorities", []):
            solution_data = p.get("solution", {})
            solution = AISolution(
                name=solution_data.get("name", ""),
                approach_type=solution_data.get("approach_type", ""),
                description=solution_data.get("description", ""),
                why_this_fits=solution_data.get("why_this_fits", ""),
                tools=[t.get("name", "") for t in solution_data.get("recommended_tools", [])],
                expected_impact=solution_data.get("expected_impact", ""),
                complexity=solution_data.get("complexity", "Medium"),
            )
            priority = BusinessPriority(
                rank=p.get("rank", 0),
                problem_name=p.get("problem_name", ""),
                problem_description=p.get("problem_description", ""),
                solution=solution,
            )
            priorities.append(priority)

        avoid = []
        for a in synthesis.get("avoid", []):
            anti = AntiRecommendation(
                name=a.get("name", ""),
                why_tempting=a.get("why_tempting", ""),
                why_wrong_for_them=a.get("why_wrong_for_them", ""),
            )
            avoid.append(anti)

        roadmap = []
        for r in synthesis.get("roadmap", []):
            phase = RoadmapPhase(
                month=r.get("month", 0),
                focus=r.get("focus", ""),
                actions=r.get("actions", []),
                decision_gate=r.get("decision_gate", ""),
            )
            roadmap.append(phase)

        return priorities, avoid, roadmap

    async def _run_qa(self, report: CompassReport) -> tuple[bool, int | None]:
        """
        Run QA validation on the report.

        Returns:
            Tuple of (passed, score)
        """
        try:
            checks = [
                bool(report.html_content),
                len(report.html_content) > 1000,
                len(report.priorities) >= 1,
                len(report.roadmap) >= 1,
                report.ai_readiness_score.overall_score > 0,
            ]

            passed = all(checks)
            score = sum(checks) * 2

            logger.info(
                "two_call_qa_completed",
                run_id=report.run_id,
                passed=passed,
                score=score,
            )

            return passed, score

        except Exception as e:
            logger.error(
                "two_call_qa_failed",
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

        body = f"""
        <html>
        <body>
        <h2>Your AI Readiness Compass Report is Ready!</h2>
        <p>Dear {request.contact_name},</p>
        <p>Thank you for your purchase. Your AI Readiness Compass report for <strong>{request.company_name}</strong> is attached below.</p>
        <h3>Key Highlights:</h3>
        <ul>
            <li><strong>AI Readiness Score:</strong> {report.ai_readiness_score.overall_score:.0f}/100</li>
            <li><strong>Readiness Tier:</strong> {get_readiness_tier(report.ai_readiness_score.overall_score)}</li>
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

    async def close(self):
        """Cleanup resources."""
        pass
