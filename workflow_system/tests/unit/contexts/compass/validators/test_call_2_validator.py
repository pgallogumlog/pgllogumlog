"""
Unit tests for Call2Validator - Synthesis specificity validation.

TDD: These tests define expected behavior. Implementation follows.
NO MOCKING of core validation logic - tests use real data.
"""

import pytest

from contexts.compass.models import CompassRequest, SelfAssessment
from contexts.compass.validators.call_2_validator import Call2Validator
from contexts.compass.validators.models import CallQAResult


class TestCall2Validator:
    """Tests for Call 2 (Strategic Synthesis) validation."""

    @pytest.fixture
    def validator(self) -> Call2Validator:
        """Create validator instance."""
        return Call2Validator()

    @pytest.fixture
    def sample_request(self) -> CompassRequest:
        """Create a sample compass request for testing."""
        return CompassRequest(
            company_name="Acme Legal Services",
            website="https://acmelegal.com",
            industry="Law Firm",
            company_size="50-200",
            self_assessment=SelfAssessment(
                data_maturity=3,
                automation_experience=2,
                change_readiness=4,
            ),
            pain_point="Manual contract review taking too long",
            description="We spend 40 hours per week on contract review",
            email="test@acmelegal.com",
            contact_name="John Doe",
        )

    # ===========================================
    # PASS CASES - Synthesis is specific
    # ===========================================

    def test_should_pass_when_synthesis_is_specific_and_cited(
        self, validator: Call2Validator, sample_request: CompassRequest
    ):
        """Valid synthesis with company reference and citations passes."""
        synthesis = {
            "executive_summary": {
                "headline": "AI Readiness Assessment for Acme Legal Services",
                "key_finding": "Contract review automation is your highest-impact opportunity",
            },
            "priorities": [
                {
                    "rank": 1,
                    "problem_name": "Contract Review Bottleneck",
                    "problem_description": "Acme Legal spends 40 hours weekly on manual contract review",
                    "research_support": "Industry data shows 60% time reduction with AI",
                    "solution": {
                        "name": "AI-Powered Contract Analyzer",
                        "approach_type": "RAG",
                        "description": "Implement clause extraction and risk flagging",
                        "recommended_tools": [
                            {"name": "Claude API", "purpose": "Document analysis"},
                            {"name": "Pinecone", "purpose": "Vector storage"},
                        ],
                    },
                },
                {
                    "rank": 2,
                    "problem_name": "Due Diligence Speed",
                    "problem_description": "M&A due diligence takes too long",
                    "research_support": "Competitors using AI complete 50% faster",
                    "solution": {
                        "name": "Document Classification Pipeline",
                        "approach_type": "ML",
                        "recommended_tools": [{"name": "Custom classifier"}],
                    },
                },
                {
                    "rank": 3,
                    "problem_name": "Knowledge Management",
                    "problem_description": "Institutional knowledge is siloed",
                    "research_support": "Survey shows 70% of firms struggle with knowledge sharing",
                    "solution": {
                        "name": "Legal Knowledge Base",
                        "approach_type": "RAG",
                        "recommended_tools": [{"name": "Notion AI"}],
                    },
                },
            ],
            "avoid": [
                {
                    "name": "Full Autonomous Agent",
                    "why_tempting": "Promises full automation",
                    "why_wrong_for_them": "Too complex for current readiness level",
                },
            ],
            "roadmap": [
                {"month": 1, "focus": "Quick Win", "actions": ["Deploy contract analyzer"]},
                {"month": 2, "focus": "Foundation", "actions": ["Build training data"]},
                {"month": 3, "focus": "Scale", "actions": ["Expand to all practice areas"]},
            ],
        }

        result = validator.validate(
            request=sample_request,
            synthesis_output=synthesis,
            call_id="call-201",
        )

        assert isinstance(result, CallQAResult)
        assert result.passed is True
        assert result.score >= 7
        assert result.is_relevant is True
        assert result.is_specific is True
        assert result.is_complete is True

    # ===========================================
    # FAIL CASES - Synthesis is NOT specific
    # ===========================================

    def test_should_fail_when_synthesis_missing_company_name(
        self, validator: Call2Validator, sample_request: CompassRequest
    ):
        """Synthesis that doesn't mention the company fails."""
        synthesis = {
            "executive_summary": {
                "headline": "Generic AI Assessment",
            },
            "priorities": [
                {
                    "rank": 1,
                    "problem_name": "Process Improvement",
                    "problem_description": "Businesses can benefit from automation",
                    "solution": {"name": "Generic AI Tool"},
                },
            ],
            "roadmap": [{"month": 1, "focus": "Start"}],
        }

        result = validator.validate(
            request=sample_request,
            synthesis_output=synthesis,
            call_id="call-202",
        )

        assert result.passed is False
        assert result.is_relevant is False
        assert any("company" in issue.lower() for issue in result.issues)

    def test_should_fail_when_priorities_lack_citations(
        self, validator: Call2Validator, sample_request: CompassRequest
    ):
        """Priorities without research support citations fail."""
        synthesis = {
            "executive_summary": {
                "headline": "AI Assessment for Acme Legal Services",
            },
            "priorities": [
                {
                    "rank": 1,
                    "problem_name": "Contract Review",
                    "problem_description": "Acme Legal needs contract automation",
                    # Missing research_support
                    "solution": {"name": "Contract AI"},
                },
                {
                    "rank": 2,
                    "problem_name": "Knowledge Management",
                    "problem_description": "Need better knowledge sharing",
                    # Missing research_support
                    "solution": {"name": "Knowledge Base"},
                },
                {
                    "rank": 3,
                    "problem_name": "Client Communication",
                    "problem_description": "Improve client updates",
                    # Missing research_support
                    "solution": {"name": "Client Portal"},
                },
            ],
            "roadmap": [{"month": 1, "focus": "Start"}],
        }

        result = validator.validate(
            request=sample_request,
            synthesis_output=synthesis,
            call_id="call-203",
        )

        assert result.is_specific is False
        assert any("citation" in issue.lower() or "research" in issue.lower() for issue in result.issues)

    def test_should_fail_when_too_few_priorities(
        self, validator: Call2Validator, sample_request: CompassRequest
    ):
        """Synthesis with fewer than 3 priorities fails."""
        synthesis = {
            "executive_summary": {
                "headline": "AI Assessment for Acme Legal Services",
            },
            "priorities": [
                {
                    "rank": 1,
                    "problem_name": "Only One Priority",
                    "problem_description": "Acme Legal needs this",
                    "research_support": "Data shows this is important",
                    "solution": {"name": "Single Solution"},
                },
            ],
            "roadmap": [{"month": 1, "focus": "Start"}],
        }

        result = validator.validate(
            request=sample_request,
            synthesis_output=synthesis,
            call_id="call-204",
        )

        assert result.is_complete is False
        assert any("priorit" in issue.lower() for issue in result.issues)

    def test_should_flag_generic_tool_recommendations(
        self, validator: Call2Validator, sample_request: CompassRequest
    ):
        """Generic tool names like 'ChatGPT' should be flagged."""
        synthesis = {
            "executive_summary": {
                "headline": "AI Assessment for Acme Legal Services",
            },
            "priorities": [
                {
                    "rank": 1,
                    "problem_name": "Contract Review",
                    "problem_description": "Acme Legal needs automation",
                    "research_support": "Industry data supports this",
                    "solution": {
                        "name": "Use ChatGPT",
                        "recommended_tools": [
                            {"name": "ChatGPT"},  # Too generic
                            {"name": "Generic AI Tool"},  # Too generic
                        ],
                    },
                },
                {
                    "rank": 2,
                    "problem_name": "Knowledge Management",
                    "research_support": "Research supports",
                    "solution": {"name": "AI Assistant", "recommended_tools": []},
                },
                {
                    "rank": 3,
                    "problem_name": "Communication",
                    "research_support": "Research supports",
                    "solution": {"name": "Copilot", "recommended_tools": [{"name": "Copilot"}]},
                },
            ],
            "roadmap": [{"month": 1, "focus": "Start"}],
        }

        result = validator.validate(
            request=sample_request,
            synthesis_output=synthesis,
            call_id="call-205",
        )

        assert any("generic" in issue.lower() for issue in result.issues)

    def test_should_fail_when_missing_roadmap(
        self, validator: Call2Validator, sample_request: CompassRequest
    ):
        """Synthesis without roadmap fails completeness check."""
        synthesis = {
            "executive_summary": {
                "headline": "AI Assessment for Acme Legal Services",
            },
            "priorities": [
                {
                    "rank": 1,
                    "problem_name": "Contract Review",
                    "problem_description": "Acme Legal needs automation",
                    "research_support": "Data supports this",
                    "solution": {"name": "Contract AI"},
                },
                {"rank": 2, "problem_name": "P2", "research_support": "R", "solution": {"name": "S"}},
                {"rank": 3, "problem_name": "P3", "research_support": "R", "solution": {"name": "S"}},
            ],
            # Missing roadmap
        }

        result = validator.validate(
            request=sample_request,
            synthesis_output=synthesis,
            call_id="call-206",
        )

        assert result.is_complete is False
        assert any("roadmap" in issue.lower() for issue in result.issues)

    # ===========================================
    # EDGE CASES
    # ===========================================

    def test_should_handle_empty_synthesis(
        self, validator: Call2Validator, sample_request: CompassRequest
    ):
        """Empty synthesis fails gracefully."""
        synthesis = {}

        result = validator.validate(
            request=sample_request,
            synthesis_output=synthesis,
            call_id="call-207",
        )

        assert result.passed is False
        assert result.score <= 3

    # ===========================================
    # OUTPUT FORMAT
    # ===========================================

    def test_should_populate_all_result_fields(
        self, validator: Call2Validator, sample_request: CompassRequest
    ):
        """Result should have all fields populated for sheets logging."""
        synthesis = {
            "executive_summary": {"headline": "Test for Acme Legal Services"},
            "priorities": [
                {"rank": 1, "problem_name": "P1", "research_support": "R", "solution": {"name": "S"}},
                {"rank": 2, "problem_name": "P2", "research_support": "R", "solution": {"name": "S"}},
                {"rank": 3, "problem_name": "P3", "research_support": "R", "solution": {"name": "S"}},
            ],
            "roadmap": [{"month": 1, "focus": "Start"}],
        }

        result = validator.validate(
            request=sample_request,
            synthesis_output=synthesis,
            call_id="call-208",
        )

        assert result.call_id == "call-208"
        assert result.call_number == 2
        assert result.call_type == "Synthesis"
        assert result.company_name == "Acme Legal Services"
        assert isinstance(result.score, int)
        assert isinstance(result.issues, list)
        assert isinstance(result.recommendations, list)

    def test_to_sheets_row_returns_correct_columns(
        self, validator: Call2Validator, sample_request: CompassRequest
    ):
        """to_sheets_row() returns correct number of columns."""
        synthesis = {
            "executive_summary": {"headline": "Test"},
            "priorities": [],
            "roadmap": [],
        }

        result = validator.validate(
            request=sample_request,
            synthesis_output=synthesis,
            call_id="call-209",
        )
        result.run_id = "test-run-456"

        row = result.to_sheets_row()

        assert len(row) == 19  # 19 columns per schema
        assert row[1] == "test-run-456"  # Run ID
        assert row[2] == 2  # Call Number
        assert row[3] == "Synthesis"  # Call Type
