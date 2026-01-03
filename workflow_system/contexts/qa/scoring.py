"""
Scoring and validation pipeline for QA system.

Contains the ValidationPipeline for orchestrating validators,
and scorers for computing aggregate scores from validation results.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

import structlog

from contexts.qa.models import CallScore, Severity
from contexts.qa.validators.base import ValidationResult
from contexts.qa.validators.deterministic import DETERMINISTIC_VALIDATORS

if TYPE_CHECKING:
    from contexts.qa.call_capture import AICallCapture
    from config.dependency_injection import AIProvider

logger = structlog.get_logger()


class ValidationPipeline:
    """
    Orchestrates running all validators on captured AI calls.

    Runs deterministic validators synchronously (fast, no external calls)
    and optionally runs probabilistic validators (require AI calls).
    """

    def __init__(
        self,
        ai_provider: Optional[AIProvider] = None,
        run_probabilistic: bool = True,
        probabilistic_sample_rate: float = 1.0,
    ):
        """
        Initialize the validation pipeline.

        Args:
            ai_provider: AI provider for probabilistic checks (optional)
            run_probabilistic: Whether to run probabilistic validators
            probabilistic_sample_rate: Fraction of calls to run probabilistic checks on (0.0-1.0)
        """
        self._ai = ai_provider
        self._run_probabilistic = run_probabilistic and ai_provider is not None
        self._sample_rate = probabilistic_sample_rate

        # Initialize deterministic validators (always run)
        self._deterministic = [cls() for cls in DETERMINISTIC_VALIDATORS]

        # Probabilistic validators loaded lazily to avoid circular imports
        self._probabilistic: list = []
        self._probabilistic_loaded = False

    def _load_probabilistic_validators(self) -> None:
        """Load probabilistic validators lazily."""
        if self._probabilistic_loaded:
            return

        try:
            from contexts.qa.validators.probabilistic import PROBABILISTIC_VALIDATORS

            self._probabilistic = [cls() for cls in PROBABILISTIC_VALIDATORS]
        except ImportError:
            # Probabilistic validators not yet implemented
            self._probabilistic = []

        self._probabilistic_loaded = True

    async def validate(self, capture: AICallCapture) -> list[ValidationResult]:
        """
        Run all applicable validators on a captured AI call.

        Args:
            capture: The captured AI call to validate

        Returns:
            List of validation results from all validators
        """
        results: list[ValidationResult] = []

        # Always run deterministic checks (fast, no external calls)
        for validator in self._deterministic:
            try:
                result = await validator.validate(capture)
                results.append(result)
            except Exception as e:
                logger.error(
                    "validator_error",
                    validator=validator.name,
                    error=str(e),
                )
                # Add error result instead of crashing
                results.append(
                    ValidationResult.failure(
                        check_name=validator.name,
                        check_type="deterministic",
                        severity=Severity.LOW,
                        failure_type=Severity.NONE,
                        message=f"Validator error: {e}",
                    )
                )

        # Optionally run probabilistic checks
        if self._run_probabilistic and self._should_run_probabilistic():
            self._load_probabilistic_validators()

            for validator in self._probabilistic:
                try:
                    result = await validator.validate(capture, ai_provider=self._ai)
                    results.append(result)
                except Exception as e:
                    logger.error(
                        "probabilistic_validator_error",
                        validator=validator.name,
                        error=str(e),
                    )
                    # Don't add error result for probabilistic - just skip

        return results

    def _should_run_probabilistic(self) -> bool:
        """Decide whether to run probabilistic checks based on sample rate."""
        if self._sample_rate >= 1.0:
            return True
        if self._sample_rate <= 0.0:
            return False
        return random.random() < self._sample_rate


class CallScorer:
    """
    Compute aggregate score for a single AI call.

    Takes validation results and produces a weighted score
    considering the severity and importance of each check.
    """

    # Weight by check importance
    WEIGHTS = {
        "json_validity": 3.0,  # Critical for generate_json
        "truncation_detection": 2.5,  # Important - data loss
        "token_limit_warning": 0.5,  # Minor warning
        "response_empty": 2.0,  # Important - useless response
        "prompt_relevance": 2.0,  # Important for quality
        "hallucination_detection": 2.5,  # Important for accuracy
    }

    # Score deductions by severity
    SEVERITY_DEDUCTIONS = {
        Severity.CRITICAL: 8,
        Severity.HIGH: 5,
        Severity.MEDIUM: 3,
        Severity.LOW: 1,
        Severity.NONE: 0,
    }

    def __init__(self, min_pass_score: int = 7):
        """
        Initialize the call scorer.

        Args:
            min_pass_score: Minimum score to pass (default 7)
        """
        self._min_pass_score = min_pass_score

    def score(self, capture: AICallCapture) -> CallScore:
        """
        Compute score from validation results.

        Args:
            capture: Captured AI call with validation results

        Returns:
            CallScore with aggregate score and details
        """
        if not capture.validation_results:
            # No validation results - assume passed
            return CallScore(
                call_id=capture.call_id,
                overall_score=10,
                passed=True,
                worst_severity=Severity.NONE,
                check_scores={},
                deterministic_passed=True,
                probabilistic_passed=None,
            )

        base_score = 10.0
        worst_severity = Severity.NONE
        check_scores: dict[str, int] = {}
        deterministic_passed = True
        probabilistic_passed = True
        has_probabilistic = False

        # Calculate total weight for normalization
        total_weight = sum(
            self.WEIGHTS.get(r.check_name, 1.0) for r in capture.validation_results
        )

        for result in capture.validation_results:
            # Calculate deduction based on severity
            deduction = self.SEVERITY_DEDUCTIONS[result.severity]
            weight = self.WEIGHTS.get(result.check_name, 1.0)

            # Weighted deduction
            weighted_deduction = (deduction * weight) / max(total_weight, 1.0)
            base_score -= weighted_deduction

            # Track individual check score
            check_score = max(0, 10 - deduction)
            check_scores[result.check_name] = check_score

            # Track worst severity
            if result.severity.base_score < worst_severity.base_score:
                worst_severity = result.severity

            # Track pass/fail by check type
            if not result.passed:
                if result.check_type == "deterministic":
                    deterministic_passed = False
                else:
                    probabilistic_passed = False

            if result.check_type == "probabilistic":
                has_probabilistic = True

        # Clamp score to valid range
        overall_score = max(1, min(10, round(base_score)))

        return CallScore(
            call_id=capture.call_id,
            overall_score=overall_score,
            passed=overall_score >= self._min_pass_score,
            worst_severity=worst_severity,
            check_scores=check_scores,
            deterministic_passed=deterministic_passed,
            probabilistic_passed=probabilistic_passed if has_probabilistic else None,
        )
