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

    CRITICAL = "critical"  # Score: 2 - Workflow won't execute
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
class QAResult:
    """Result from quality analysis."""

    score: int  # 1-10
    passed: bool  # True if score >= min_pass_score
    severity: Severity
    failure_type: FailureType
    failing_node_name: str  # Which component failed
    root_cause: str  # Brief explanation of the problem
    suggested_prompt_fix: str  # How to fix the prompt
    critique: str  # Detailed analysis
    run_id: str = ""
    client_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    was_truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "run_id": self.run_id,
            "client_name": self.client_name,
            "score": self.score,
            "passed": self.passed,
            "severity": self.severity.value,
            "failure_type": self.failure_type.value,
            "failing_node_name": self.failing_node_name,
            "root_cause": self.root_cause,
            "suggested_prompt_fix": self.suggested_prompt_fix,
            "critique": self.critique,
            "timestamp": self.timestamp.isoformat(),
            "was_truncated": self.was_truncated,
        }

    def to_sheets_row(self) -> list[Any]:
        """Convert to a row for Google Sheets."""
        return [
            self.timestamp.isoformat(),
            self.run_id,
            self.client_name,
            self.score,
            "PASS" if self.passed else "FAIL",
            self.critique,
            self.suggested_prompt_fix,
        ]


@dataclass
class QAConfig:
    """Configuration for QA analysis."""

    min_pass_score: int = 7
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.1
    max_tokens: int = 16384

    # Severity scoring thresholds
    severity_scores: dict[Severity, int] = field(default_factory=lambda: {
        Severity.CRITICAL: 2,
        Severity.HIGH: 5,
        Severity.MEDIUM: 7,
        Severity.LOW: 8,
        Severity.NONE: 10,
    })


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


@dataclass
class WorkflowQAResult:
    """
    Complete QA result for an entire workflow run.

    Aggregates all AI call captures and their scores,
    plus optional semantic analysis from QAAuditor.
    """

    run_id: str
    client_name: str

    # Call-level data
    total_calls: int
    calls_passed: int
    calls_failed: int

    # Aggregate scoring
    overall_score: int  # Weighted average of call scores
    passed: bool
    worst_call_id: Optional[str] = None  # Call with lowest score
    worst_severity: Severity = Severity.NONE

    # Semantic analysis (from existing QAAuditor)
    semantic_result: Optional[QAResult] = None

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    total_duration_ms: float = 0.0

    # Token usage
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "run_id": self.run_id,
            "client_name": self.client_name,
            "total_calls": self.total_calls,
            "calls_passed": self.calls_passed,
            "calls_failed": self.calls_failed,
            "overall_score": self.overall_score,
            "passed": self.passed,
            "worst_call_id": self.worst_call_id,
            "worst_severity": self.worst_severity.value,
            "semantic_score": self.semantic_result.score if self.semantic_result else None,
            "timestamp": self.timestamp.isoformat(),
            "total_duration_ms": self.total_duration_ms,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
        }

    def to_sheets_row(self) -> list[Any]:
        """
        Convert to a row for Google Sheets "Workflow QA Summary" sheet.

        Columns: Timestamp, Run ID, Client, Total Calls, Calls Passed,
                 Calls Failed, Overall Score, Passed, Worst Call ID,
                 Worst Severity, Semantic Score, Duration (s), Top Issues
        """
        return [
            self.timestamp.isoformat(),
            self.run_id,
            self.client_name,
            self.total_calls,
            self.calls_passed,
            self.calls_failed,
            self.overall_score,
            "PASS" if self.passed else "FAIL",
            self.worst_call_id or "",
            self.worst_severity.value,
            self.semantic_result.score if self.semantic_result else "",
            round(self.total_duration_ms / 1000, 2),  # Convert to seconds
            "",  # Top issues filled by caller
        ]
