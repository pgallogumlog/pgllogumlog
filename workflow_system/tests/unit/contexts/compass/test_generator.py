"""
Unit tests for Compass Report Generator.
"""

import pytest
from unittest.mock import AsyncMock
from pathlib import Path

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
from contexts.compass.generator import CompassReportGenerator


class MockAIProvider:
    """Mock AI provider for testing."""

    def __init__(self, response: str = "Generated executive summary."):
        self.response = response
        self.generate = AsyncMock(return_value=self.response)


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
def sample_score():
    """Create sample AIReadinessScore."""
    return AIReadinessScore(
        self_assessment_score=66.0,
        research_score=60.0,
        overall_score=62.0,
        breakdown={"data": 60, "automation": 80, "change": 60},
    )


@pytest.fixture
def sample_research():
    """Create sample research insights."""
    return {
        "company": {
            "tech_signals": ["Modern website", "API integrations"],
            "key_findings": ["Good foundation"],
            "ai_opportunities": ["Support automation"],
        },
        "industry": {
            "ai_maturity": "growing",
            "common_use_cases": ["Chatbots", "Analytics"],
            "competitor_adoption": "medium",
        },
    }


@pytest.fixture
def sample_priorities():
    """Create sample business priorities."""
    return [
        BusinessPriority(
            rank=1,
            problem_name="Customer Support",
            problem_description="High ticket volume",
            solution=AISolution(
                name="RAG Support Bot",
                approach_type="RAG",
                description="Knowledge-based chatbot",
                why_this_fits="Matches readiness level",
                tools=["Claude", "Pinecone"],
                expected_impact="40% ticket reduction",
                complexity="Medium",
            ),
        ),
        BusinessPriority(
            rank=2,
            problem_name="Data Entry",
            problem_description="Manual processes",
            solution=AISolution(
                name="Document Processor",
                approach_type="Agentic",
                description="Auto-process documents",
                why_this_fits="Simple implementation",
                tools=["Claude", "n8n"],
                expected_impact="60% time savings",
                complexity="Low",
            ),
        ),
    ]


@pytest.fixture
def sample_avoid():
    """Create sample anti-recommendations."""
    return [
        AntiRecommendation(
            name="Full Autonomous Agent",
            why_tempting="Complete automation promise",
            why_wrong_for_them="Requires data maturity you lack",
        ),
    ]


@pytest.fixture
def sample_roadmap():
    """Create sample roadmap phases."""
    return [
        RoadmapPhase(
            month=1,
            focus="Quick Win",
            actions=["Deploy chatbot", "Train team", "Monitor metrics"],
            decision_gate="Achieve 20% deflection",
        ),
        RoadmapPhase(
            month=2,
            focus="Foundation",
            actions=["Expand knowledge base", "Add integrations"],
            decision_gate="30% deflection, positive feedback",
        ),
        RoadmapPhase(
            month=3,
            focus="Scale",
            actions=["Roll out to all channels", "Optimize"],
            decision_gate="Full deployment complete",
        ),
    ]


class TestCompassReportGenerator:
    """Tests for CompassReportGenerator."""

    @pytest.mark.asyncio
    async def test_returns_compass_report(
        self,
        sample_request,
        sample_score,
        sample_research,
        sample_priorities,
        sample_avoid,
        sample_roadmap,
    ):
        """Should return a CompassReport object."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        result = await generator.generate(
            request=sample_request,
            score=sample_score,
            research_insights=sample_research,
            priorities=sample_priorities,
            avoid=sample_avoid,
            roadmap=sample_roadmap,
            run_id="compass-test-123",
        )

        assert isinstance(result, CompassReport)
        assert result.run_id == "compass-test-123"
        assert result.company_name == "Acme Corp"

    @pytest.mark.asyncio
    async def test_includes_ai_readiness_score(
        self,
        sample_request,
        sample_score,
        sample_research,
        sample_priorities,
        sample_avoid,
        sample_roadmap,
    ):
        """Should include AI readiness score in report."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        result = await generator.generate(
            request=sample_request,
            score=sample_score,
            research_insights=sample_research,
            priorities=sample_priorities,
            avoid=sample_avoid,
            roadmap=sample_roadmap,
            run_id="compass-test-123",
        )

        assert result.ai_readiness_score.overall_score == 62.0
        assert result.ai_readiness_score == sample_score

    @pytest.mark.asyncio
    async def test_includes_priorities(
        self,
        sample_request,
        sample_score,
        sample_research,
        sample_priorities,
        sample_avoid,
        sample_roadmap,
    ):
        """Should include business priorities in report."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        result = await generator.generate(
            request=sample_request,
            score=sample_score,
            research_insights=sample_research,
            priorities=sample_priorities,
            avoid=sample_avoid,
            roadmap=sample_roadmap,
            run_id="compass-test-123",
        )

        assert len(result.priorities) == 2
        assert result.priorities[0].problem_name == "Customer Support"

    @pytest.mark.asyncio
    async def test_includes_roadmap(
        self,
        sample_request,
        sample_score,
        sample_research,
        sample_priorities,
        sample_avoid,
        sample_roadmap,
    ):
        """Should include 90-day roadmap in report."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        result = await generator.generate(
            request=sample_request,
            score=sample_score,
            research_insights=sample_research,
            priorities=sample_priorities,
            avoid=sample_avoid,
            roadmap=sample_roadmap,
            run_id="compass-test-123",
        )

        assert len(result.roadmap) == 3
        assert result.roadmap[0].month == 1
        assert result.roadmap[0].focus == "Quick Win"

    @pytest.mark.asyncio
    async def test_includes_anti_recommendations(
        self,
        sample_request,
        sample_score,
        sample_research,
        sample_priorities,
        sample_avoid,
        sample_roadmap,
    ):
        """Should include anti-recommendations in report."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        result = await generator.generate(
            request=sample_request,
            score=sample_score,
            research_insights=sample_research,
            priorities=sample_priorities,
            avoid=sample_avoid,
            roadmap=sample_roadmap,
            run_id="compass-test-123",
        )

        assert len(result.avoid) == 1
        assert result.avoid[0].name == "Full Autonomous Agent"

    @pytest.mark.asyncio
    async def test_generates_html_content(
        self,
        sample_request,
        sample_score,
        sample_research,
        sample_priorities,
        sample_avoid,
        sample_roadmap,
    ):
        """Should generate HTML content."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        result = await generator.generate(
            request=sample_request,
            score=sample_score,
            research_insights=sample_research,
            priorities=sample_priorities,
            avoid=sample_avoid,
            roadmap=sample_roadmap,
            run_id="compass-test-123",
        )

        assert result.html_content is not None
        assert len(result.html_content) > 0
        assert "<!DOCTYPE html>" in result.html_content or "<html>" in result.html_content

    @pytest.mark.asyncio
    async def test_html_contains_company_name(
        self,
        sample_request,
        sample_score,
        sample_research,
        sample_priorities,
        sample_avoid,
        sample_roadmap,
    ):
        """Should include company name in HTML."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        result = await generator.generate(
            request=sample_request,
            score=sample_score,
            research_insights=sample_research,
            priorities=sample_priorities,
            avoid=sample_avoid,
            roadmap=sample_roadmap,
            run_id="compass-test-123",
        )

        assert "Acme Corp" in result.html_content

    @pytest.mark.asyncio
    async def test_html_contains_score(
        self,
        sample_request,
        sample_score,
        sample_research,
        sample_priorities,
        sample_avoid,
        sample_roadmap,
    ):
        """Should include AI readiness score in HTML."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        result = await generator.generate(
            request=sample_request,
            score=sample_score,
            research_insights=sample_research,
            priorities=sample_priorities,
            avoid=sample_avoid,
            roadmap=sample_roadmap,
            run_id="compass-test-123",
        )

        assert "62" in result.html_content

    @pytest.mark.asyncio
    async def test_calls_ai_for_executive_summary(
        self,
        sample_request,
        sample_score,
        sample_research,
        sample_priorities,
        sample_avoid,
        sample_roadmap,
    ):
        """Should call AI provider to generate executive summary."""
        provider = MockAIProvider("This is the AI-generated executive summary.")
        generator = CompassReportGenerator(provider)

        await generator.generate(
            request=sample_request,
            score=sample_score,
            research_insights=sample_research,
            priorities=sample_priorities,
            avoid=sample_avoid,
            roadmap=sample_roadmap,
            run_id="compass-test-123",
        )

        assert provider.generate.called
        call_kwargs = provider.generate.call_args[1]
        assert "Acme Corp" in call_kwargs["prompt"]
        assert "62" in call_kwargs["prompt"]

    @pytest.mark.asyncio
    async def test_handles_ai_failure_gracefully(
        self,
        sample_request,
        sample_score,
        sample_research,
        sample_priorities,
        sample_avoid,
        sample_roadmap,
    ):
        """Should use fallback summary if AI generation fails."""
        provider = MockAIProvider()
        provider.generate = AsyncMock(side_effect=Exception("AI Error"))
        generator = CompassReportGenerator(provider)

        result = await generator.generate(
            request=sample_request,
            score=sample_score,
            research_insights=sample_research,
            priorities=sample_priorities,
            avoid=sample_avoid,
            roadmap=sample_roadmap,
            run_id="compass-test-123",
        )

        # Should still return a valid report with fallback summary
        assert isinstance(result, CompassReport)
        assert result.html_content is not None
        assert "Acme Corp" in result.html_content

    @pytest.mark.asyncio
    async def test_includes_research_insights(
        self,
        sample_request,
        sample_score,
        sample_research,
        sample_priorities,
        sample_avoid,
        sample_roadmap,
    ):
        """Should include research insights in report."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        result = await generator.generate(
            request=sample_request,
            score=sample_score,
            research_insights=sample_research,
            priorities=sample_priorities,
            avoid=sample_avoid,
            roadmap=sample_roadmap,
            run_id="compass-test-123",
        )

        assert result.research_insights == sample_research


class TestReadinessLevelMapping:
    """Tests for readiness level scoring."""

    def test_beginner_level(self):
        """Score <= 30 should be Beginner."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        assert generator._get_readiness_level(20) == "Beginner"
        assert generator._get_readiness_level(30) == "Beginner"

    def test_developing_level(self):
        """Score 31-50 should be Developing."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        assert generator._get_readiness_level(31) == "Developing"
        assert generator._get_readiness_level(50) == "Developing"

    def test_established_level(self):
        """Score 51-70 should be Established."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        assert generator._get_readiness_level(51) == "Established"
        assert generator._get_readiness_level(70) == "Established"

    def test_advanced_level(self):
        """Score 71-85 should be Advanced."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        assert generator._get_readiness_level(71) == "Advanced"
        assert generator._get_readiness_level(85) == "Advanced"

    def test_leading_level(self):
        """Score > 85 should be Leading."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        assert generator._get_readiness_level(86) == "Leading"
        assert generator._get_readiness_level(100) == "Leading"


class TestScoreColorMapping:
    """Tests for score color mapping."""

    def test_red_for_low_scores(self):
        """Score <= 30 should be red."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        assert generator._get_score_color(20) == "#ff4444"
        assert generator._get_score_color(30) == "#ff4444"

    def test_orange_for_developing_scores(self):
        """Score 31-50 should be orange."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        assert generator._get_score_color(31) == "#ffaa00"
        assert generator._get_score_color(50) == "#ffaa00"

    def test_blue_for_established_scores(self):
        """Score 51-70 should be blue."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        assert generator._get_score_color(51) == "#00d4ff"
        assert generator._get_score_color(70) == "#00d4ff"

    def test_green_for_advanced_scores(self):
        """Score 71-85 should be green."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        assert generator._get_score_color(71) == "#00ff88"
        assert generator._get_score_color(85) == "#00ff88"

    def test_purple_for_leading_scores(self):
        """Score > 85 should be purple."""
        provider = MockAIProvider()
        generator = CompassReportGenerator(provider)

        assert generator._get_score_color(86) == "#7c3aed"
        assert generator._get_score_color(100) == "#7c3aed"
