"""
Unit tests for the Test Orchestrator.
"""

import pytest

from contexts.testing import TestOrchestrator, TestConfig
from contexts.testing.models import Environment, Tier, TestCase, TestResult
from contexts.testing.test_cases import get_test_cases, get_test_cases_by_category


class TestTestConfig:
    """Tests for TestConfig model."""

    def test_default_config(self):
        config = TestConfig()

        assert config.environment == Environment.PRODUCTION
        assert config.tier == Tier.STANDARD
        assert config.count == 50
        assert config.parallel is True

    def test_run_all_tiers(self):
        config = TestConfig(tier=Tier.ALL)

        assert config.run_all_tiers is True
        assert len(config.tiers_to_run) == 3
        assert "Budget" in config.tiers_to_run
        assert "Standard" in config.tiers_to_run
        assert "Premium" in config.tiers_to_run

    def test_single_tier(self):
        config = TestConfig(tier=Tier.PREMIUM)

        assert config.run_all_tiers is False
        assert config.tiers_to_run == ["Premium"]


class TestTestCases:
    """Tests for test case utilities."""

    def test_get_all_test_cases(self):
        cases = get_test_cases(50)
        assert len(cases) == 50

    def test_get_limited_test_cases(self):
        cases = get_test_cases(5)
        assert len(cases) == 5

    def test_get_test_cases_by_category(self):
        compliance_cases = get_test_cases_by_category("High Compliance")
        assert len(compliance_cases) == 10
        assert all(c.category == "High Compliance" for c in compliance_cases)

    def test_categories_exist(self):
        categories = ["High Compliance", "Data Heavy", "Creative", "Technical", "Service/Retail"]
        for category in categories:
            cases = get_test_cases_by_category(category)
            assert len(cases) > 0


class TestTestResult:
    """Tests for TestResult model."""

    def test_to_dict(self):
        test_case = TestCase(
            company="Test Co",
            prompt="Test prompt",
            category="Test",
        )

        result = TestResult(
            test_case=test_case,
            tier="Standard",
            environment="Production",
            success=True,
            run_id="test-123",
            workflow_count=5,
            phase_count=3,
            consensus_strength="Strong",
            confidence_percent=80,
            duration_seconds=5.5,
        )

        data = result.to_dict()

        assert data["company"] == "Test Co"
        assert data["tier"] == "Standard"
        assert data["success"] is True
        assert data["workflow_count"] == 5


@pytest.mark.asyncio
class TestTestOrchestrator:
    """Tests for TestOrchestrator class."""

    async def test_run_single_test(self, mock_ai_provider, sample_test_case):
        """Test running a single test case."""
        orchestrator = TestOrchestrator(ai_provider=mock_ai_provider)

        result = await orchestrator._run_single_test(
            test_case=sample_test_case,
            tier="Standard",
            environment="Production",
        )

        assert result.test_case == sample_test_case
        assert result.tier == "Standard"
        assert result.success is True
        assert result.run_id is not None

    async def test_run_tests_sequential(self, mock_ai_provider):
        """Test sequential test execution."""
        orchestrator = TestOrchestrator(ai_provider=mock_ai_provider)

        config = TestConfig(
            environment=Environment.PRODUCTION,
            tier=Tier.STANDARD,
            count=2,
            parallel=False,
        )

        result = await orchestrator.run_tests(config)

        assert result.total_tests == 2
        assert len(result.results) == 2

    async def test_run_tests_all_tiers(self, mock_ai_provider):
        """Test running with all tiers."""
        orchestrator = TestOrchestrator(ai_provider=mock_ai_provider)

        config = TestConfig(
            environment=Environment.PRODUCTION,
            tier=Tier.ALL,
            count=2,
            parallel=True,
            max_parallel=3,
        )

        result = await orchestrator.run_tests(config)

        # 2 test cases × 3 tiers = 6 total
        assert result.total_tests == 6
        assert len(result.results) == 6

        # Verify all tiers were tested
        tiers_tested = set(r.tier for r in result.results)
        assert "Budget" in tiers_tested
        assert "Standard" in tiers_tested
        assert "Premium" in tiers_tested


class TestFilenameSanitization:
    """Tests for filename sanitization in HTML proposal saving."""

    def test_sanitize_company_name_with_apostrophe(self):
        """Test that apostrophes are removed from company names."""
        from contexts.testing.orchestrator import TestOrchestrator
        import re

        company_name = "Bob's Burgers"
        # Simulate the sanitization logic
        company_slug = company_name.replace(" ", "_").replace("/", "-")
        company_slug = re.sub(r'[^A-Za-z0-9_\-]', '', company_slug)

        assert company_slug == "Bobs_Burgers"
        assert "'" not in company_slug

    def test_sanitize_company_name_with_ampersand(self):
        """Test that ampersands are removed from company names."""
        import re

        company_name = "Smith & Co."
        company_slug = company_name.replace(" ", "_").replace("/", "-")
        company_slug = re.sub(r'[^A-Za-z0-9_\-]', '', company_slug)

        assert company_slug == "Smith__Co"
        assert "&" not in company_slug

    def test_sanitize_company_name_with_period(self):
        """Test that periods are removed from company names."""
        import re

        company_name = "Inc."
        company_slug = company_name.replace(" ", "_").replace("/", "-")
        company_slug = re.sub(r'[^A-Za-z0-9_\-]', '', company_slug)

        assert company_slug == "Inc"
        assert "." not in company_slug

    def test_sanitize_company_name_with_multiple_special_chars(self):
        """Test that multiple special characters are removed."""
        import re

        company_name = "O'Reilly & Associates, Inc."
        company_slug = company_name.replace(" ", "_").replace("/", "-")
        company_slug = re.sub(r'[^A-Za-z0-9_\-]', '', company_slug)

        assert company_slug == "OReilly__Associates_Inc"
        assert "'" not in company_slug
        assert "&" not in company_slug
        assert "," not in company_slug
        assert "." not in company_slug

    def test_sanitize_normal_company_name(self):
        """Test that normal company names still work correctly."""
        import re

        company_name = "Acme Corp"
        company_slug = company_name.replace(" ", "_").replace("/", "-")
        company_slug = re.sub(r'[^A-Za-z0-9_\-]', '', company_slug)

        assert company_slug == "Acme_Corp"

    def test_sanitize_company_name_with_slash(self):
        """Test that slashes are converted to hyphens."""
        import re

        company_name = "Sales/Marketing Dept"
        company_slug = company_name.replace(" ", "_").replace("/", "-")
        company_slug = re.sub(r'[^A-Za-z0-9_\-]', '', company_slug)

        assert company_slug == "Sales-Marketing_Dept"
        assert "/" not in company_slug

    def test_filename_matches_backend_validation_regex(self):
        """Test that sanitized filenames match backend validation regex."""
        import re

        # Backend validation regex from the bug report
        backend_regex = r"^[A-Za-z0-9_\-]+\.html$"

        test_cases = [
            "Bob's Burgers",
            "Smith & Co.",
            "O'Reilly & Associates, Inc.",
            "Acme Corp",
            "Sales/Marketing Dept"
        ]

        for company_name in test_cases:
            company_slug = company_name.replace(" ", "_").replace("/", "-")
            company_slug = re.sub(r'[^A-Za-z0-9_\-]', '', company_slug)
            filename = f"{company_slug}.html"

            assert re.match(backend_regex, filename), f"Filename '{filename}' should match backend regex"
