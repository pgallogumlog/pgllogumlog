"""
Unit tests for Call1Validator - Research relevance validation.

TDD: These tests define expected behavior. Implementation follows.
NO MOCKING of core validation logic - tests use real data.
"""

import pytest

from contexts.compass.models import CompassRequest, SelfAssessment
from contexts.compass.validators.call_1_validator import Call1Validator
from contexts.compass.validators.models import CallQAResult


class TestCall1Validator:
    """Tests for Call 1 (Deep Research) validation."""

    @pytest.fixture
    def validator(self) -> Call1Validator:
        """Create validator instance."""
        return Call1Validator()

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
    # PASS CASES - Research is relevant
    # ===========================================

    def test_should_pass_when_research_mentions_company_industry_painpoint(
        self, validator: Call1Validator, sample_request: CompassRequest
    ):
        """Valid research that mentions company, industry, and pain point passes."""
        research = {
            "company_analysis": {
                "company_name": "Acme Legal Services",
                "findings": [
                    "Acme Legal Services is a mid-size law firm",
                    "They specialize in corporate M&A transactions",
                    "Current contract review process is manual",
                ],
            },
            "industry_intelligence": {
                "industry": "Law Firm",
                "trends": [
                    "Law firms are adopting AI for contract analysis",
                    "Average contract review time reduced by 60% with AI",
                ],
            },
            "implementation_patterns": {
                "use_cases": [
                    "Automated contract review for due diligence",
                    "AI-powered clause extraction",
                ],
            },
            "research_metadata": {
                "total_findings": 15,
                "high_confidence_findings": 10,
                "sources_consulted": 8,
                "research_gaps": [],
            },
        }

        result = validator.validate(
            request=sample_request,
            research_findings=research,
            call_id="call-001",
        )

        assert isinstance(result, CallQAResult)
        assert result.passed is True
        assert result.score >= 7
        assert result.is_relevant is True
        assert result.is_specific is True
        assert result.is_complete is True
        assert len(result.issues) == 0

    def test_should_pass_with_partial_match_if_above_threshold(
        self, validator: Call1Validator, sample_request: CompassRequest
    ):
        """Research with some but not all matches can still pass."""
        research = {
            "company_analysis": {
                "findings": [
                    "Acme Legal Services handles complex transactions",
                    "The firm processes contracts regularly",
                ],
            },
            "industry_intelligence": {
                "industry": "Law Firm",
                "trends": ["Law firm AI adoption growing for contract review"],
            },
            "implementation_patterns": {},
            "research_metadata": {
                "total_findings": 8,
                "sources_consulted": 5,
            },
        }

        result = validator.validate(
            request=sample_request,
            research_findings=research,
            call_id="call-002",
        )

        # Should pass with score >= 7 even if not perfect
        assert result.passed is True
        assert result.score >= 7

    # ===========================================
    # FAIL CASES - Research is NOT relevant
    # ===========================================

    def test_should_fail_when_research_missing_company_name(
        self, validator: Call1Validator, sample_request: CompassRequest
    ):
        """Research that doesn't mention the company fails."""
        research = {
            "company_analysis": {
                "findings": [
                    "Generic law firm analysis",
                    "Typical legal operations",
                ],
            },
            "industry_intelligence": {
                "trends": ["Law firms are adopting AI"],
            },
            "research_metadata": {
                "total_findings": 5,
                "sources_consulted": 3,
            },
        }

        result = validator.validate(
            request=sample_request,
            research_findings=research,
            call_id="call-003",
        )

        assert result.passed is False
        assert result.is_relevant is False
        assert any("company" in issue.lower() for issue in result.issues)

    def test_should_fail_when_research_wrong_industry(
        self, validator: Call1Validator, sample_request: CompassRequest
    ):
        """Research about wrong industry fails."""
        research = {
            "company_analysis": {
                "findings": [
                    "E-commerce platform analysis",
                    "Online retail operations",
                ],
            },
            "industry_intelligence": {
                "industry": "E-commerce",
                "trends": ["Retail AI chatbots growing"],
            },
            "research_metadata": {
                "total_findings": 5,
                "sources_consulted": 3,
            },
        }

        result = validator.validate(
            request=sample_request,
            research_findings=research,
            call_id="call-004",
        )

        assert result.passed is False
        assert any("industry" in issue.lower() for issue in result.issues)

    def test_should_fail_when_research_doesnt_address_pain_point(
        self, validator: Call1Validator, sample_request: CompassRequest
    ):
        """Research that ignores client's pain point fails."""
        research = {
            "company_analysis": {
                "company_name": "Acme Legal Services",
                "findings": ["Acme Legal has 100 employees"],
            },
            "industry_intelligence": {
                "industry": "Law Firm",
                "trends": ["Marketing automation for law firms"],  # Wrong topic
            },
            "implementation_patterns": {
                "use_cases": ["Social media management"],  # Irrelevant
            },
            "research_metadata": {
                "total_findings": 3,  # Also insufficient depth
                "sources_consulted": 2,  # Also insufficient sources
            },
        }

        result = validator.validate(
            request=sample_request,
            research_findings=research,
            call_id="call-005",
        )

        # Should fail due to pain point + insufficient depth
        assert result.passed is False
        assert any("pain point" in issue.lower() for issue in result.issues)

    def test_should_fail_when_research_is_generic_boilerplate(
        self, validator: Call1Validator, sample_request: CompassRequest
    ):
        """Generic boilerplate responses fail."""
        research = {
            "company_analysis": {
                "findings": [
                    "For example, companies like yours typically face challenges.",
                    "In general, businesses can benefit from automation.",
                    "Such as implementing AI solutions.",
                    "Typically, organizations see improvements.",
                ],
            },
            "industry_intelligence": {
                "trends": [
                    "Companies are generally adopting AI.",
                ],
            },
            "research_metadata": {
                "total_findings": 5,
                "sources_consulted": 2,
            },
        }

        result = validator.validate(
            request=sample_request,
            research_findings=research,
            call_id="call-006",
        )

        assert result.is_specific is False
        assert any("generic" in issue.lower() for issue in result.issues)

    def test_should_fail_when_research_has_insufficient_depth(
        self, validator: Call1Validator, sample_request: CompassRequest
    ):
        """Research with too few findings fails."""
        research = {
            "company_analysis": {
                "findings": ["Acme Legal exists"],
            },
            "research_metadata": {
                "total_findings": 1,
                "sources_consulted": 1,
            },
        }

        result = validator.validate(
            request=sample_request,
            research_findings=research,
            call_id="call-007",
        )

        assert result.is_complete is False
        assert any("insufficient" in issue.lower() or "depth" in issue.lower() for issue in result.issues)

    # ===========================================
    # EDGE CASES
    # ===========================================

    def test_should_handle_empty_research(
        self, validator: Call1Validator, sample_request: CompassRequest
    ):
        """Empty research fails gracefully."""
        research = {}

        result = validator.validate(
            request=sample_request,
            research_findings=research,
            call_id="call-008",
        )

        assert result.passed is False
        assert result.score <= 3
        assert result.is_complete is False

    def test_should_handle_research_with_not_found_markers(
        self, validator: Call1Validator, sample_request: CompassRequest
    ):
        """Research with NOT_FOUND markers is handled appropriately."""
        research = {
            "company_analysis": {
                "company_name": "Acme Legal Services",
                "tech_stack": "NOT_FOUND",
                "findings": [
                    "Acme Legal Services is a law firm",
                    "Tech stack information not publicly available",
                ],
            },
            "industry_intelligence": {
                "industry": "Law Firm",
                "trends": ["Contract review automation"],
            },
            "research_metadata": {
                "total_findings": 8,
                "sources_consulted": 5,
                "research_gaps": ["Tech stack not found"],
            },
        }

        result = validator.validate(
            request=sample_request,
            research_findings=research,
            call_id="call-009",
        )

        # NOT_FOUND is acceptable if research is otherwise good
        assert result.passed is True
        assert result.is_relevant is True

    # ===========================================
    # OUTPUT FORMAT
    # ===========================================

    def test_should_populate_all_result_fields(
        self, validator: Call1Validator, sample_request: CompassRequest
    ):
        """Result should have all fields populated for sheets logging."""
        research = {
            "company_analysis": {"findings": ["Acme Legal Services data"]},
            "industry_intelligence": {"industry": "Law Firm"},
            "research_metadata": {"total_findings": 5, "sources_consulted": 3},
        }

        result = validator.validate(
            request=sample_request,
            research_findings=research,
            call_id="call-010",
        )

        # Check all fields are populated
        assert result.call_id == "call-010"
        assert result.call_number == 1
        assert result.call_type == "Research"
        assert result.company_name == "Acme Legal Services"
        assert result.industry == "Law Firm"
        assert result.pain_point == "Manual contract review taking too long"
        assert isinstance(result.score, int)
        assert isinstance(result.passed, bool)
        assert isinstance(result.is_relevant, bool)
        assert isinstance(result.is_specific, bool)
        assert isinstance(result.is_complete, bool)
        assert isinstance(result.issues, list)
        assert isinstance(result.recommendations, list)

    def test_to_sheets_row_returns_correct_columns(
        self, validator: Call1Validator, sample_request: CompassRequest
    ):
        """to_sheets_row() returns correct number of columns."""
        research = {
            "company_analysis": {"findings": ["Test"]},
            "research_metadata": {"total_findings": 1, "sources_consulted": 1},
        }

        result = validator.validate(
            request=sample_request,
            research_findings=research,
            call_id="call-011",
        )
        result.run_id = "test-run-123"

        row = result.to_sheets_row()

        assert len(row) == 19  # 19 columns per schema
        assert row[1] == "test-run-123"  # Run ID
        assert row[2] == 1  # Call Number
        assert row[3] == "Research"  # Call Type

    def test_recommendations_are_actionable(
        self, validator: Call1Validator, sample_request: CompassRequest
    ):
        """Recommendations should be actionable prompt fixes."""
        research = {
            "company_analysis": {
                "findings": ["Generic analysis"],
            },
            "research_metadata": {
                "total_findings": 2,
                "sources_consulted": 1,
            },
        }

        result = validator.validate(
            request=sample_request,
            research_findings=research,
            call_id="call-012",
        )

        # Should have recommendations for each issue
        assert len(result.recommendations) > 0
        # Recommendations should reference prompt changes
        for rec in result.recommendations:
            assert any(
                keyword in rec.lower()
                for keyword in ["add", "include", "require", "prompt", "instruction"]
            )
