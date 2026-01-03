"""
Data models for the QA Context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class Severity(str, Enum):
    """Severity levels for QA findings."""

    CRITICAL = "critical"  # Score: 2 - Won't execute
    HIGH = "high"  # Score: 5 - Wrong results
    MEDIUM = "medium"  # Score: 7 - Edge case bugs
    LOW = "low"  # Score: 8 - Minor issues
    NONE = "none"  # Score: 10 - Production-ready

    @property
    def base_score(self) -> int:
        """Get the base score for this severity level."""
        scores = {
            Severity.CRITICAL: 2,
            Severity.HIGH: 5,
            Severity.MEDIUM: 7,
            Severity.LOW: 8,
            Severity.NONE: 10,
        }
        return scores[self]


class FailureType(str, Enum):
    """Types of failures that can be detected."""

    LOGIC_ERROR = "logic_error"
    FORMAT_VIOLATION = "format_violation"
    HALLUCINATION = "hallucination"
    TRUNCATION = "truncation"
    VALIDATION_ERROR = "validation_error"
    NONE = "none"


@dataclass
class CallScore:
    """
    Aggregate score for a single AI call.

    Computed from validation results by the CallScorer.
    """

    call_id: str
    overall_score: int  # 1-10
    passed: bool  # True if score >= threshold (default 7)
    worst_severity: Severity
    check_scores: dict[str, int] = field(default_factory=dict)  # Individual check scores
    deterministic_passed: bool = True  # All deterministic checks passed
    probabilistic_passed: Optional[bool] = None  # None if not run

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "call_id": self.call_id,
            "overall_score": self.overall_score,
            "passed": self.passed,
            "worst_severity": self.worst_severity.value,
            "check_scores": self.check_scores,
            "deterministic_passed": self.deterministic_passed,
            "probabilistic_passed": self.probabilistic_passed,
        }
