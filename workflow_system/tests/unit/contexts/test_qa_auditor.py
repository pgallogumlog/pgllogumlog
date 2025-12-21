"""
Unit tests for the QA Auditor.
"""

import pytest
from datetime import datetime

from contexts.qa import QAAuditor, QAResult, Severity, FailureType
from contexts.qa.models import QAConfig
from contexts.workflow.models import (
    ConsensusResult,
    Phase,
    WorkflowProposal,
    WorkflowRecommendation,
    WorkflowResult,
)


@pytest.fixture
def sample_workflow_result():
    """Create a sample workflow result for testing."""
    return WorkflowResult(
        run_id="test-123",
        client_name="Test Client",
        business_name="Test Business",
        original_question="Test question",
        normalized_prompt="Normalized test prompt",
        research_pack={"businessSummary": "Test summary"},
        consensus=ConsensusResult(
            final_answer="support bot",
            total_responses=5,
            votes_for_winner=4,
            confidence_percent=80,
            consensus_strength="Strong",
            had_consensus=True,
            all_workflows=[
                WorkflowRecommendation(
                    name="Support Bot",
                    objective="Automate tickets",
                    tools=["n8n"],
                    description="AI chatbot",
                )
            ],
        ),
        proposal=WorkflowProposal(
            phases=[
                Phase(
                    phase_number=1,
                    phase_name="Quick Wins",
                    workflows=[
                        WorkflowRecommendation(
                            name="Support Bot",
                            objective="Automate tickets",
                            tools=["n8n"],
                            description="AI chatbot",
                        )
                    ],
                )
            ],
            recommendation="Start with Phase 1",
            html_body="<h1>Test</h1>",
            subject="Test Subject",
        ),
        timestamp=datetime.now(),
        tier="Standard",
    )


class TestQAResult:
    """Tests for QAResult model."""

    def test_to_dict(self):
        result = QAResult(
            score=8,
            passed=True,
            severity=Severity.LOW,
            failure_type=FailureType.NONE,
            failing_node_name="None",
            root_cause="Minor issue",
            suggested_prompt_fix="Add validation",
            critique="Good overall",
            run_id="test-123",
            client_name="Test Client",
        )

        data = result.to_dict()

        assert data["score"] == 8
        assert data["passed"] is True
        assert data["severity"] == "low"
        assert data["failure_type"] == "none"

    def test_to_sheets_row(self):
        result = QAResult(
            score=8,
            passed=True,
            severity=Severity.LOW,
            failure_type=FailureType.NONE,
            failing_node_name="None",
            root_cause="Minor issue",
            suggested_prompt_fix="Add validation",
            critique="Good overall",
            run_id="test-123",
            client_name="Test Client",
        )

        row = result.to_sheets_row()

        assert len(row) == 7
        assert row[1] == "test-123"
        assert row[2] == "Test Client"
        assert row[3] == 8
        assert row[4] == "PASS"


class TestSeverity:
    """Tests for Severity enum."""

    def test_base_scores(self):
        assert Severity.CRITICAL.base_score == 2
        assert Severity.HIGH.base_score == 5
        assert Severity.MEDIUM.base_score == 7
        assert Severity.LOW.base_score == 8
        assert Severity.NONE.base_score == 10


@pytest.mark.asyncio
class TestQAAuditor:
    """Tests for QAAuditor class."""

    async def test_audit_passing(self, mock_ai_provider, sample_workflow_result):
        """Test audit with passing result."""
        # Set up mock to return passing result
        mock_ai_provider.set_json_responses([
            {
                "score": 10,
                "pass": True,
                "severity": "none",
                "failureType": "none",
                "failingNodeName": "None",
                "rootCause": "No issues found",
                "suggestedPromptFix": "None needed",
                "critique": "Workflow is production-ready",
            }
        ])

        auditor = QAAuditor(ai_provider=mock_ai_provider)
        result = await auditor.audit(sample_workflow_result)

        assert result.score == 10
        assert result.passed is True
        assert result.severity == Severity.NONE

    async def test_audit_failing(self, mock_ai_provider, sample_workflow_result):
        """Test audit with failing result."""
        mock_ai_provider.set_json_responses([
            {
                "score": 5,
                "pass": False,
                "severity": "high",
                "failureType": "logic_error",
                "failingNodeName": "Vote Counter",
                "rootCause": "Consensus threshold too low",
                "suggestedPromptFix": "Increase minimum votes",
                "critique": "Logic error in voting",
            }
        ])

        auditor = QAAuditor(ai_provider=mock_ai_provider)
        result = await auditor.audit(sample_workflow_result)

        assert result.score == 5
        assert result.passed is False
        assert result.severity == Severity.HIGH
        assert result.failure_type == FailureType.LOGIC_ERROR

    async def test_build_audit_payload(self, mock_ai_provider, sample_workflow_result):
        """Test audit payload construction."""
        auditor = QAAuditor(ai_provider=mock_ai_provider)
        payload = auditor._build_audit_payload(sample_workflow_result)

        assert "meta" in payload
        assert payload["meta"]["runId"] == "test-123"
        assert payload["meta"]["clientName"] == "Test Client"
        assert "inputs" in payload
        assert "logic" in payload
        assert "outputs" in payload
