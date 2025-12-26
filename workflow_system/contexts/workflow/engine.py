"""
Workflow Engine - Main orchestrator for the Self-Consistency workflow.

This is the primary public API for the workflow context.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import structlog

from config.dependency_injection import AIProvider
from contexts.workflow.models import (
    ConsensusResult,
    EmailInquiry,
    Phase,
    WorkflowProposal,
    WorkflowRecommendation,
    WorkflowResult,
)
from contexts.workflow.prompts import (
    GROUPER_SYSTEM,
    INPUT_REWRITER_SYSTEM,
    RESEARCH_ENGINE_SYSTEM,
    SELF_CONSISTENCY_SYSTEM,
)
from contexts.workflow.voter import count_votes

if TYPE_CHECKING:
    from contexts.qa.models import WorkflowQAResult
    from contexts.qa.sheets_logger import QASheetsLogger
    from infrastructure.ai.capturing_adapter import CapturingAIAdapter

logger = structlog.get_logger()


class WorkflowEngine:
    """
    Main orchestrator for the Self-Consistency workflow.

    Processes email inquiries through:
    1. Input Rewriting (normalize prompt)
    2. Research Engine (generate research pack)
    3. Self-Consistency Voting (5 parallel runs)
    4. Grouper (organize into phases)
    5. Proposal Writer (generate HTML email)

    Optionally captures all AI calls for QA validation when using
    a CapturingAIAdapter.
    """

    def __init__(
        self,
        ai_provider: AIProvider,
        temperatures: Optional[list[float]] = None,
        min_consensus_votes: int = 3,
        qa_sheets_logger: Optional[QASheetsLogger] = None,
    ):
        """
        Initialize the workflow engine.

        Args:
            ai_provider: AI provider implementing AIProvider protocol.
                         Pass a CapturingAIAdapter to enable QA capture.
            temperatures: Temperature values for self-consistency runs
            min_consensus_votes: Minimum votes required for consensus
            qa_sheets_logger: Optional sheets logger for QA results
        """
        self._ai = ai_provider
        self._temperatures = temperatures or [0.4, 0.6, 0.8, 1.0, 1.2]
        self._min_consensus = min_consensus_votes
        self._qa_logger = qa_sheets_logger

        # Check if we have a capturing adapter for QA
        self._is_capturing = hasattr(ai_provider, "call_store")

    @property
    def is_capturing(self) -> bool:
        """Check if QA capture is enabled."""
        return self._is_capturing

    def _push_context(self, context: str) -> None:
        """Push caller context onto stack for QA tracking."""
        if self._is_capturing:
            self._ai.push_context(context)

    def _pop_context(self) -> None:
        """Pop caller context from stack."""
        if self._is_capturing:
            self._ai.pop_context()

    async def process_inquiry(
        self,
        inquiry: EmailInquiry,
        tier: str = "Standard",
    ) -> tuple[WorkflowResult, Optional[WorkflowQAResult]]:
        """
        Process an email inquiry through the full workflow.

        Args:
            inquiry: The incoming email inquiry
            tier: Service tier (Budget/Standard/Premium)

        Returns:
            Tuple of (WorkflowResult, Optional[WorkflowQAResult])
            QA result is None if QA capture is not enabled.
        """
        run_id = str(uuid.uuid4())[:8]
        logger.info(
            "workflow_started",
            run_id=run_id,
            tier=tier,
            from_email=inquiry.from_email,
            qa_enabled=self._is_capturing,
        )

        # Step 1: Normalize the input prompt
        self._push_context("WorkflowEngine._rewrite_input")
        normalized_prompt = await self._rewrite_input(inquiry.body)
        self._pop_context()
        logger.debug("input_rewritten", run_id=run_id)

        # Step 2: Generate research pack
        self._push_context("WorkflowEngine._run_research")
        research_pack = await self._run_research(normalized_prompt)
        self._pop_context()
        logger.debug("research_complete", run_id=run_id)

        # Step 3: Run self-consistency voting
        self._push_context("WorkflowEngine._run_self_consistency")
        consensus = await self._run_self_consistency(
            normalized_prompt=normalized_prompt,
            research_pack=research_pack,
        )
        self._pop_context()
        logger.info(
            "self_consistency_complete",
            run_id=run_id,
            consensus_strength=consensus.consensus_strength,
            confidence=consensus.confidence_percent,
        )

        # Step 4: Group workflows into phases
        self._push_context("WorkflowEngine._run_grouper")
        grouped = await self._run_grouper(
            question=inquiry.body,
            consensus=consensus,
            research_pack=research_pack,
        )
        self._pop_context()
        logger.debug("grouper_complete", run_id=run_id)

        # Step 5: Extract identity
        client_name, business_name = self._extract_identity(
            inquiry=inquiry,
            normalized_prompt=normalized_prompt,
        )

        # Step 6: Generate proposal HTML
        proposal = self._generate_proposal(
            phases=grouped.get("phases", []),
            recommendation=grouped.get("recommendation", ""),
            client_name=client_name,
            business_name=business_name,
        )

        result = WorkflowResult(
            run_id=run_id,
            client_name=client_name,
            business_name=business_name,
            original_question=inquiry.body,
            normalized_prompt=normalized_prompt,
            research_pack=research_pack,
            consensus=consensus,
            proposal=proposal,
            timestamp=datetime.now(),
            tier=tier,
        )

        logger.info(
            "workflow_complete",
            run_id=run_id,
            workflow_count=len(consensus.all_workflows),
            phase_count=len(proposal.phases),
        )

        # Step 7: Run QA analysis if capturing is enabled
        qa_result = None
        if self._is_capturing:
            qa_result = await self._run_qa_analysis(result, client_name)

        return result, qa_result

    async def _run_qa_analysis(
        self,
        workflow_result: WorkflowResult,
        client_name: str,
    ) -> Optional[WorkflowQAResult]:
        """
        Run QA analysis on captured AI calls.

        Args:
            workflow_result: The completed workflow result
            client_name: Name of the client

        Returns:
            WorkflowQAResult with scores and details
        """
        from contexts.qa.auditor import QAAuditor
        from contexts.qa.scoring import WorkflowScorer

        try:
            # Get the call store from the capturing adapter
            call_store = self._ai.call_store

            # Run semantic analysis using QAAuditor
            self._push_context("QAAuditor.audit")
            auditor = QAAuditor(ai_provider=self._ai)
            semantic_result = await auditor.audit(workflow_result)
            self._pop_context()

            # Score the workflow
            scorer = WorkflowScorer()
            qa_result = scorer.score(call_store, semantic_result)
            qa_result.client_name = client_name

            logger.info(
                "qa_analysis_complete",
                run_id=workflow_result.run_id,
                overall_score=qa_result.overall_score,
                passed=qa_result.passed,
                total_calls=qa_result.total_calls,
                calls_failed=qa_result.calls_failed,
            )

            # Log to sheets if configured
            if self._qa_logger:
                await self._qa_logger.log_complete_workflow(
                    call_store=call_store,
                    client_name=client_name,
                    semantic_result=semantic_result,
                )

            return qa_result

        except Exception as e:
            logger.error(
                "qa_analysis_failed",
                run_id=workflow_result.run_id,
                error=str(e),
            )
            return None

    async def _rewrite_input(self, raw_input: str) -> str:
        """Normalize and rewrite the input prompt."""
        return await self._ai.generate(
            prompt=raw_input,
            system_prompt=INPUT_REWRITER_SYSTEM,
            temperature=0.0,
            max_tokens=3000,
        )

    async def _run_research(self, normalized_prompt: str) -> dict:
        """Generate research pack about the business."""
        return await self._ai.generate_json(
            prompt=normalized_prompt,
            system_prompt=RESEARCH_ENGINE_SYSTEM,
            temperature=0.0,
            max_tokens=6000,
        )

    async def _run_self_consistency(
        self,
        normalized_prompt: str,
        research_pack: dict,
    ) -> ConsensusResult:
        """Run self-consistency voting with multiple temperatures."""
        import json
        from contexts.workflow.voter import validate_response_has_table

        # Build the prompt with research pack
        styles = [
            "Be very logical",
            "Think creatively",
            "Be practical",
            "Focus on ROI",
            "Prioritize scalability",
        ]

        prompt_template = """NORMALIZED PROMPT:
{prompt}

RESEARCH PACK (JSON):
{research}

STYLE HINT: {style}"""

        prompt = prompt_template.format(
            prompt=normalized_prompt,
            research=json.dumps(research_pack),
            style=styles[0],  # First style
        )

        # Generate responses in parallel
        responses = await self._ai.generate_parallel(
            prompt=prompt,
            system_prompt=SELF_CONSISTENCY_SYSTEM,
            temperatures=self._temperatures,
            max_tokens=8192,
        )

        # Validate and retry invalid responses
        final_responses = []
        valid_count = 0
        invalid_count = 0
        retry_count = 0
        max_retries = 2

        for idx, response in enumerate(responses):
            is_valid, error_msg = validate_response_has_table(response)

            if is_valid:
                final_responses.append(response)
                valid_count += 1
                logger.debug(
                    "sc_response_valid",
                    temperature=self._temperatures[idx],
                    index=idx,
                )
            else:
                # Retry invalid response
                invalid_count += 1
                retry_count += 1
                logger.warning(
                    "sc_response_invalid_retrying",
                    temperature=self._temperatures[idx],
                    index=idx,
                    error=error_msg,
                )

                retried_response = await self._retry_single_response(
                    prompt=prompt,
                    temperature=self._temperatures[idx],
                    max_retries=max_retries,
                    original_error=error_msg,
                )

                # Validate retry result
                retry_valid, retry_error = validate_response_has_table(retried_response)
                if retry_valid:
                    valid_count += 1
                else:
                    invalid_count += 1

                final_responses.append(retried_response)

        # Batch-level validation: ensure minimum valid responses
        min_valid_responses = 3
        if valid_count < min_valid_responses:
            logger.error(
                "sc_batch_validation_failed",
                valid_count=valid_count,
                invalid_count=invalid_count,
                total=len(responses),
                min_required=min_valid_responses,
                message=f"Only {valid_count}/{len(responses)} responses are valid. Need at least {min_valid_responses}.",
            )
        else:
            logger.info(
                "sc_batch_validation_passed",
                valid_count=valid_count,
                invalid_count=invalid_count,
                total=len(responses),
            )

        # Count votes and determine consensus
        return count_votes(
            responses=final_responses,
            min_consensus_votes=self._min_consensus,
            valid_count=valid_count,
            invalid_count=invalid_count,
            retry_count=retry_count,
            normalized_prompt=normalized_prompt,
        )

    async def _retry_single_response(
        self,
        prompt: str,
        temperature: float,
        max_retries: int,
        original_error: str,
    ) -> str:
        """
        Retry a single failed response up to max_retries times.

        Args:
            prompt: The prompt to send
            temperature: Temperature for this response
            max_retries: Maximum retry attempts
            original_error: Error from original response

        Returns:
            Response string (may still be invalid if all retries fail)
        """
        from contexts.workflow.voter import validate_response_has_table

        for attempt in range(max_retries):
            logger.info(
                "sc_retrying_response",
                temperature=temperature,
                attempt=attempt + 1,
                max_retries=max_retries,
            )

            # Enhanced prompt for retry with explicit warning
            enhanced_prompt = f"""{prompt}

⚠️ CRITICAL: Previous response was REJECTED due to: {original_error}
You MUST include a complete markdown table with all required columns and rows.
Your response will be REJECTED again if the table is missing or incomplete."""

            response = await self._ai.generate(
                prompt=enhanced_prompt,
                system_prompt=SELF_CONSISTENCY_SYSTEM,
                temperature=temperature,
                max_tokens=8192,
            )

            is_valid, error_msg = validate_response_has_table(response)

            if is_valid:
                logger.info(
                    "sc_retry_successful",
                    temperature=temperature,
                    attempt=attempt + 1,
                )
                return response
            else:
                logger.warning(
                    "sc_retry_failed",
                    temperature=temperature,
                    attempt=attempt + 1,
                    error=error_msg,
                )

        # All retries exhausted - return last response (will be marked invalid by voter)
        logger.error(
            "sc_all_retries_exhausted",
            temperature=temperature,
            max_retries=max_retries,
        )
        return response  # Return last attempt even if invalid

    async def _run_grouper(
        self,
        question: str,
        consensus: ConsensusResult,
        research_pack: dict,
    ) -> dict:
        """Organize workflows into implementation phases."""
        import json

        user_content = {
            "question": question,
            "finalAnswer": consensus.final_answer,
            "stats": {
                "totalResponses": consensus.total_responses,
                "votesForWinner": consensus.votes_for_winner,
                "confidencePercent": consensus.confidence_percent,
                "consensusStrength": consensus.consensus_strength,
            },
            "allWorkflows": [
                {
                    "name": w.name,
                    "objective": w.objective,
                    "tools": w.tools,
                    "description": w.description,
                }
                for w in consensus.all_workflows
            ],
            "researchPack": research_pack,
        }

        return await self._ai.generate_json(
            prompt=json.dumps(user_content),
            system_prompt=GROUPER_SYSTEM,
            temperature=0.3,
            max_tokens=8192,
        )

    def _extract_identity(
        self,
        inquiry: EmailInquiry,
        normalized_prompt: str,
    ) -> tuple[str, str]:
        """Extract client name and business name from inquiry."""
        # Client name from email
        client_name = inquiry.from_name or "Client"

        # Business name from prompt patterns
        business_name = "Your Business"
        patterns = [
            r"(?:analyze|assess|review)\s+(.+?)\s+at\s+https?:",
            r"advising\s+(.+?),\s+a\b",
            r"for\s+(.+?)\s+at\s+https?:",
            r"(?:help|assist)\s+(.+?)\s+in",
        ]

        for pattern in patterns:
            match = re.search(pattern, normalized_prompt, re.IGNORECASE)
            if match:
                business_name = match.group(1).strip()
                break

        return client_name, business_name

    def _generate_proposal(
        self,
        phases: list[dict],
        recommendation: str,
        client_name: str,
        business_name: str,
    ) -> WorkflowProposal:
        """Generate the HTML proposal email."""
        # Convert dict phases to Phase objects
        phase_objects = []
        for p in phases:
            workflows = [
                WorkflowRecommendation(
                    name=w.get("name", ""),
                    objective=w.get("objective", ""),
                    tools=w.get("tools", []) if isinstance(w.get("tools"), list) else [],
                    description=w.get("description", ""),
                )
                for w in p.get("workflows", [])
            ]
            phase_objects.append(Phase(
                phase_number=p.get("phaseNumber", 0),
                phase_name=p.get("phaseName", ""),
                workflows=workflows,
            ))

        # Generate HTML
        html = self._render_proposal_html(
            phases=phase_objects,
            recommendation=recommendation,
            client_name=client_name,
            business_name=business_name,
        )

        return WorkflowProposal(
            phases=phase_objects,
            recommendation=recommendation,
            html_body=html,
            subject=f"AI Workflow Proposal for {business_name} – Phased Rollout",
        )

    def _render_proposal_html(
        self,
        phases: list[Phase],
        recommendation: str,
        client_name: str,
        business_name: str,
    ) -> str:
        """Render the proposal as HTML."""
        html = f"""
<h2 style="color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 8px;">
    AI Workflow Proposal
</h2>

<p>Dear <strong>{client_name}</strong>,</p>

<p>Here is your custom AI automation roadmap for <strong>{business_name}</strong>:</p>

<div style="background: #e7f3ff; padding: 12px; border-left: 4px solid #007bff; margin: 15px 0;">
    <p><strong>Recommendation:</strong> {recommendation}</p>
</div>
"""

        for phase in phases:
            html += f"""
<div style="background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
    <h3 style="margin-top: 0; color: #007bff;">Phase {phase.phase_number}: {phase.phase_name}</h3>
"""
            for wf in phase.workflows:
                tools_str = ", ".join(wf.tools) if wf.tools else "To be determined"
                html += f"""
    <div style="margin: 15px 0; padding: 10px; border-left: 3px solid #007bff;">
        <p><strong>{wf.name}</strong><br>
        <em>{wf.objective}</em></p>

        <p><strong>Implementation Steps (n8n)</strong></p>
        <ol style="margin: 5px 0 10px 20px;">
            <li>Trigger Node</li>
            <li><em>AI Agent</em> – {wf.objective}</li>
            <li>IF Node – Confidence ≥90%</li>
            <li>Auto-Action / Log</li>
        </ol>

        <p><strong>Tools:</strong> {tools_str}<br>
        {f'<strong>Description:</strong> {wf.description}' if wf.description else ''}</p>
    </div>
"""
            html += "</div>"

        html += f"""
<p><small>Generated on {datetime.now().strftime('%Y-%m-%d')} by Workflow Automation System</small></p>
"""
        return html
