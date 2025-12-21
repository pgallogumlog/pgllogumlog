"""
QA Auditor - AI-powered quality analysis.

Analyzes workflow outputs for technical failures and assigns quality scores.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

import structlog

from config.dependency_injection import AIProvider, SheetsClient
from contexts.qa.models import FailureType, QAConfig, QAResult, Severity
from contexts.workflow.models import WorkflowResult

logger = structlog.get_logger()


QA_AUDITOR_SYSTEM = """You are a System Debugger for an AI Automation Agency. Analyze workflow traces for technical failures and assign quality scores.

**YOUR TASK**:
1. Identify ALL technical issues in the generated workflow output
2. Classify the MOST SEVERE issue found
3. Assign a quality score (1-10) based on severity
4. Provide actionable fix instructions

**SEVERITY CLASSIFICATION**:
- **CRITICAL** (score: 2): Workflow won't execute at all (syntax errors, missing required nodes, broken connections)
- **HIGH** (score: 5): Workflow executes but produces wrong results (logic errors, incorrect branching, data loss)
- **MEDIUM** (score: 7): Workflow works but has edge case bugs (missing validation, poor error handling)
- **LOW** (score: 8): Workflow functions well but has minor issues (suboptimal patterns, missing comments)
- **NONE** (score: 10): Workflow is production-ready with no issues detected

**OUTPUT STRICT JSON ONLY**:
{
    "score": 5,
    "pass": false,
    "severity": "high",
    "failureType": "logic_error",
    "failingNodeName": "Exact Node Name from workflow",
    "rootCause": "Brief explanation of the core problem",
    "suggestedPromptFix": "Specific instruction to add to the LLM prompt to prevent this issue",
    "critique": "Professional explanation of the issue and its impact"
}

**SCORING RULES**:
- Use the severity's base score (critical=2, high=5, medium=7, low=8, none=10)
- Pass = true if score >= 7, false otherwise
- If multiple issues exist, report only the MOST SEVERE one
- Be precise about which node has the problem
- Suggest fixes that can be added to the code generation prompt

**IMPORTANT**:
- Always output valid JSON
- Always include all required fields
- Score must match severity level
- If no issues found: score=10, severity="none", pass=true"""


class QAAuditor:
    """
    AI-powered quality auditor for workflow outputs.

    Analyzes workflow results and provides:
    - Quality scores (1-10)
    - Severity classification
    - Root cause analysis
    - Suggested fixes
    """

    def __init__(
        self,
        ai_provider: AIProvider,
        sheets_client: Optional[SheetsClient] = None,
        config: Optional[QAConfig] = None,
        qa_spreadsheet_id: Optional[str] = None,
    ):
        """
        Initialize the QA auditor.

        Args:
            ai_provider: AI provider for analysis
            sheets_client: Optional sheets client for logging
            config: QA configuration
            qa_spreadsheet_id: Spreadsheet ID for logging
        """
        self._ai = ai_provider
        self._sheets = sheets_client
        self._config = config or QAConfig()
        self._qa_spreadsheet_id = qa_spreadsheet_id

    async def audit(self, workflow_result: WorkflowResult) -> QAResult:
        """
        Audit a workflow result for quality issues.

        Args:
            workflow_result: The workflow output to analyze

        Returns:
            QAResult with score and analysis
        """
        logger.info(
            "qa_audit_started",
            run_id=workflow_result.run_id,
            client=workflow_result.client_name,
        )

        # Build the audit payload
        payload = self._build_audit_payload(workflow_result)

        try:
            # Call AI for analysis
            audit_response = await self._ai.generate_json(
                prompt=json.dumps(payload),
                system_prompt=QA_AUDITOR_SYSTEM,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            )

            # Parse the response
            result = self._parse_audit_response(
                audit_response,
                workflow_result,
            )

            logger.info(
                "qa_audit_complete",
                run_id=workflow_result.run_id,
                score=result.score,
                passed=result.passed,
                severity=result.severity.value,
            )

            return result

        except Exception as e:
            logger.error(
                "qa_audit_failed",
                run_id=workflow_result.run_id,
                error=str(e),
            )

            # Return a failure result
            return QAResult(
                score=0,
                passed=False,
                severity=Severity.CRITICAL,
                failure_type=FailureType.VALIDATION_ERROR,
                failing_node_name="QA Auditor",
                root_cause=f"QA analysis failed: {str(e)}",
                suggested_prompt_fix="Check QA auditor configuration",
                critique=f"QA Parser Error: {str(e)}",
                run_id=workflow_result.run_id,
                client_name=workflow_result.client_name,
            )

    def _build_audit_payload(self, result: WorkflowResult) -> dict[str, Any]:
        """Build the payload for the QA auditor."""
        return {
            "meta": {
                "runId": result.run_id,
                "clientName": result.client_name,
                "businessName": result.business_name,
                "timestamp": result.timestamp.isoformat(),
                "tier": result.tier,
                "phaseCount": len(result.proposal.phases),
                "workflowCount": len(result.consensus.all_workflows),
            },
            "inputs": {
                "originalQuestion": result.original_question[:500],  # Truncate for size
                "normalizedPrompt": result.normalized_prompt[:500],
            },
            "logic": {
                "consensus": {
                    "finalAnswer": result.consensus.final_answer,
                    "confidencePercent": result.consensus.confidence_percent,
                    "consensusStrength": result.consensus.consensus_strength,
                    "hadConsensus": result.consensus.had_consensus,
                    "totalResponses": result.consensus.total_responses,
                    "votesForWinner": result.consensus.votes_for_winner,
                },
                "workflowNames": [w.name for w in result.consensus.all_workflows],
            },
            "outputs": {
                "proposalSubject": result.proposal.subject,
                "recommendation": result.proposal.recommendation,
                "phases": [
                    {
                        "phaseNumber": p.phase_number,
                        "phaseName": p.phase_name,
                        "workflowCount": len(p.workflows),
                    }
                    for p in result.proposal.phases
                ],
            },
        }

    def _parse_audit_response(
        self,
        response: dict[str, Any],
        workflow_result: WorkflowResult,
    ) -> QAResult:
        """Parse the AI audit response into a QAResult."""
        # Extract fields with defaults
        score = response.get("score", 0)
        passed = response.get("pass", False)
        severity_str = response.get("severity", "critical").lower()
        failure_type_str = response.get("failureType", "validation_error").lower()

        # Map to enums
        try:
            severity = Severity(severity_str)
        except ValueError:
            severity = Severity.CRITICAL

        try:
            failure_type = FailureType(failure_type_str)
        except ValueError:
            failure_type = FailureType.VALIDATION_ERROR

        # Build critique with severity emoji
        severity_emoji = {
            Severity.CRITICAL: "🔴",
            Severity.HIGH: "🟠",
            Severity.MEDIUM: "🟡",
            Severity.LOW: "🟢",
            Severity.NONE: "✅",
        }.get(severity, "⚪")

        critique = response.get("critique", "")
        if severity != Severity.NONE:
            formatted_critique = (
                f"{severity_emoji} [MACHINE AUDIT]\n"
                f"Severity: {severity.value.upper()}\n"
                f"Type: {failure_type.value}\n"
                f"Node: {response.get('failingNodeName', 'Unknown')}\n"
                f"Cause: {response.get('rootCause', 'No cause specified')}\n\n"
                f"Details: {critique}"
            )
        else:
            formatted_critique = critique or "✅ Workflow passed all quality checks"

        return QAResult(
            score=score,
            passed=passed or score >= self._config.min_pass_score,
            severity=severity,
            failure_type=failure_type,
            failing_node_name=response.get("failingNodeName", "Unknown"),
            root_cause=response.get("rootCause", ""),
            suggested_prompt_fix=response.get("suggestedPromptFix", ""),
            critique=formatted_critique,
            run_id=workflow_result.run_id,
            client_name=workflow_result.client_name,
            timestamp=datetime.now(),
        )

    async def log_to_sheets(
        self,
        result: QAResult,
        sheet_name: str = "QA Logs",
    ) -> bool:
        """
        Log QA result to Google Sheets.

        Args:
            result: QA result to log
            sheet_name: Sheet tab name

        Returns:
            True if successful
        """
        if not self._sheets or not self._qa_spreadsheet_id:
            logger.warning("sheets_logging_not_configured")
            return False

        try:
            await self._sheets.append_row(
                spreadsheet_id=self._qa_spreadsheet_id,
                sheet_name=sheet_name,
                values=result.to_sheets_row(),
            )
            logger.info("qa_result_logged", run_id=result.run_id)
            return True
        except Exception as e:
            logger.error("qa_logging_failed", error=str(e))
            return False
