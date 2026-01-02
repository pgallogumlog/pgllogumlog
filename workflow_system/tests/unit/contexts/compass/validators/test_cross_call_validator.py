"""
Unit tests for CrossCallValidator - Cross-call integration validation.

TDD: These tests define expected behavior. Implementation follows.
NO MOCKING of core validation logic - tests use real data.
"""

import pytest

from contexts.compass.validators.cross_call_validator import CrossCallValidator
from contexts.compass.validators.models import CrossCallQAResult


class TestCrossCallValidator:
    """Tests for Cross-Call validation (Call 2 uses Call 1)."""

    @pytest.fixture
    def validator(self) -> CrossCallValidator:
        """Create validator instance."""
        return CrossCallValidator()

    # ===========================================
    # PASS CASES - Synthesis uses research
    # ===========================================

    def test_should_pass_when_synthesis_cites_research_findings(
        self, validator: CrossCallValidator
    ):
        """Synthesis that references research findings passes."""
        research = {
            "company_analysis": {
                "company_name": "Acme Legal Services",
                "tech_stack": ["Document management system", "Email"],
                "findings": [
                    "Acme Legal processes 500 contracts monthly",
                    "Current review takes 2 hours per contract",
                    "No existing automation tools",
                ],
            },
            "industry_intelligence": {
                "industry": "Law Firm",
                "trends": [
                    "AI contract review reduces time by 60%",
                    "RAG systems popular for legal research",
                ],
                "competitors": ["LegalZoom uses AI", "Rocket Lawyer automated"],
            },
            "implementation_patterns": {
                "use_cases": [
                    "Clause extraction with NLP",
                    "Risk flagging automation",
                ],
            },
        }

        synthesis = {
            "priorities": [
                {
                    "rank": 1,
                    "problem_name": "Contract Review Automation",
                    "problem_description": "Acme Legal processes 500 contracts monthly at 2 hours each",
                    "research_support": "Industry shows 60% time reduction with AI",
                    "solution": {
                        "name": "AI Contract Analyzer",
                        "description": "Implement clause extraction with NLP",
                    },
                },
                {
                    "rank": 2,
                    "problem_name": "Legal Research Enhancement",
                    "research_support": "RAG systems popular for legal research",
                    "solution": {"name": "Legal RAG System"},
                },
                {
                    "rank": 3,
                    "problem_name": "Risk Assessment",
                    "research_support": "Risk flagging automation proven effective",
                    "solution": {"name": "Risk Flagger"},
                },
            ],
        }

        result = validator.validate(research, synthesis)

        assert isinstance(result, CrossCallQAResult)
        assert result.passed is True
        assert result.score >= 7
        assert result.call_2_references_call_1 is True
        assert result.research_used_count > 0
        assert result.research_used_percent > 30

    def test_should_calculate_research_usage_percentage(
        self, validator: CrossCallValidator
    ):
        """Validate research usage percentage calculation."""
        research = {
            "company_analysis": {
                "findings": ["Finding A", "Finding B", "Finding C", "Finding D"],
            },
            "industry_intelligence": {
                "trends": ["Trend 1", "Trend 2"],
            },
        }

        # Synthesis that uses some but not all findings
        synthesis = {
            "priorities": [
                {
                    "problem_description": "Finding A is important",
                    "research_support": "Finding B supports this",
                },
                {
                    "problem_description": "Based on Trend 1",
                    "research_support": "Trend 2 confirms",
                },
            ],
        }

        result = validator.validate(research, synthesis)

        # Should have calculated percentage
        assert result.research_used_percent >= 0
        assert result.research_used_percent <= 100
        assert result.research_total_count > 0

    # ===========================================
    # FAIL CASES - Synthesis ignores research
    # ===========================================

    def test_should_fail_when_synthesis_ignores_research(
        self, validator: CrossCallValidator
    ):
        """Synthesis that doesn't reference research fails."""
        research = {
            "company_analysis": {
                "company_name": "Acme Legal Services",
                "findings": [
                    "Acme Legal has 50 attorneys",
                    "Specializes in corporate M&A",
                    "Uses legacy document management",
                ],
            },
            "industry_intelligence": {
                "trends": [
                    "AI adoption growing in legal sector",
                    "Contract automation trending",
                ],
            },
        }

        # Synthesis with completely different content
        synthesis = {
            "priorities": [
                {
                    "problem_name": "Marketing Improvement",
                    "problem_description": "Need better social media presence",
                    "solution": {"name": "Social Media Manager"},
                },
                {
                    "problem_name": "Customer Service",
                    "problem_description": "Improve customer satisfaction",
                    "solution": {"name": "Support Bot"},
                },
            ],
        }

        result = validator.validate(research, synthesis)

        assert result.passed is False
        assert result.call_2_references_call_1 is False
        assert any("research" in issue.lower() or "citation" in issue.lower() for issue in result.issues)

    def test_should_fail_when_low_research_utilization(
        self, validator: CrossCallValidator
    ):
        """Synthesis that uses very little research fails."""
        research = {
            "company_analysis": {
                "findings": [
                    "Very specific finding 1 about company",
                    "Very specific finding 2 about tech",
                    "Very specific finding 3 about process",
                    "Very specific finding 4 about team",
                    "Very specific finding 5 about challenges",
                ],
            },
            "industry_intelligence": {
                "trends": [
                    "Industry trend alpha",
                    "Industry trend beta",
                    "Industry trend gamma",
                ],
            },
        }

        # Synthesis that barely uses research
        synthesis = {
            "priorities": [
                {
                    "problem_name": "Generic Problem",
                    "problem_description": "Businesses need improvement",
                    "solution": {"name": "Generic Solution"},
                },
            ],
        }

        result = validator.validate(research, synthesis)

        assert result.research_used_percent < 30
        assert any("utilization" in issue.lower() or "cite" in issue.lower() for issue in result.issues)

    def test_should_track_orphaned_findings(
        self, validator: CrossCallValidator
    ):
        """Track research findings that weren't used in synthesis."""
        research = {
            "company_analysis": {
                "findings": [
                    "Important finding 1",
                    "Important finding 2",
                    "Important finding 3",
                ],
            },
        }

        synthesis = {
            "priorities": [
                {
                    "problem_description": "Based on Important finding 1",
                },
            ],
        }

        result = validator.validate(research, synthesis)

        # Should track orphaned findings
        assert result.orphaned_findings_count >= 0
        assert result.research_total_count >= result.research_used_count

    # ===========================================
    # EDGE CASES
    # ===========================================

    def test_should_handle_empty_research(
        self, validator: CrossCallValidator
    ):
        """Empty research handled gracefully."""
        research = {}
        synthesis = {
            "priorities": [{"problem_name": "Test"}],
        }

        result = validator.validate(research, synthesis)

        # Can't fail for not citing empty research
        assert result.research_total_count == 0

    def test_should_handle_empty_synthesis(
        self, validator: CrossCallValidator
    ):
        """Empty synthesis fails validation."""
        research = {
            "company_analysis": {
                "findings": ["Finding 1", "Finding 2"],
            },
        }
        synthesis = {}

        result = validator.validate(research, synthesis)

        assert result.passed is False
        assert result.call_2_references_call_1 is False

    def test_should_be_case_insensitive(
        self, validator: CrossCallValidator
    ):
        """Citation matching should be case insensitive."""
        research = {
            "company_analysis": {
                "findings": ["UPPERCASE FINDING"],
            },
        }
        synthesis = {
            "priorities": [
                {
                    "problem_description": "Based on uppercase finding",
                },
            ],
        }

        result = validator.validate(research, synthesis)

        # Should match despite case difference
        assert result.research_used_count > 0

    # ===========================================
    # OUTPUT FORMAT
    # ===========================================

    def test_should_populate_all_result_fields(
        self, validator: CrossCallValidator
    ):
        """Result should have all expected fields."""
        research = {
            "company_analysis": {"findings": ["Test finding"]},
        }
        synthesis = {
            "priorities": [{"problem_description": "Test finding based"}],
        }

        result = validator.validate(research, synthesis)

        assert isinstance(result.passed, bool)
        assert isinstance(result.score, int)
        assert isinstance(result.call_2_references_call_1, bool)
        assert isinstance(result.research_used_count, int)
        assert isinstance(result.research_total_count, int)
        assert isinstance(result.orphaned_findings_count, int)
        assert isinstance(result.issues, list)
        assert isinstance(result.recommendations, list)

    def test_recommendations_should_be_actionable(
        self, validator: CrossCallValidator
    ):
        """Recommendations should be actionable prompt fixes."""
        research = {
            "company_analysis": {
                "findings": ["Specific research finding"],
            },
        }
        synthesis = {
            "priorities": [
                {"problem_description": "Generic content"},
            ],
        }

        result = validator.validate(research, synthesis)

        if result.recommendations:
            for rec in result.recommendations:
                assert any(
                    keyword in rec.lower()
                    for keyword in ["add", "include", "require", "cite", "reference"]
                )
