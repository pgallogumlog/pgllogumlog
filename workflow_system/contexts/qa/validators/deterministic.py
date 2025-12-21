"""
Deterministic validators for AI call validation.

These validators perform rule-based checks that don't require AI calls.
They run synchronously and have no latency impact.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional

from contexts.qa.models import FailureType, Severity
from contexts.qa.validators.base import BaseValidator, ValidationResult

if TYPE_CHECKING:
    from contexts.qa.call_capture import AICallCapture
    from config.dependency_injection import AIProvider


class JSONValidityValidator(BaseValidator):
    """
    Check if generate_json output is valid JSON.

    Only runs for generate_json calls. Verifies that the response
    can be parsed as valid JSON.
    """

    name = "json_validity"
    check_type = "deterministic"

    async def validate(
        self,
        capture: AICallCapture,
        ai_provider: Optional[AIProvider] = None,
    ) -> ValidationResult:
        # Skip if not a JSON call
        if not capture.is_json_call:
            return self._skipped("Not a generate_json call")

        # If parsed_json exists, it was already successfully parsed
        if capture.parsed_json is not None:
            return self._success("Valid JSON parsed successfully")

        # Try to parse the response ourselves
        try:
            json.loads(capture.response_text.strip())
            return self._success("Valid JSON in response")
        except json.JSONDecodeError as e:
            # Try extracting from markdown code block
            import re

            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", capture.response_text)
            if json_match:
                try:
                    json.loads(json_match.group(1).strip())
                    return self._warning(
                        message="JSON wrapped in markdown code block",
                        severity=Severity.LOW,
                        recommended_fix="Add 'No markdown formatting' to system prompt",
                    )
                except json.JSONDecodeError:
                    pass

            # Try finding bare JSON object
            json_obj_match = re.search(r"\{[\s\S]*\}", capture.response_text)
            if json_obj_match:
                try:
                    json.loads(json_obj_match.group(0))
                    return self._warning(
                        message="JSON has extra text around it",
                        severity=Severity.LOW,
                        recommended_fix="Add 'Respond with JSON only, no explanation' to system prompt",
                    )
                except json.JSONDecodeError:
                    pass

            # Complete JSON parse failure
            return self._failure(
                severity=Severity.HIGH,
                failure_type=FailureType.FORMAT_VIOLATION,
                message=f"Invalid JSON at position {e.pos}: {e.msg}",
                recommended_fix="Add to system prompt: 'Respond with valid JSON only. No markdown, no explanation.'",
                details={
                    "error_position": e.pos,
                    "error_message": e.msg,
                    "response_preview": capture.response_text[:200],
                },
            )


class TruncationDetector(BaseValidator):
    """
    Detect if response was truncated due to max_tokens.

    Checks the stop_reason from the API response. A stop_reason of
    "max_tokens" indicates the response was cut off.
    """

    name = "truncation_detection"
    check_type = "deterministic"

    async def validate(
        self,
        capture: AICallCapture,
        ai_provider: Optional[AIProvider] = None,
    ) -> ValidationResult:
        if capture.stop_reason == "max_tokens":
            # Calculate suggested new limit
            suggested_limit = int(capture.max_tokens * 1.5)

            return self._failure(
                severity=Severity.MEDIUM,
                failure_type=FailureType.TRUNCATION,
                message=f"Response truncated at {capture.output_tokens} tokens (limit: {capture.max_tokens})",
                recommended_fix=f"Increase max_tokens from {capture.max_tokens} to {suggested_limit}",
                details={
                    "output_tokens": capture.output_tokens,
                    "max_tokens": capture.max_tokens,
                    "stop_reason": capture.stop_reason,
                    "suggested_limit": suggested_limit,
                },
            )

        if capture.stop_reason == "stop_sequence":
            # This is fine - intentional stop
            return self._success("Response ended at stop sequence")

        if capture.stop_reason == "end_turn":
            return self._success("Response completed normally")

        # Unknown stop reason - warn but don't fail
        return self._warning(
            message=f"Unknown stop_reason: {capture.stop_reason}",
            severity=Severity.LOW,
            details={"stop_reason": capture.stop_reason},
        )


class TokenLimitWarning(BaseValidator):
    """
    Warn when output tokens approach max_tokens limit.

    This is a proactive warning - the response wasn't truncated,
    but it came close. Useful for identifying prompts that may
    need higher limits.
    """

    name = "token_limit_warning"
    check_type = "deterministic"

    # Warn at 85% usage
    WARNING_THRESHOLD = 0.85
    # Critical warning at 95% usage
    CRITICAL_THRESHOLD = 0.95

    async def validate(
        self,
        capture: AICallCapture,
        ai_provider: Optional[AIProvider] = None,
    ) -> ValidationResult:
        # Skip if already truncated (handled by TruncationDetector)
        if capture.was_truncated:
            return self._skipped("Already truncated - see truncation_detection")

        ratio = capture.token_usage_ratio

        if ratio >= self.CRITICAL_THRESHOLD:
            return self._warning(
                message=f"Token usage at {ratio:.0%} of limit - very close to truncation",
                severity=Severity.MEDIUM,
                recommended_fix=f"Increase max_tokens from {capture.max_tokens} to {int(capture.max_tokens * 1.3)}",
                details={
                    "usage_ratio": round(ratio, 3),
                    "output_tokens": capture.output_tokens,
                    "max_tokens": capture.max_tokens,
                },
            )

        if ratio >= self.WARNING_THRESHOLD:
            return self._warning(
                message=f"Token usage at {ratio:.0%} of limit",
                severity=Severity.LOW,
                recommended_fix="Consider increasing max_tokens buffer by 20%",
                details={
                    "usage_ratio": round(ratio, 3),
                    "output_tokens": capture.output_tokens,
                    "max_tokens": capture.max_tokens,
                },
            )

        return self._success(f"Token usage at {ratio:.0%} - within safe limits")


class ResponseEmptyValidator(BaseValidator):
    """
    Check if the response is empty or nearly empty.

    An empty response usually indicates a problem with the prompt
    or a misunderstanding by the model.
    """

    name = "response_empty"
    check_type = "deterministic"

    # Minimum expected response length (characters)
    MIN_LENGTH = 10

    async def validate(
        self,
        capture: AICallCapture,
        ai_provider: Optional[AIProvider] = None,
    ) -> ValidationResult:
        response_length = len(capture.response_text.strip())

        if response_length == 0:
            return self._failure(
                severity=Severity.HIGH,
                failure_type=FailureType.VALIDATION_ERROR,
                message="Response is empty",
                recommended_fix="Check prompt clarity and ensure system prompt provides clear instructions",
                details={"response_length": 0},
            )

        if response_length < self.MIN_LENGTH:
            return self._warning(
                message=f"Response is very short ({response_length} chars)",
                severity=Severity.LOW,
                recommended_fix="Ensure prompt asks for sufficient detail",
                details={"response_length": response_length},
            )

        return self._success(f"Response length OK ({response_length} chars)")


# Export all deterministic validators
DETERMINISTIC_VALIDATORS = [
    JSONValidityValidator,
    TruncationDetector,
    TokenLimitWarning,
    ResponseEmptyValidator,
]
