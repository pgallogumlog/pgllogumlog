"""
Tests for ResearchQualityGate - HARD blocker for report generation.

Principle: No research = No report = No charge

NOTE ON TEST STRATEGY:
- `_verify_citations` is mocked in integration tests to avoid network calls
- Synchronous helper methods are tested directly with real implementations
- All business logic (thresholds, issue generation) is tested with real code
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiohttp import ClientResponseError

from contexts.compass.validators.research_quality_gate import (
    ResearchQualityGate,
    ResearchQualityResult,
    ResearchFailedError,
    MIN_VERIFIED_SOURCES,
    MIN_UNIQUE_DOMAINS,
    MAX_NOT_FOUND_RATIO,
)


class TestResearchQualityGate:
    """Tests for ResearchQualityGate validation."""

    @pytest.fixture
    def gate(self):
        """Create a quality gate instance."""
        return ResearchQualityGate()

    @pytest.fixture
    def valid_citations(self):
        """Citations that meet all requirements."""
        return [
            {"title": "AI Report", "url": "https://mckinsey.com/ai-report", "snippet": "AI adoption..."},
            {"title": "Gartner", "url": "https://gartner.com/trends", "snippet": "Trends..."},
            {"title": "Forbes", "url": "https://forbes.com/digital", "snippet": "Digital..."},
            {"title": "HBR", "url": "https://hbr.org/ai", "snippet": "AI implementation..."},
            {"title": "Microsoft", "url": "https://microsoft.com/ai", "snippet": "AI solutions..."},
            {"title": "AWS", "url": "https://aws.amazon.com/ai", "snippet": "Cloud AI..."},
            {"title": "Google Cloud", "url": "https://cloud.google.com/ai", "snippet": "AI platform..."},
            {"title": "IBM", "url": "https://ibm.com/watson", "snippet": "Watson AI..."},
            {"title": "Deloitte", "url": "https://deloitte.com/ai-study", "snippet": "Study..."},
            {"title": "PwC", "url": "https://pwc.com/ai", "snippet": "AI report..."},
            {"title": "Accenture", "url": "https://accenture.com/ai", "snippet": "AI trends..."},
        ]

    @pytest.fixture
    def valid_research(self):
        """Research findings with company and industry data."""
        return {
            "company_analysis": {
                "company_profile": "TestCorp is a technology company in Healthcare industry.",
                "digital_maturity": "Medium adoption of digital tools",
            },
            "industry_intelligence": {
                "ai_adoption": "Healthcare AI adoption grew 47% in 2024.",
                "market_trends": "Healthcare spending on AI reached $12.5 billion.",
            },
            "implementation_patterns": {
                "case_studies": ["Hospital ABC increased efficiency by 30%"],
            },
            "research_metadata": {
                "total_findings": 15,
                "high_confidence_findings": 8,
            },
        }

    @pytest.mark.asyncio
    async def test_should_pass_when_all_requirements_met(
        self, gate, valid_citations, valid_research
    ):
        """Quality gate passes when all checks pass."""
        with patch.object(gate, "_verify_citations", return_value=12):
            result = await gate.validate(
                research_findings=valid_research,
                citations=valid_citations,
                company_name="TestCorp",
                industry="Healthcare",
            )

        assert result.passed is True
        assert result.should_cancel_authorization is False
        assert len(result.issues) == 0

    @pytest.mark.asyncio
    async def test_should_fail_when_insufficient_verified_sources(
        self, gate, valid_citations, valid_research
    ):
        """Quality gate fails when not enough verified sources."""
        with patch.object(gate, "_verify_citations", return_value=5):  # Below MIN_VERIFIED_SOURCES
            result = await gate.validate(
                research_findings=valid_research,
                citations=valid_citations,
                company_name="TestCorp",
                industry="Healthcare",
            )

        assert result.passed is False
        assert result.should_cancel_authorization is True
        assert any("INSUFFICIENT SOURCES" in issue for issue in result.issues)

    @pytest.mark.asyncio
    async def test_should_fail_when_low_domain_diversity(self, gate, valid_research):
        """Quality gate fails when not enough unique domains."""
        # All citations from same domain
        citations = [
            {"title": f"Article {i}", "url": f"https://example.com/article-{i}", "snippet": "..."}
            for i in range(15)
        ]

        with patch.object(gate, "_verify_citations", return_value=15):
            result = await gate.validate(
                research_findings=valid_research,
                citations=citations,
                company_name="TestCorp",
                industry="Healthcare",
            )

        assert result.passed is False
        assert any("LOW DIVERSITY" in issue for issue in result.issues)

    @pytest.mark.asyncio
    async def test_should_fail_when_high_not_found_ratio(
        self, gate, valid_citations
    ):
        """Quality gate fails when too many NOT_FOUND values."""
        research = {
            "company_analysis": {
                "company_profile": "Not Found",
                "digital_maturity": "NOT_FOUND",
                "recent_news": "No data available",
            },
            "industry_intelligence": {
                "ai_adoption": "Unable to find",
                "market_trends": "",  # Empty = not found
            },
            "research_metadata": {
                "total_findings": 0,
            },
        }

        with patch.object(gate, "_verify_citations", return_value=15):
            result = await gate.validate(
                research_findings=research,
                citations=valid_citations,
                company_name="TestCorp",
                industry="Healthcare",
            )

        assert result.passed is False
        assert any("HIGH DATA GAPS" in issue for issue in result.issues)

    @pytest.mark.asyncio
    async def test_should_fail_when_no_company_data(
        self, gate, valid_citations
    ):
        """Quality gate fails when no company-specific findings."""
        research = {
            "company_analysis": {
                "profile": "Generic technology company profile",
            },
            "industry_intelligence": {
                "ai_adoption": "Healthcare AI is growing 25% year-over-year.",
            },
            "research_metadata": {},
        }

        with patch.object(gate, "_verify_citations", return_value=15):
            result = await gate.validate(
                research_findings=research,
                citations=valid_citations,
                company_name="SpecificCorp",  # Not mentioned in research
                industry="Healthcare",
            )

        assert result.passed is False
        assert any("NO COMPANY DATA" in issue for issue in result.issues)

    @pytest.mark.asyncio
    async def test_should_fail_when_no_industry_stats(
        self, gate, valid_citations
    ):
        """Quality gate fails when no industry statistics."""
        research = {
            "company_analysis": {
                "profile": "TestCorp is a growing company in Healthcare.",
            },
            "industry_intelligence": {
                "overview": "The industry is evolving.",  # No stats
            },
            "research_metadata": {},
        }

        with patch.object(gate, "_verify_citations", return_value=15):
            result = await gate.validate(
                research_findings=research,
                citations=valid_citations,
                company_name="TestCorp",
                industry="Healthcare",
            )

        assert result.passed is False
        assert any("NO INDUSTRY DATA" in issue for issue in result.issues)

    @pytest.mark.asyncio
    async def test_should_return_correct_counts(
        self, gate, valid_citations, valid_research
    ):
        """Result includes correct counts for monitoring."""
        with patch.object(gate, "_verify_citations", return_value=12):
            result = await gate.validate(
                research_findings=valid_research,
                citations=valid_citations,
                company_name="TestCorp",
                industry="Healthcare",
            )

        assert result.verified_source_count == 12
        assert result.unique_domain_count >= MIN_UNIQUE_DOMAINS
        assert result.total_citations == len(valid_citations)

    @pytest.mark.asyncio
    async def test_should_track_duration(
        self, gate, valid_citations, valid_research
    ):
        """Result includes validation duration for monitoring."""
        with patch.object(gate, "_verify_citations", return_value=12):
            result = await gate.validate(
                research_findings=valid_research,
                citations=valid_citations,
                company_name="TestCorp",
                industry="Healthcare",
            )

        # With mocked HTTP calls, duration may be 0.0ms (too fast to measure)
        # We verify the field exists and is numeric - production calls will be > 0
        assert result.verification_duration_ms >= 0
        assert isinstance(result.verification_duration_ms, float)

    def test_count_unique_domains_extracts_base_domain(self, gate):
        """Domain counter extracts base domain correctly."""
        citations = [
            {"url": "https://www.mckinsey.com/article"},
            {"url": "https://mckinsey.com/different-article"},  # Same domain
            {"url": "https://sub.gartner.com/page"},
            {"url": "https://gartner.com/page2"},  # Same domain
            {"url": "https://forbes.com/tech"},
        ]

        count = gate._count_unique_domains(citations)
        assert count == 3  # mckinsey, gartner, forbes

    def test_calculate_not_found_ratio_handles_empty(self, gate):
        """NOT_FOUND ratio is 1.0 for empty research."""
        ratio = gate._calculate_not_found_ratio({})
        assert ratio == 1.0

    def test_calculate_not_found_ratio_detects_patterns(self, gate):
        """NOT_FOUND ratio detects various not-found patterns."""
        research = {
            "field1": "Not Found",
            "field2": "NOT_FOUND",
            "field3": "No data",
            "field4": "Unable to find",
            "field5": "N/A",
            "field6": "Valid data here",
        }

        ratio = gate._calculate_not_found_ratio(research)
        # 5 out of 6 fields are not found
        assert ratio > 0.5

    def test_has_company_findings_case_insensitive(self, gate):
        """Company name search is case insensitive."""
        research = {
            "analysis": "TESTCORP has strong digital presence.",
        }

        assert gate._has_company_findings(research, "TestCorp") is True
        assert gate._has_company_findings(research, "testcorp") is True
        assert gate._has_company_findings(research, "TESTCORP") is True

    def test_has_industry_stats_requires_numbers(self, gate):
        """Industry stats check requires numerical data."""
        research_without_stats = {
            "industry": "Healthcare is transforming rapidly.",
        }
        research_with_stats = {
            "industry": "Healthcare AI adoption grew 47% in 2024.",
        }

        assert gate._has_industry_stats(research_without_stats, "Healthcare") is False
        assert gate._has_industry_stats(research_with_stats, "Healthcare") is True

    def test_has_industry_stats_with_dollar_amounts(self, gate):
        """Industry stats detects dollar amounts."""
        research = {
            "market": "Healthcare AI market reached $12.5 billion in 2024.",
        }
        assert gate._has_industry_stats(research, "Healthcare") is True

    def test_has_industry_stats_with_growth_metrics(self, gate):
        """Industry stats detects growth metrics."""
        research = {
            "growth": "Healthcare spending increased by 25 in 2024.",
        }
        assert gate._has_industry_stats(research, "Healthcare") is True

    def test_has_company_findings_returns_false_for_empty(self, gate):
        """Company findings check returns False for empty research."""
        assert gate._has_company_findings({}, "TestCorp") is False
        assert gate._has_company_findings({"data": "value"}, "") is False

    def test_has_company_findings_skips_metadata_keys(self, gate):
        """Company findings check skips metadata keys."""
        research = {
            "_citations": "TestCorp mentioned here",
            "research_metadata": "TestCorp also here",
            "actual_data": "No company name here",
        }
        # Should return False because TestCorp only appears in metadata
        assert gate._has_company_findings(research, "TestCorp") is False

    def test_has_company_findings_searches_nested_data(self, gate):
        """Company findings check searches nested structures."""
        research = {
            "analysis": {
                "company": {
                    "profile": "TestCorp is a leading company",
                }
            }
        }
        assert gate._has_company_findings(research, "TestCorp") is True

    def test_calculate_not_found_ratio_with_nested_empty_values(self, gate):
        """NOT_FOUND ratio handles nested empty values."""
        research = {
            "level1": {
                "level2": {
                    "empty": "",
                    "none": None,
                    "valid": "data",
                }
            }
        }
        ratio = gate._calculate_not_found_ratio(research)
        # 2 out of 3 nested values are empty/None
        assert ratio > 0.5

    def test_calculate_not_found_ratio_with_empty_list(self, gate):
        """NOT_FOUND ratio treats empty lists as not found."""
        research = {
            "items": [],  # Empty list = not found
            "valid": ["item1", "item2"],
        }
        ratio = gate._calculate_not_found_ratio(research)
        # Empty list counts as 1 not found, valid list has 2 items
        assert ratio > 0

    def test_count_unique_domains_handles_subdomains(self, gate):
        """Domain counter handles various subdomain patterns."""
        citations = [
            {"url": "https://www.example.com/page"},
            {"url": "https://api.example.com/data"},  # Same base domain
            {"url": "https://blog.other.org/article"},
            {"url": "https://www.other.org/main"},  # Same base domain
        ]
        count = gate._count_unique_domains(citations)
        assert count == 2  # example.com, other.org

    def test_count_unique_domains_handles_invalid_urls(self, gate):
        """Domain counter handles invalid URLs gracefully."""
        citations = [
            {"url": "not-a-url"},
            {"url": ""},
            {"url": None},
            {"url": "https://valid.com/page"},
        ]
        count = gate._count_unique_domains(citations)
        assert count == 1  # Only valid.com

    def test_count_unique_domains_is_case_insensitive(self, gate):
        """Domain counter treats URLs case-insensitively."""
        citations = [
            {"url": "https://Example.COM/page"},
            {"url": "https://EXAMPLE.com/other"},
        ]
        count = gate._count_unique_domains(citations)
        assert count == 1  # Both are example.com


class TestVerifyCitationsMethod:
    """Tests for _verify_citations method (HTTP verification logic)."""

    @pytest.fixture
    def gate(self):
        return ResearchQualityGate()

    @pytest.mark.asyncio
    async def test_verify_citations_returns_zero_for_empty_list(self, gate):
        """Verify returns 0 for empty citation list."""
        result = await gate._verify_citations([])
        assert result == 0

    @pytest.mark.asyncio
    async def test_verify_citations_filters_invalid_urls(self, gate):
        """Verify filters out invalid URLs before checking."""
        # Mock aiohttp to avoid real network calls
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session_instance = MagicMock()
            mock_session_instance.head = MagicMock(return_value=mock_response)
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_session_instance

            citations = [
                {"url": "not-a-valid-url"},
                {"url": "ftp://wrong-protocol.com"},
                {"url": ""},
            ]

            result = await gate._verify_citations(citations)
            # None of these are valid HTTP(S) URLs, so result is 0
            # The check happens BEFORE the HTTP call
            assert result == 0


class TestResearchQualityResult:
    """Tests for ResearchQualityResult dataclass."""

    def test_to_sheets_row_format(self):
        """Result converts to correct sheets row format."""
        result = ResearchQualityResult(
            passed=True,
            verified_source_count=12,
            unique_domain_count=5,
            not_found_ratio=0.1,
            has_company_data=True,
            has_industry_stats=True,
            issues=[],
            total_citations=15,
            verification_duration_ms=250.5,
        )

        row = result.to_sheets_row()

        assert len(row) == 10
        assert row[1] == "PASS"
        assert row[2] == 12  # verified sources
        assert row[3] == 5  # unique domains
        assert row[5] == "TRUE"  # has company data
        assert row[6] == "TRUE"  # has industry stats

    def test_headers_match_row_length(self):
        """Headers match the number of columns in row."""
        result = ResearchQualityResult(
            passed=False,
            verified_source_count=5,
            unique_domain_count=2,
            not_found_ratio=0.5,
            issues=["Issue 1", "Issue 2"],
        )

        headers = ResearchQualityResult.get_headers()
        row = result.to_sheets_row()

        assert len(headers) == len(row)


class TestResearchFailedError:
    """Tests for ResearchFailedError exception."""

    def test_stores_issues(self):
        """Error stores list of issues."""
        issues = ["INSUFFICIENT SOURCES", "NO COMPANY DATA"]
        error = ResearchFailedError(issues)

        assert error.issues == issues
        assert error.cancel_authorization is True

    def test_formats_message(self):
        """Error message includes all issues."""
        issues = ["Issue 1", "Issue 2"]
        error = ResearchFailedError(issues)

        assert "Issue 1" in str(error)
        assert "Issue 2" in str(error)


class TestQualityGateThresholds:
    """
    Tests that verify the quality gate uses the correct thresholds.

    These tests would FAIL if the threshold logic was removed or changed.
    """

    def test_min_verified_sources_is_10(self):
        """Verify MIN_VERIFIED_SOURCES constant is 10."""
        assert MIN_VERIFIED_SOURCES == 10

    def test_min_unique_domains_is_3(self):
        """Verify MIN_UNIQUE_DOMAINS constant is 3."""
        assert MIN_UNIQUE_DOMAINS == 3

    def test_max_not_found_ratio_is_30_percent(self):
        """Verify MAX_NOT_FOUND_RATIO constant is 0.30."""
        assert MAX_NOT_FOUND_RATIO == 0.30

    @pytest.mark.asyncio
    async def test_gate_uses_configured_thresholds(self):
        """Gate should use the thresholds passed to constructor."""
        custom_gate = ResearchQualityGate(
            min_verified_sources=5,
            min_unique_domains=2,
            max_not_found_ratio=0.50,
        )

        # With 5 verified sources (at threshold), should pass that check
        with patch.object(custom_gate, "_verify_citations", return_value=5):
            result = await custom_gate.validate(
                research_findings={"data": "TestCorp in Healthcare grew 25% in 2024"},
                citations=[{"url": f"https://domain{i}.com"} for i in range(5)],
                company_name="TestCorp",
                industry="Healthcare",
            )

        # Should pass because we meet the custom lower thresholds
        # The 5 citations from 5 different domains meets min_unique_domains=2
        # The research has valid data, so NOT_FOUND ratio is low
        # Company name and industry stats are present
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_gate_fails_exactly_at_threshold_boundary(self):
        """Gate should fail when EXACTLY below threshold."""
        gate = ResearchQualityGate()

        # With 9 verified sources (1 below threshold of 10), should fail
        with patch.object(gate, "_verify_citations", return_value=9):
            result = await gate.validate(
                research_findings={"data": "TestCorp in Healthcare grew 25%"},
                citations=[{"url": f"https://domain{i}.com"} for i in range(10)],
                company_name="TestCorp",
                industry="Healthcare",
            )

        assert result.passed is False
        assert "INSUFFICIENT SOURCES: 9/10" in str(result.issues)


class TestBusinessLogicIntegrity:
    """
    Tests that verify the business logic is actually enforced.

    If someone removed or modified the validation logic, these tests would fail.
    """

    @pytest.fixture
    def gate(self):
        return ResearchQualityGate()

    @pytest.mark.asyncio
    async def test_all_five_checks_are_performed(self, gate):
        """All 5 quality checks must be performed."""
        # Create conditions that fail ALL checks
        with patch.object(gate, "_verify_citations", return_value=0):
            result = await gate.validate(
                research_findings={},  # Empty = fails NOT_FOUND, company, industry
                citations=[],  # Empty = fails verified sources, domain diversity
                company_name="TestCorp",
                industry="Healthcare",
            )

        # All 5 checks should have generated issues
        assert result.passed is False
        assert len(result.issues) >= 5
        assert any("INSUFFICIENT SOURCES" in issue for issue in result.issues)
        assert any("LOW DIVERSITY" in issue for issue in result.issues)
        assert any("HIGH DATA GAPS" in issue for issue in result.issues)
        assert any("NO COMPANY DATA" in issue for issue in result.issues)
        assert any("NO INDUSTRY DATA" in issue for issue in result.issues)

    @pytest.mark.asyncio
    async def test_should_cancel_authorization_is_opposite_of_passed(self, gate):
        """should_cancel_authorization must be True when passed is False."""
        with patch.object(gate, "_verify_citations", return_value=0):
            failed_result = await gate.validate(
                research_findings={},
                citations=[],
                company_name="TestCorp",
                industry="Healthcare",
            )

        # If passed is False, should_cancel_authorization MUST be True
        assert failed_result.passed is False
        assert failed_result.should_cancel_authorization is True

        # If passed is True, should_cancel_authorization MUST be False
        with patch.object(gate, "_verify_citations", return_value=15):
            passed_result = await gate.validate(
                research_findings={
                    "data": "TestCorp in Healthcare grew 47% in 2024."
                },
                citations=[{"url": f"https://domain{i}.com"} for i in range(15)],
                company_name="TestCorp",
                industry="Healthcare",
            )

        assert passed_result.passed is True
        assert passed_result.should_cancel_authorization is False

    def test_not_found_patterns_are_actually_detected(self, gate):
        """Each NOT_FOUND pattern must be detected."""
        patterns_to_test = [
            ("Not Found", True),
            ("NOT_FOUND", True),
            ("No data", True),
            ("Unable to find", True),
            ("N/A", True),
            ("not available", True),
            ("Valid data here", False),
            ("42% growth", False),
        ]

        for text, should_be_not_found in patterns_to_test:
            research = {"field": text}
            ratio = gate._calculate_not_found_ratio(research)
            if should_be_not_found:
                assert ratio > 0, f"'{text}' should be detected as NOT_FOUND"
            else:
                assert ratio == 0, f"'{text}' should NOT be detected as NOT_FOUND"

    def test_industry_stat_patterns_are_actually_detected(self, gate):
        """Each industry statistic pattern must be detected."""
        patterns_to_test = [
            ("Healthcare AI grew 47%", True),  # Percentage
            ("Healthcare market is $12 billion", True),  # Dollar amount
            ("Healthcare spending increased by 25", True),  # Growth metric
            ("Healthcare is growing rapidly", False),  # No numbers
            ("Technology sector saw 30% growth", False),  # Wrong industry
        ]

        for text, should_have_stats in patterns_to_test:
            research = {"field": text}
            result = gate._has_industry_stats(research, "Healthcare")
            if should_have_stats:
                assert result is True, f"'{text}' should be detected as industry stat"
            else:
                assert result is False, f"'{text}' should NOT be detected as industry stat"
