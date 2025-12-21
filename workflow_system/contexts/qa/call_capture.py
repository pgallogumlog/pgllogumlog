"""
AI Call Capture models for QA system.
Captures complete context for every AI call including inputs, outputs, and metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from contexts.qa.validators.base import ValidationResult
    from contexts.qa.scoring import CallScore


@dataclass
class AICallCapture:
    """
    Captures complete context for a single AI call.

    Used by CapturingAIAdapter to record all inputs, outputs, and metadata
    for every AI call made during a workflow run.
    """

    # Identity
    call_id: str  # Unique ID for this call (e.g., "abc123-001")
    run_id: str  # Parent workflow run ID
    sequence_number: int  # Order within workflow (1, 2, 3...)
    method: str  # "generate" | "generate_json" | "generate_parallel"
    caller_context: str  # e.g., "WorkflowEngine._rewrite_input"

    # Inputs
    prompt: str
    system_prompt: Optional[str]
    temperature: float
    max_tokens: int
    model: str

    # Outputs
    response_text: str
    parsed_json: Optional[dict[str, Any]] = None  # For generate_json calls

    # API Response Metadata
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = "unknown"  # "end_turn", "max_tokens", "stop_sequence"

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0

    # Validation Results (filled after validation runs)
    validation_results: list[ValidationResult] = field(default_factory=list)
    call_score: Optional[CallScore] = None

    @property
    def was_truncated(self) -> bool:
        """Check if response was truncated due to max_tokens."""
        return self.stop_reason == "max_tokens"

    @property
    def token_usage_ratio(self) -> float:
        """Ratio of output tokens to max tokens (0.0 to 1.0+)."""
        if self.max_tokens == 0:
            return 0.0
        return self.output_tokens / self.max_tokens

    @property
    def is_json_call(self) -> bool:
        """Check if this was a generate_json call."""
        return self.method == "generate_json"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "call_id": self.call_id,
            "run_id": self.run_id,
            "sequence_number": self.sequence_number,
            "method": self.method,
            "caller_context": self.caller_context,
            "prompt_length": len(self.prompt),
            "system_prompt_length": len(self.system_prompt) if self.system_prompt else 0,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "model": self.model,
            "response_length": len(self.response_text),
            "has_parsed_json": self.parsed_json is not None,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "stop_reason": self.stop_reason,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "was_truncated": self.was_truncated,
            "token_usage_ratio": round(self.token_usage_ratio, 3),
            "validation_count": len(self.validation_results),
            "call_score": self.call_score.overall_score if self.call_score else None,
        }

    def to_sheets_row(self) -> list[Any]:
        """
        Convert to a row for Google Sheets "AI Call Log" sheet.

        Columns: Timestamp, Run ID, Call ID, Sequence, Method, Caller,
                 Model, Temperature, Max Tokens, Input Tokens, Output Tokens,
                 Stop Reason, Duration, Call Score, Passed, Worst Severity,
                 Failed Checks, Recommended Fixes, Prompt Preview, Response Preview
        """
        # Get failed checks and fixes
        failed_checks = []
        fixes = []
        worst_severity = "none"

        for result in self.validation_results:
            if not result.passed:
                failed_checks.append(result.check_name)
                if result.recommended_fix:
                    fixes.append(result.recommended_fix)
                # Track worst severity
                if result.severity.value != "none":
                    worst_severity = result.severity.value

        return [
            self.timestamp.isoformat(),
            self.run_id,
            self.call_id,
            self.sequence_number,
            self.method,
            self.caller_context,
            self.model,
            self.temperature,
            self.max_tokens,
            self.input_tokens,
            self.output_tokens,
            self.stop_reason,
            round(self.duration_ms, 1),
            self.call_score.overall_score if self.call_score else "",
            "PASS" if self.call_score and self.call_score.passed else "FAIL",
            worst_severity,
            ", ".join(failed_checks),
            "; ".join(fixes[:3]),  # Limit to 3 fixes
            self.prompt[:200],
            self.response_text[:200],
        ]


@dataclass
class AICallStore:
    """
    Stores captured AI calls for a workflow run.

    Provides methods for adding, retrieving, and analyzing captured calls.
    """

    run_id: str
    calls: list[AICallCapture] = field(default_factory=list)
    _sequence_counter: int = field(default=0, repr=False)

    def add(self, capture: AICallCapture) -> None:
        """Add a captured call to the store."""
        self.calls.append(capture)

    def next_sequence(self) -> int:
        """Get next sequence number for a new call."""
        self._sequence_counter += 1
        return self._sequence_counter

    def get_by_id(self, call_id: str) -> Optional[AICallCapture]:
        """Get a specific call by ID."""
        for call in self.calls:
            if call.call_id == call_id:
                return call
        return None

    def get_failed_calls(self) -> list[AICallCapture]:
        """Get all calls that failed validation."""
        return [c for c in self.calls if c.call_score and not c.call_score.passed]

    def get_by_method(self, method: str) -> list[AICallCapture]:
        """Get all calls of a specific method type."""
        return [c for c in self.calls if c.method == method]

    @property
    def total_calls(self) -> int:
        """Total number of captured calls."""
        return len(self.calls)

    @property
    def total_tokens(self) -> tuple[int, int]:
        """Total input and output tokens across all calls."""
        input_total = sum(c.input_tokens for c in self.calls)
        output_total = sum(c.output_tokens for c in self.calls)
        return input_total, output_total

    @property
    def total_duration_ms(self) -> float:
        """Total duration across all calls in milliseconds."""
        return sum(c.duration_ms for c in self.calls)

    def summary(self) -> dict[str, Any]:
        """Get summary statistics for all captured calls."""
        input_tokens, output_tokens = self.total_tokens

        passed = sum(1 for c in self.calls if c.call_score and c.call_score.passed)
        failed = sum(1 for c in self.calls if c.call_score and not c.call_score.passed)

        return {
            "run_id": self.run_id,
            "total_calls": self.total_calls,
            "calls_passed": passed,
            "calls_failed": failed,
            "total_input_tokens": input_tokens,
            "total_output_tokens": output_tokens,
            "total_duration_ms": round(self.total_duration_ms, 1),
            "methods": {
                "generate": len(self.get_by_method("generate")),
                "generate_json": len(self.get_by_method("generate_json")),
                "generate_parallel": len(self.get_by_method("generate_parallel")),
            },
        }
