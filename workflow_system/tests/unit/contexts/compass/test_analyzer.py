"""
Unit tests for Priority Analyzer.
"""

import pytest
from unittest.mock import AsyncMock

from contexts.compass.models import (
    SelfAssessment,
    CompassRequest,
    AIReadinessScore,
    BusinessPriority,
    AntiRecommendation,
    RoadmapPhase,
)
from contexts.compass.analyzer import PriorityAnalyzer


class MockAIProvider:
    """Mock AI provider for testing."""

    def __init__(self, response: dict = None):
        self.response = response or {}
        self.generate_json = AsyncMock(return_value=self.response)


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
    """Create sample research insights matching ResearchInsights.to_dict() structure."""
    return {
        "company": {
            "detected_technologies": ["Modern website", "API integrations"],
            "stack_maturity": "modern",
            "integration_level": "medium",
            "tech_findings": [],
            "digital_maturity_score": 7,
            "digital_strengths": ["Good foundation"],
            "digital_gaps": [],
            "positive_ai_signals": [{"finding": "Support automation potential", "source_url": ""}],
            "negative_ai_signals": [],
            "hiring_indicators": [],
            "automation_tools": [],
            "data_infrastructure_score": 6,
            "detected_platforms": [],
            "digital_vs_industry": "average",
            "key_differentiators": [],
            "vulnerability_areas": [],
            "readiness_score": 65.0,
            "executive_summary": "Good foundation",
            "all_citations": [],
        },
        "industry": {
            "maturity_level": "growing",
            "adoption_rate": "45%",
            "trend_direction": "accelerating",
            "key_statistics": [],
            "leading_competitors": [],
            "adoption_level": "medium",
            "competitive_urgency": "medium",
            "proven_use_cases": [],
            "emerging_use_cases": ["Chatbots", "Analytics"],
            "use_case_relevance": "",
            "typical_roi": "25-40%",
            "time_to_value": "3-6 months",
            "cost_range": "$10K-$50K",
            "success_rate": "70%",
            "key_regulations": [],
            "compliance_requirements": [],
            "risk_factors": [],
            "growth_projection": "15% CAGR",
            "key_drivers": [],
            "emerging_technologies": [],
            "readiness_score": 60.0,
            "executive_summary": "Growing industry adoption",
            "all_citations": [],
        },
        "whitepaper": {
            "case_studies": [],
            "implementation": {
                "average_timeline": "3-6 months",
                "success_factors": ["Executive buy-in", "Clear metrics"],
                "failure_reasons": ["Over-scoping", "No training data"],
                "budget_small": "$5K-$15K",
                "budget_medium": "$15K-$50K",
                "budget_enterprise": "$50K-$200K",
            },
            "methodologies": [],
            "vendors": {
                "leaders": [],
                "challengers": [],
                "pricing_models": [],
            },
            "top_risks": [],
            "regulatory_considerations": [],
            "change_management": [],
            "confidence": 75.0,
            "executive_summary": "Implementation best practices",
            "all_citations": [],
        },
        "aggregated_score": 62.0,
        "all_sources": [],
    }


class TestPriorityAnalyzer:
    """Tests for PriorityAnalyzer."""

    @pytest.mark.asyncio
    async def test_returns_tuple_of_three_lists(
        self, sample_request, sample_score, sample_research
    ):
        """Should return (priorities, avoid, roadmap)."""
        mock_response = {
            "priorities": [
                {
                    "rank": 1,
                    "problem_name": "Support Overload",
                    "problem_description": "Too many tickets",
                    "solution": {
                        "name": "Support Bot",
                        "approach_type": "RAG",
                        "description": "AI chatbot",
                        "why_this_fits": "Good fit",
                        "tools": ["Claude"],
                        "expected_impact": "40% reduction",
                        "complexity": "Medium",
                    },
                }
            ],
            "avoid": [
                {
                    "name": "Full Automation",
                    "why_tempting": "Promises everything",
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
        provider = MockAIProvider(mock_response)
        analyzer = PriorityAnalyzer(provider)

        result = await analyzer.analyze(sample_request, sample_research, sample_score)

        assert isinstance(result, tuple)
        assert len(result) == 3
        priorities, avoid, roadmap = result
        assert isinstance(priorities, list)
        assert isinstance(avoid, list)
        assert isinstance(roadmap, list)

    @pytest.mark.asyncio
    async def test_parses_priorities_correctly(
        self, sample_request, sample_score, sample_research
    ):
        """Should parse priorities into BusinessPriority objects."""
        mock_response = {
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
                        "tools": ["Claude", "Pinecone"],
                        "expected_impact": "40% ticket reduction",
                        "complexity": "Medium",
                    },
                },
                {
                    "rank": 2,
                    "problem_name": "Data Entry",
                    "problem_description": "Manual processes",
                    "solution": {
                        "name": "Document Processor",
                        "approach_type": "Agentic",
                        "description": "Auto-process documents",
                        "why_this_fits": "Simple implementation",
                        "tools": ["Claude", "n8n"],
                        "expected_impact": "60% time savings",
                        "complexity": "Low",
                    },
                },
            ],
            "avoid": [],
            "roadmap": [],
        }
        provider = MockAIProvider(mock_response)
        analyzer = PriorityAnalyzer(provider)

        priorities, _, _ = await analyzer.analyze(
            sample_request, sample_research, sample_score
        )

        assert len(priorities) == 2
        assert all(isinstance(p, BusinessPriority) for p in priorities)
        assert priorities[0].rank == 1
        assert priorities[0].problem_name == "Customer Support"
        assert priorities[0].solution.name == "RAG Support Bot"
        assert priorities[0].solution.approach_type == "RAG"
        assert "Claude" in priorities[0].solution.tools

    @pytest.mark.asyncio
    async def test_parses_anti_recommendations(
        self, sample_request, sample_score, sample_research
    ):
        """Should parse anti-recommendations correctly."""
        mock_response = {
            "priorities": [],
            "avoid": [
                {
                    "name": "Full Autonomous Agent",
                    "why_tempting": "Complete automation promise",
                    "why_wrong_for_them": "Requires data maturity you lack",
                },
                {
                    "name": "Custom LLM Training",
                    "why_tempting": "Perfect fit for your domain",
                    "why_wrong_for_them": "Expensive and time-consuming",
                },
            ],
            "roadmap": [],
        }
        provider = MockAIProvider(mock_response)
        analyzer = PriorityAnalyzer(provider)

        _, avoid, _ = await analyzer.analyze(
            sample_request, sample_research, sample_score
        )

        assert len(avoid) == 2
        assert all(isinstance(a, AntiRecommendation) for a in avoid)
        assert avoid[0].name == "Full Autonomous Agent"
        assert "automation" in avoid[0].why_tempting.lower()

    @pytest.mark.asyncio
    async def test_parses_roadmap(
        self, sample_request, sample_score, sample_research
    ):
        """Should parse roadmap phases correctly."""
        mock_response = {
            "priorities": [],
            "avoid": [],
            "roadmap": [
                {
                    "month": 1,
                    "focus": "Quick Win",
                    "actions": ["Deploy chatbot", "Train team", "Monitor metrics"],
                    "decision_gate": "Achieve 20% deflection",
                },
                {
                    "month": 2,
                    "focus": "Foundation",
                    "actions": ["Expand knowledge base", "Add integrations"],
                    "decision_gate": "30% deflection, positive feedback",
                },
                {
                    "month": 3,
                    "focus": "Scale",
                    "actions": ["Roll out to all channels", "Optimize"],
                    "decision_gate": "Full deployment complete",
                },
            ],
        }
        provider = MockAIProvider(mock_response)
        analyzer = PriorityAnalyzer(provider)

        _, _, roadmap = await analyzer.analyze(
            sample_request, sample_research, sample_score
        )

        assert len(roadmap) == 3
        assert all(isinstance(r, RoadmapPhase) for r in roadmap)
        assert roadmap[0].month == 1
        assert roadmap[0].focus == "Quick Win"
        assert len(roadmap[0].actions) == 3
        assert "deflection" in roadmap[0].decision_gate.lower()

    @pytest.mark.asyncio
    async def test_limits_to_three_priorities(
        self, sample_request, sample_score, sample_research
    ):
        """Should limit priorities to 3 even if more returned."""
        mock_response = {
            "priorities": [
                {"rank": i, "problem_name": f"Problem {i}", "solution": {"name": f"Solution {i}"}}
                for i in range(1, 6)  # 5 priorities
            ],
            "avoid": [],
            "roadmap": [],
        }
        provider = MockAIProvider(mock_response)
        analyzer = PriorityAnalyzer(provider)

        priorities, _, _ = await analyzer.analyze(
            sample_request, sample_research, sample_score
        )

        assert len(priorities) == 3

    @pytest.mark.asyncio
    async def test_handles_api_error_with_defaults(
        self, sample_request, sample_score, sample_research
    ):
        """Should return sensible defaults on API error."""
        provider = MockAIProvider()
        provider.generate_json = AsyncMock(side_effect=Exception("API Error"))
        analyzer = PriorityAnalyzer(provider)

        priorities, avoid, roadmap = await analyzer.analyze(
            sample_request, sample_research, sample_score
        )

        # Should return defaults, not raise
        assert len(priorities) >= 1
        assert len(avoid) >= 1
        assert len(roadmap) >= 1
        # Default should reference their pain point
        assert sample_request.pain_point in priorities[0].problem_name

    @pytest.mark.asyncio
    async def test_includes_readiness_score_in_prompt(
        self, sample_request, sample_score, sample_research
    ):
        """Should include readiness score in the AI prompt."""
        provider = MockAIProvider({"priorities": [], "avoid": [], "roadmap": []})
        analyzer = PriorityAnalyzer(provider)

        await analyzer.analyze(sample_request, sample_research, sample_score)

        # Check the prompt includes the score
        call_args = provider.generate_json.call_args
        prompt = call_args[1]["prompt"]
        assert "62" in prompt  # overall_score
        assert "Established" in prompt  # readiness level for 62

    @pytest.mark.asyncio
    async def test_formats_research_in_prompt(
        self, sample_request, sample_score, sample_research
    ):
        """Should include research insights in prompt."""
        provider = MockAIProvider({"priorities": [], "avoid": [], "roadmap": []})
        analyzer = PriorityAnalyzer(provider)

        await analyzer.analyze(sample_request, sample_research, sample_score)

        call_args = provider.generate_json.call_args
        prompt = call_args[1]["prompt"]
        assert "Modern website" in prompt  # from company research
        assert "growing" in prompt  # from industry research
