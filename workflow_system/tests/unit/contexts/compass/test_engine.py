"""
Unit tests for Compass Engine.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from contexts.compass.models import (
    SelfAssessment,
    CompassRequest,
    AIReadinessScore,
    BusinessPriority,
    AISolution,
    AntiRecommendation,
    RoadmapPhase,
    CompassReport,
)
from contexts.compass.agents.orchestrator import ResearchInsights
from contexts.compass.engine import CompassEngine, CompassResult


class MockAIProvider:
    """Mock AI provider for testing."""

    def __init__(self):
        self.generate = AsyncMock(return_value="Generated content")
        self.generate_json = AsyncMock(
            return_value={
                "priorities": [
                    {
                        "rank": 1,
                        "problem_name": "Customer Support",
                        "problem_description": "High ticket volume",
                        "solution": {
                            "name": "RAG Support Bot",
                            "approach_type": "RAG",
                            "description": "Knowledge-based chatbot",
                            "why_this_fits": "Matches readiness level",
                            "tools": ["Claude"],
                            "expected_impact": "40% reduction",
                            "complexity": "Medium",
                        },
                    }
                ],
                "avoid": [
                    {
                        "name": "Full Autonomous Agent",
                        "why_tempting": "Complete automation",
                        "why_wrong_for_them": "Too complex",
                    }
                ],
                "roadmap": [
                    {
                        "month": 1,
                        "focus": "Quick Win",
                        "actions": ["Deploy bot"],
                        "decision_gate": "20% deflection",
                    }
                ],
            }
        )


class MockPaymentClient:
    """Mock payment client for testing."""

    def __init__(self):
        self.capture_payment = AsyncMock(return_value=MagicMock(success=True))
        self.cancel_payment = AsyncMock(return_value=MagicMock(success=True))


class MockEmailClient:
    """Mock email client for testing."""

    def __init__(self):
        self.send = AsyncMock(return_value=True)


@pytest.fixture
def sample_request():
    """Create sample CompassRequest."""
    return CompassRequest(
        company_name="Acme Corp",
        website="https://acme.com",
        industry="Technology",
        company_size="50-200",
        self_assessment=SelfAssessment(3, 4, 3),
        pain_point="Customer support overload",
        description="We're drowning in support tickets",
        email="ceo@acme.com",
        contact_name="John Smith",
    )


@pytest.fixture
def mock_ai_provider():
    """Create mock AI provider."""
    return MockAIProvider()


@pytest.fixture
def mock_payment_client():
    """Create mock payment client."""
    return MockPaymentClient()


@pytest.fixture
def mock_email_client():
    """Create mock email client."""
    return MockEmailClient()


class TestCompassEngine:
    """Tests for CompassEngine."""

    @pytest.mark.asyncio
    async def test_returns_compass_result(
        self, sample_request, mock_ai_provider
    ):
        """Should return CompassResult."""
        engine = CompassEngine(ai_provider=mock_ai_provider)

        result = await engine.process(sample_request)

        assert isinstance(result, CompassResult)

    @pytest.mark.asyncio
    async def test_result_contains_report(
        self, sample_request, mock_ai_provider
    ):
        """Should return result with report."""
        engine = CompassEngine(ai_provider=mock_ai_provider)

        result = await engine.process(sample_request)

        assert result.report is not None
        assert isinstance(result.report, CompassReport)

    @pytest.mark.asyncio
    async def test_report_contains_company_name(
        self, sample_request, mock_ai_provider
    ):
        """Should include company name in report."""
        engine = CompassEngine(ai_provider=mock_ai_provider)

        result = await engine.process(sample_request)

        assert result.report.company_name == "Acme Corp"

    @pytest.mark.asyncio
    async def test_calculates_hybrid_score(
        self, sample_request, mock_ai_provider
    ):
        """Should calculate hybrid AI readiness score."""
        engine = CompassEngine(ai_provider=mock_ai_provider)

        result = await engine.process(sample_request)

        score = result.report.ai_readiness_score
        assert score.overall_score > 0
        assert score.overall_score <= 100
        # Should be weighted: 30% self + 70% research
        assert score.self_assessment_score > 0
        assert score.research_score > 0

    @pytest.mark.asyncio
    async def test_includes_priorities(
        self, sample_request, mock_ai_provider
    ):
        """Should include business priorities in report."""
        engine = CompassEngine(ai_provider=mock_ai_provider)

        result = await engine.process(sample_request)

        assert len(result.report.priorities) >= 1
        assert result.report.priorities[0].problem_name == "Customer Support"

    @pytest.mark.asyncio
    async def test_includes_roadmap(
        self, sample_request, mock_ai_provider
    ):
        """Should include roadmap in report."""
        engine = CompassEngine(ai_provider=mock_ai_provider)

        result = await engine.process(sample_request)

        assert len(result.report.roadmap) >= 1

    @pytest.mark.asyncio
    async def test_includes_anti_recommendations(
        self, sample_request, mock_ai_provider
    ):
        """Should include anti-recommendations in report."""
        engine = CompassEngine(ai_provider=mock_ai_provider)

        result = await engine.process(sample_request)

        assert len(result.report.avoid) >= 1

    @pytest.mark.asyncio
    async def test_generates_html_content(
        self, sample_request, mock_ai_provider
    ):
        """Should generate HTML content."""
        engine = CompassEngine(ai_provider=mock_ai_provider)

        result = await engine.process(sample_request)

        assert result.report.html_content is not None
        assert len(result.report.html_content) > 0

    @pytest.mark.asyncio
    async def test_runs_qa_validation(
        self, sample_request, mock_ai_provider
    ):
        """Should run QA validation."""
        engine = CompassEngine(ai_provider=mock_ai_provider)

        result = await engine.process(sample_request)

        # QA should have run
        assert result.qa_score is not None

    @pytest.mark.asyncio
    async def test_qa_passes_for_valid_report(
        self, sample_request, mock_ai_provider
    ):
        """QA should pass for valid report."""
        engine = CompassEngine(ai_provider=mock_ai_provider)

        result = await engine.process(sample_request)

        assert result.qa_passed is True

    @pytest.mark.asyncio
    async def test_captures_payment_on_qa_pass(
        self, sample_request, mock_ai_provider, mock_payment_client
    ):
        """Should capture payment when QA passes."""
        engine = CompassEngine(
            ai_provider=mock_ai_provider,
            payment_client=mock_payment_client,
        )

        result = await engine.process(
            sample_request,
            payment_intent_id="pi_test123",
        )

        assert result.qa_passed is True
        mock_payment_client.capture_payment.assert_called_once_with("pi_test123")
        assert result.payment_captured is True

    @pytest.mark.asyncio
    async def test_sends_email_on_qa_pass(
        self, sample_request, mock_ai_provider, mock_email_client
    ):
        """Should send email when QA passes."""
        engine = CompassEngine(
            ai_provider=mock_ai_provider,
            email_client=mock_email_client,
        )

        result = await engine.process(sample_request)

        assert result.qa_passed is True
        mock_email_client.send.assert_called_once()
        assert result.email_sent is True

    @pytest.mark.asyncio
    async def test_email_sent_to_correct_recipient(
        self, sample_request, mock_ai_provider, mock_email_client
    ):
        """Should send email to the customer's email."""
        engine = CompassEngine(
            ai_provider=mock_ai_provider,
            email_client=mock_email_client,
        )

        await engine.process(sample_request)

        call_kwargs = mock_email_client.send.call_args[1]
        assert call_kwargs["to"] == "ceo@acme.com"
        assert "Acme Corp" in call_kwargs["subject"]

    @pytest.mark.asyncio
    async def test_handles_ai_error_with_fallback(
        self, sample_request
    ):
        """Should handle AI errors gracefully with fallback content."""
        # Engine has fallback behavior - it still produces reports with default content
        failing_provider = MockAIProvider()
        failing_provider.generate_json = AsyncMock(side_effect=Exception("API Error"))

        engine = CompassEngine(ai_provider=failing_provider)

        result = await engine.process(sample_request)

        # Should still produce a report using fallback defaults
        assert result.report is not None
        assert result.qa_passed is True  # Fallback content passes basic QA
        assert len(result.report.priorities) >= 1  # Has default priority

    @pytest.mark.asyncio
    async def test_captures_payment_even_with_ai_fallback(
        self, sample_request, mock_payment_client
    ):
        """Should still capture payment when using AI fallback content."""
        # Engine has fallback - reports are still generated and QA passes
        failing_provider = MockAIProvider()
        failing_provider.generate_json = AsyncMock(side_effect=Exception("API Error"))

        engine = CompassEngine(
            ai_provider=failing_provider,
            payment_client=mock_payment_client,
        )

        result = await engine.process(
            sample_request,
            payment_intent_id="pi_test123",
        )

        # Payment should be captured because fallback produces valid report
        assert result.qa_passed is True
        mock_payment_client.capture_payment.assert_called_once_with("pi_test123")

    @pytest.mark.asyncio
    async def test_generates_unique_run_id(
        self, sample_request, mock_ai_provider
    ):
        """Should generate unique run_id for each request."""
        engine = CompassEngine(ai_provider=mock_ai_provider)

        result1 = await engine.process(sample_request)
        result2 = await engine.process(sample_request)

        assert result1.report.run_id != result2.report.run_id
        assert result1.report.run_id.startswith("compass-")


class TestHybridScoring:
    """Tests for hybrid scoring calculation."""

    @pytest.mark.asyncio
    async def test_hybrid_score_weighting(
        self, sample_request, mock_ai_provider
    ):
        """Should weight: 30% self-assessment + 70% research."""
        engine = CompassEngine(ai_provider=mock_ai_provider)

        result = await engine.process(sample_request)

        score = result.report.ai_readiness_score
        # Verify the weights are applied correctly
        expected_overall = (
            score.self_assessment_score * 0.30
            + score.research_score * 0.70
        )
        assert abs(score.overall_score - expected_overall) < 0.01

    @pytest.mark.asyncio
    async def test_self_assessment_contributes_30_percent(
        self, mock_ai_provider
    ):
        """Self-assessment should contribute 30% to overall score."""
        # High self-assessment, assuming research returns moderate score
        high_self_request = CompassRequest(
            company_name="Test Corp",
            website="https://test.com",
            industry="Technology",
            company_size="50-200",
            self_assessment=SelfAssessment(5, 5, 5),  # Max scores
            pain_point="Test",
            description="Test",
            email="test@test.com",
            contact_name="Test User",
        )

        low_self_request = CompassRequest(
            company_name="Test Corp",
            website="https://test.com",
            industry="Technology",
            company_size="50-200",
            self_assessment=SelfAssessment(1, 1, 1),  # Min scores
            pain_point="Test",
            description="Test",
            email="test@test.com",
            contact_name="Test User",
        )

        engine = CompassEngine(ai_provider=mock_ai_provider)

        high_result = await engine.process(high_self_request)
        low_result = await engine.process(low_self_request)

        # Higher self-assessment should yield higher overall score
        assert (
            high_result.report.ai_readiness_score.overall_score
            > low_result.report.ai_readiness_score.overall_score
        )
