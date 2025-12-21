"""
Data models for the Testing Context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Tier(str, Enum):
    """Service tier levels."""

    BUDGET = "Budget"
    STANDARD = "Standard"
    PREMIUM = "Premium"
    ALL = "All Tiers (Comparison)"


class Environment(str, Enum):
    """Deployment environments."""

    PRODUCTION = "Production"
    STAGING = "Staging"


@dataclass
class TestConfig:
    """Configuration for a test run."""

    environment: Environment = Environment.PRODUCTION
    tier: Tier | str = Tier.STANDARD
    count: int = 50  # Number of test cases to run (1-50)
    parallel: bool = True  # Run tests in parallel
    max_parallel: int = 5  # Max concurrent tests

    @property
    def run_all_tiers(self) -> bool:
        """Check if running all tiers for comparison."""
        return self.tier == Tier.ALL or self.tier == "All Tiers (Comparison)"

    @property
    def tiers_to_run(self) -> list[str]:
        """Get list of tiers to run."""
        if self.run_all_tiers:
            return [Tier.BUDGET.value, Tier.STANDARD.value, Tier.PREMIUM.value]
        return [self.tier if isinstance(self.tier, str) else self.tier.value]


@dataclass
class TestCase:
    """A single test case."""

    company: str
    prompt: str
    category: str = ""  # e.g., "High Compliance", "Data Heavy"
    test_id: str = ""

    def __post_init__(self):
        if not self.test_id:
            self.test_id = self.company.lower().replace(" ", "_")


@dataclass
class TestResult:
    """Result from a single test case execution."""

    test_case: TestCase
    tier: str
    environment: str
    success: bool
    run_id: str
    workflow_count: int = 0
    phase_count: int = 0
    consensus_strength: str = ""
    confidence_percent: int = 0
    qa_score: int | None = None
    qa_passed: bool | None = None
    error_message: str | None = None
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "test_id": self.test_case.test_id,
            "company": self.test_case.company,
            "tier": self.tier,
            "environment": self.environment,
            "success": self.success,
            "run_id": self.run_id,
            "workflow_count": self.workflow_count,
            "phase_count": self.phase_count,
            "consensus_strength": self.consensus_strength,
            "confidence_percent": self.confidence_percent,
            "qa_score": self.qa_score,
            "qa_passed": self.qa_passed,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TestSuiteResult:
    """Result from running a full test suite."""

    config: TestConfig
    results: list[TestResult]
    start_time: datetime
    end_time: datetime
    total_tests: int = 0
    passed: int = 0
    failed: int = 0

    def __post_init__(self):
        self.total_tests = len(self.results)
        self.passed = sum(1 for r in self.results if r.success)
        self.failed = self.total_tests - self.passed

    @property
    def duration_seconds(self) -> float:
        """Total test suite duration."""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def pass_rate(self) -> float:
        """Percentage of tests that passed."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    @property
    def avg_qa_score(self) -> float | None:
        """Average QA score across all tests."""
        scores = [r.qa_score for r in self.results if r.qa_score is not None]
        if not scores:
            return None
        return sum(scores) / len(scores)

    def summary(self) -> dict[str, Any]:
        """Generate summary statistics."""
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": f"{self.pass_rate:.1f}%",
            "duration_seconds": self.duration_seconds,
            "avg_qa_score": self.avg_qa_score,
            "tiers_tested": list(set(r.tier for r in self.results)),
            "environment": self.config.environment.value,
        }
