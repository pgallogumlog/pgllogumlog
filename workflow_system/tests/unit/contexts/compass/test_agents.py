"""
Unit tests for Compass Research Agents.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from contexts.compass.models import SelfAssessment, CompassRequest
from contexts.compass.agents.company_agent import CompanyResearchAgent, CompanyResearchResult
from contexts.compass.agents.industry_agent import IndustryResearchAgent, IndustryResearchResult
from contexts.compass.agents.whitepaper_agent import WhitePaperResearchAgent, WhitePaperResearchResult, RealCaseStudy
from contexts.compass.agents.orchestrator import ResearchOrchestrator, ResearchInsights


class MockAIProvider:
    """Mock AI provider for testing."""

    def __init__(self, response: dict = None):
        self.response = response or {}
        self.generate_json = AsyncMock(return_value=self.response)


@pytest.fixture
def sample_request():
    """Create sample CompassRequest for testing."""
    return CompassRequest(
        company_name="Acme Corp",
        website="https://acme.com",
        industry="Technology",
        company_size="50-200",
        self_assessment=SelfAssessment(3, 4, 3),
        pain_point="Customer support overload",
        description="We're drowning in support tickets and need AI help",
        email="ceo@acme.com",
        contact_name="John Smith",
    )


class TestCompanyResearchAgent:
    """Tests for CompanyResearchAgent."""

    @pytest.mark.asyncio
    async def test_returns_research_result(self):
        """Agent should return CompanyResearchResult."""
        mock_response = {
            "technology_assessment": {
                "detected_stack": ["Modern website", "API integrations"],
                "stack_maturity": "modern",
                "integration_level": "medium",
            },
            "digital_maturity": {"score": 6},
            "data_infrastructure": {"score": 7},
            "overall_readiness_score": 65.0,
        }
        provider = MockAIProvider(mock_response)
        agent = CompanyResearchAgent(provider)

        result = await agent.research(
            company_name="Test Corp",
            website="https://test.com",
            industry="Technology",
            description="Need help with support",
        )

        assert isinstance(result, CompanyResearchResult)
        assert result.overall_readiness_score == 65.0
        assert "Modern website" in result.detected_technologies
        assert result.integration_level == "medium"

    @pytest.mark.asyncio
    async def test_handles_missing_website(self):
        """Agent should work without website."""
        provider = MockAIProvider({"overall_readiness_score": 50.0})
        agent = CompanyResearchAgent(provider)

        result = await agent.research(
            company_name="No Web Corp",
            website="",
            industry="Retail",
            description="Manual processes",
        )

        assert isinstance(result, CompanyResearchResult)
        assert provider.generate_json.called

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        """Agent should return default result on error."""
        provider = MockAIProvider()
        provider.generate_json = AsyncMock(side_effect=Exception("API Error"))
        agent = CompanyResearchAgent(provider)

        result = await agent.research(
            company_name="Error Corp",
            website="https://error.com",
            industry="Tech",
            description="Test",
        )

        # Should return default values, not raise
        assert isinstance(result, CompanyResearchResult)
        assert result.overall_readiness_score == 50.0


class TestIndustryResearchAgent:
    """Tests for IndustryResearchAgent."""

    @pytest.mark.asyncio
    async def test_returns_industry_result(self):
        """Agent should return IndustryResearchResult."""
        mock_response = {
            "industry_ai_landscape": {
                "maturity_level": "growing",
            },
            "use_case_analysis": {
                "emerging_use_cases": ["Chatbots", "Analytics"],
            },
            "competitor_intelligence": {
                "adoption_level": "medium",
            },
            "regulatory_landscape": {
                "key_regulations": [],
            },
            "industry_readiness_score": 60.0,
        }
        provider = MockAIProvider(mock_response)
        agent = IndustryResearchAgent(provider)

        result = await agent.research(
            industry="Healthcare",
            company_size="200-500",
            pain_point="Patient scheduling",
        )

        assert isinstance(result, IndustryResearchResult)
        assert result.maturity_level == "growing"
        assert result.industry_readiness_score == 60.0
        assert "Chatbots" in result.emerging_use_cases

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        """Agent should return default result on error."""
        provider = MockAIProvider()
        provider.generate_json = AsyncMock(side_effect=Exception("API Error"))
        agent = IndustryResearchAgent(provider)

        result = await agent.research(
            industry="Unknown",
            company_size="10-50",
            pain_point="Test",
        )

        assert isinstance(result, IndustryResearchResult)
        assert result.industry_readiness_score == 50.0


class TestWhitePaperResearchAgent:
    """Tests for WhitePaperResearchAgent."""

    @pytest.mark.asyncio
    async def test_returns_whitepaper_result(self):
        """Agent should return WhitePaperResearchResult."""
        mock_response = {
            "case_studies": [
                {
                    "title": "Retail AI Success",
                    "company": "Mid-size retailer",
                    "industry": "Retail",
                    "challenge": "Manual inventory",
                    "solution": "AI forecasting",
                    "vendor_tools": ["Tool1"],
                    "results": {
                        "primary_metric": "30% reduction in stockouts",
                        "secondary_metrics": [],
                        "timeline": "6 months"
                    },
                    "source_title": "Case Study Report",
                    "source_url": "https://example.com",
                    "credibility": "high",
                }
            ],
            "methodology_recommendations": [
                {"name": "Agile AI", "description": "MVP approach", "best_for": "Quick wins", "source": "Report", "source_url": "https://example.com"}
            ],
            "confidence_score": 75.0,
        }
        provider = MockAIProvider(mock_response)
        agent = WhitePaperResearchAgent(provider)

        result = await agent.research(
            industry="Retail",
            company_size="100-200",
            pain_point="Inventory management",
            description="We need better forecasting",
        )

        assert isinstance(result, WhitePaperResearchResult)
        assert result.confidence_score == 75.0
        assert len(result.case_studies) == 1
        assert result.case_studies[0].company == "Mid-size retailer"

    @pytest.mark.asyncio
    async def test_parses_case_studies_correctly(self):
        """Should parse case studies into RealCaseStudy objects."""
        mock_response = {
            "case_studies": [
                {
                    "title": "CS1",
                    "company": "Type1",
                    "industry": "Tech",
                    "challenge": "C1",
                    "solution": "S1",
                    "vendor_tools": [],
                    "results": {"primary_metric": "R1", "secondary_metrics": [], "timeline": ""},
                    "source_title": "Source1",
                    "source_url": "https://example.com/1",
                    "credibility": "medium",
                },
                {
                    "title": "CS2",
                    "company": "Type2",
                    "industry": "Tech",
                    "challenge": "C2",
                    "solution": "S2",
                    "vendor_tools": [],
                    "results": {"primary_metric": "R2", "secondary_metrics": [], "timeline": ""},
                    "source_title": "Source2",
                    "source_url": "https://example.com/2",
                    "credibility": "medium",
                },
            ],
            "confidence_score": 80.0,
        }
        provider = MockAIProvider(mock_response)
        agent = WhitePaperResearchAgent(provider)

        result = await agent.research("Tech", "50-100", "Pain", "Desc")

        assert len(result.case_studies) == 2
        assert all(isinstance(cs, RealCaseStudy) for cs in result.case_studies)


class TestResearchOrchestrator:
    """Tests for ResearchOrchestrator."""

    @pytest.mark.asyncio
    async def test_runs_three_agents_in_parallel(self, sample_request):
        """Orchestrator should call all three agents."""
        mock_response = {
            "overall_readiness_score": 70.0,
            "industry_readiness_score": 65.0,
            "confidence_score": 75.0,
        }
        provider = MockAIProvider(mock_response)
        orchestrator = ResearchOrchestrator(provider)

        insights, score = await orchestrator.run_research(sample_request)

        # Should have called generate_json 3 times (once per agent)
        assert provider.generate_json.call_count == 3
        assert isinstance(insights, ResearchInsights)

    @pytest.mark.asyncio
    async def test_calculates_weighted_score(self, sample_request):
        """Should calculate weighted research score correctly."""
        # Set up provider to return different scores
        call_count = 0
        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # Company agent
                return {"overall_readiness_score": 80.0}
            elif call_count == 2:  # Industry agent
                return {"industry_readiness_score": 60.0}
            else:  # Whitepaper agent
                return {"confidence_score": 70.0}

        provider = MockAIProvider()
        provider.generate_json = mock_generate
        orchestrator = ResearchOrchestrator(provider)

        insights, score = await orchestrator.run_research(sample_request)

        # Expected: (80 * 0.40) + (60 * 0.35) + (70 * 0.25) = 32 + 21 + 17.5 = 70.5
        assert score == 70.5

    @pytest.mark.asyncio
    async def test_returns_insights_and_score(self, sample_request):
        """Should return tuple of (ResearchInsights, float)."""
        provider = MockAIProvider({"overall_readiness_score": 50.0})
        orchestrator = ResearchOrchestrator(provider)

        result = await orchestrator.run_research(sample_request)

        assert isinstance(result, tuple)
        assert len(result) == 2
        insights, score = result
        assert isinstance(insights, ResearchInsights)
        assert isinstance(score, float)

    def test_weights_sum_to_one(self):
        """Weights should sum to 1.0."""
        provider = MockAIProvider()
        orchestrator = ResearchOrchestrator(provider)

        total = sum(orchestrator.WEIGHTS.values())
        assert total == 1.0

    @pytest.mark.asyncio
    async def test_to_insights_dict(self, sample_request):
        """Should convert insights to dictionary."""
        provider = MockAIProvider({
            "overall_readiness_score": 60.0,
            "industry_readiness_score": 55.0,
            "confidence_score": 70.0,
            "technology_assessment": {"detected_stack": ["Modern"]},
            "use_case_analysis": {"emerging_use_cases": ["Chatbot"]},
            "case_studies": [],
        })
        orchestrator = ResearchOrchestrator(provider)

        insights, _ = await orchestrator.run_research(sample_request)
        insights_dict = insights.to_dict()

        assert "company" in insights_dict
        assert "industry" in insights_dict
        assert "whitepaper" in insights_dict
        assert "aggregated_score" in insights_dict
