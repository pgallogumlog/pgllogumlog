"""
Base classes and protocols for QA validators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

from contexts.qa.models import FailureType, Severity

if TYPE_CHECKING:
    from contexts.qa.call_capture import AICallCapture
    from config.dependency_injection import AIProvider


@dataclass
class ValidationResult:
    """
    Result from a single validation check.

    Each validator produces one ValidationResult indicating whether
    the check passed, the severity if it failed, and recommendations.
    """

    check_name: str  # e.g., "json_validity", "truncation_detection"
    check_type: str  # "deterministic" | "probabilistic"
    passed: bool
    severity: Severity
    failure_type: FailureType
    message: str  # Human-readable explanation
    details: dict[str, Any] = field(default_factory=dict)  # Check-specific data
    recommended_fix: Optional[str] = None

    @classmethod
    def success(
        cls,
        check_name: str,
        check_type: str,
        message: str = "Check passed",
    ) -> ValidationResult:
        """Create a successful validation result."""
        return cls(
            check_name=check_name,
            check_type=check_type,
            passed=True,
            severity=Severity.NONE,
            failure_type=FailureType.NONE,
            message=message,
        )

    @classmethod
    def failure(
        cls,
        check_name: str,
        check_type: str,
        severity: Severity,
        failure_type: FailureType,
        message: str,
        recommended_fix: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> ValidationResult:
        """Create a failed validation result."""
        return cls(
            check_name=check_name,
            check_type=check_type,
            passed=False,
            severity=severity,
            failure_type=failure_type,
            message=message,
            recommended_fix=recommended_fix,
            details=details or {},
        )

    @classmethod
    def warning(
        cls,
        check_name: str,
        check_type: str,
        message: str,
        severity: Severity = Severity.LOW,
        recommended_fix: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> ValidationResult:
        """Create a warning (passes but with low severity)."""
        return cls(
            check_name=check_name,
            check_type=check_type,
            passed=True,  # Warnings still pass
            severity=severity,
            failure_type=FailureType.NONE,
            message=message,
            recommended_fix=recommended_fix,
            details=details or {},
        )

    @classmethod
    def skipped(
        cls,
        check_name: str,
        check_type: str,
        reason: str,
    ) -> ValidationResult:
        """Create a skipped validation result (not applicable)."""
        return cls(
            check_name=check_name,
            check_type=check_type,
            passed=True,
            severity=Severity.NONE,
            failure_type=FailureType.NONE,
            message=f"Skipped: {reason}",
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "check_name": self.check_name,
            "check_type": self.check_type,
            "passed": self.passed,
            "severity": self.severity.value,
            "failure_type": self.failure_type.value,
            "message": self.message,
            "details": self.details,
            "recommended_fix": self.recommended_fix,
        }


@runtime_checkable
class Validator(Protocol):
    """
    Protocol for validation checks.

    All validators must implement this interface. Deterministic validators
    don't need an AI provider, while probabilistic validators do.
    """

    name: str
    check_type: str  # "deterministic" | "probabilistic"

    async def validate(
        self,
        capture: AICallCapture,
        ai_provider: Optional[AIProvider] = None,
    ) -> ValidationResult:
        """
        Run validation check on a captured AI call.

        Args:
            capture: The captured AI call to validate
            ai_provider: Optional AI provider for probabilistic checks

        Returns:
            ValidationResult indicating pass/fail and details
        """
        ...


class BaseValidator:
    """
    Base class for validators with common functionality.

    Provides default implementations and helper methods.
    """

    name: str = "base"
    check_type: str = "deterministic"

    async def validate(
        self,
        capture: AICallCapture,
        ai_provider: Optional[AIProvider] = None,
    ) -> ValidationResult:
        """Override in subclasses."""
        raise NotImplementedError("Subclasses must implement validate()")

    def _success(self, message: str = "Check passed") -> ValidationResult:
        """Create a success result for this validator."""
        return ValidationResult.success(
            check_name=self.name,
            check_type=self.check_type,
            message=message,
        )

    def _failure(
        self,
        severity: Severity,
        failure_type: FailureType,
        message: str,
        recommended_fix: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> ValidationResult:
        """Create a failure result for this validator."""
        return ValidationResult.failure(
            check_name=self.name,
            check_type=self.check_type,
            severity=severity,
            failure_type=failure_type,
            message=message,
            recommended_fix=recommended_fix,
            details=details,
        )

    def _warning(
        self,
        message: str,
        severity: Severity = Severity.LOW,
        recommended_fix: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> ValidationResult:
        """Create a warning result for this validator."""
        return ValidationResult.warning(
            check_name=self.name,
            check_type=self.check_type,
            message=message,
            severity=severity,
            recommended_fix=recommended_fix,
            details=details,
        )

    def _skipped(self, reason: str) -> ValidationResult:
        """Create a skipped result for this validator."""
        return ValidationResult.skipped(
            check_name=self.name,
            check_type=self.check_type,
            reason=reason,
        )
