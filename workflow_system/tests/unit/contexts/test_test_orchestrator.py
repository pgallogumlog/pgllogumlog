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
