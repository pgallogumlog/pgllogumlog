"""
Unit tests for the Workflow Engine.
"""

import pytest

from contexts.workflow import WorkflowEngine
from contexts.workflow.models import EmailInquiry


@pytest.mark.asyncio
class TestWorkflowEngine:
    """Tests for WorkflowEngine class."""

    async def test_process_inquiry_basic(self, mock_ai_provider, sample_email_inquiry):
        """Test basic workflow processing."""
        engine = WorkflowEngine(
            ai_provider=mock_ai_provider,
            temperatures=[0.5, 0.7],  # Fewer temps for faster test
            min_consensus_votes=1,
        )

        result, qa_result = await engine.process_inquiry(sample_email_inquiry)

        assert result.run_id is not None
        assert result.client_name == "Test User"
        assert len(result.consensus.all_workflows) > 0
        # QA result is None when not using CapturingAIAdapter
        assert qa_result is None

    async def test_process_inquiry_with_tier(self, mock_ai_provider, sample_email_inquiry):
        """Test workflow processing with tier."""
        engine = WorkflowEngine(
            ai_provider=mock_ai_provider,
            min_consensus_votes=1,
        )

        result, qa_result = await engine.process_inquiry(
            sample_email_inquiry,
            tier="Premium",
        )

        assert result.tier == "Premium"
        assert qa_result is None  # Not using CapturingAIAdapter

    async def test_extract_identity(self, mock_ai_provider):
        """Test identity extraction from inquiry."""
        engine = WorkflowEngine(ai_provider=mock_ai_provider)

        inquiry = EmailInquiry(
            message_id="test-123",
            from_email="john@example.com",
            from_name="John Smith",
            subject="Test",
            body="Analyze Starbucks at https://www.starbucks.com",
        )

        client_name, business_name = engine._extract_identity(
            inquiry=inquiry,
            normalized_prompt="analyze Starbucks at https://www.starbucks.com",
        )

        assert client_name == "John Smith"
        assert business_name == "Starbucks"

    async def test_extract_identity_no_name(self, mock_ai_provider):
        """Test identity extraction with no from_name."""
        engine = WorkflowEngine(ai_provider=mock_ai_provider)

        inquiry = EmailInquiry(
            message_id="test-123",
            from_email="john@example.com",
            from_name="",
            subject="Test",
            body="Test body",
        )

        client_name, business_name = engine._extract_identity(
            inquiry=inquiry,
            normalized_prompt="Some prompt without business pattern",
        )

        assert client_name == "Client"
        assert business_name == "Your Business"


@pytest.mark.asyncio
class TestWorkflowEngineProposal:
    """Tests for proposal generation."""

    async def test_generate_proposal_html(self, mock_ai_provider):
        """Test HTML proposal generation."""
        engine = WorkflowEngine(ai_provider=mock_ai_provider)

        # Set up mock responses for grouper
        mock_ai_provider.set_json_responses([
            # Research response
            {"businessSummary": "Test"},
            # Grouper response
            {
                "phases": [
                    {
                        "phaseNumber": 1,
                        "phaseName": "Quick Wins",
                        "workflows": [
                            {
                                "name": "Support Bot",
                                "objective": "Automate tickets",
                                "tools": ["n8n", "OpenAI"],
                                "description": "AI chatbot",
                            }
                        ],
                    }
                ],
                "allWorkflows": [],
                "recommendation": "Start with Phase 1",
            },
        ])

        proposal = engine._generate_proposal(
            phases=[{
                "phaseNumber": 1,
                "phaseName": "Quick Wins",
                "workflows": [{
                    "name": "Support Bot",
                    "objective": "Automate tickets",
                    "tools": ["n8n"],
                    "description": "Test",
                }],
            }],
            recommendation="Start with Quick Wins",
            client_name="Test Client",
            business_name="Test Business",
        )

        assert "Test Client" in proposal.html_body
        assert "Test Business" in proposal.html_body
        assert "Phase 1: Quick Wins" in proposal.html_body
        assert "Support Bot" in proposal.html_body
