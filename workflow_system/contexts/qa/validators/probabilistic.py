"""
Probabilistic validators for AI call validation.

These validators use AI to analyze responses for quality issues
that cannot be detected deterministically.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import structlog

from contexts.qa.models import FailureType, Severity
from contexts.qa.validators.base import BaseValidator, ValidationResult

if TYPE_CHECKING:
    from contexts.qa.call_capture import AICallCapture
    from config.dependency_injection import AIProvider

logger = structlog.get_logger()


# System prompt for relevance checking
RELEVANCE_CHECK_SYSTEM = """You are a QA validator checking if an AI response appropriately addresses its prompt.

Analyze the given prompt and response, then evaluate:
1. Does the response directly address what the prompt asked for?
2. Is the response on-topic and relevant?
3. Did the response follow any system instructions provided?

Respond with valid JSON only:
{
    "relevant": true/false,
    "score": 1-10,
    "issues": ["list of specific relevance issues if any"],
    "explanation": "brief explanation of your assessment"
}"""


# System prompt for hallucination detection
HALLUCINATION_CHECK_SYSTEM = """You are a QA validator checking for hallucinations in an AI response.

A hallucination is when the AI generates information that:
1. Is not supported by the provided context/prompt
2. Makes up facts, names, dates, or statistics
3. Claims something that goes beyond what was asked or provided

Analyze the prompt context and response for any ungrounded claims.

Respond with valid JSON only:
{
    "grounded": true/false,
    "hallucinations": ["list of specific ungrounded claims found"],
    "confidence": 0.0-1.0,
    "explanation": "brief explanation of findings"
}"""


class PromptRelevanceValidator(BaseValidator):
    """
    Check if the AI response appropriately addresses the input prompt.

    Uses AI to analyze whether the response is on-topic, follows
    instructions, and directly addresses what was asked.
    """

    name = "prompt_relevance"
    check_type = "probabilistic"

    # Truncation limits to keep validation fast
    MAX_PROMPT_LENGTH = 2000
    MAX_RESPONSE_LENGTH = 2000

    async def validate(
        self,
        capture: AICallCapture,
        ai_provider: Optional[AIProvider] = None,
    ) -> ValidationResult:
        if ai_provider is None:
            return self._skipped("No AI provider for probabilistic check")

        # Build the analysis prompt
        analysis_prompt = self._build_analysis_prompt(capture)

        try:
            result = await ai_provider.generate_json(
                prompt=analysis_prompt,
                system_prompt=RELEVANCE_CHECK_SYSTEM,
                temperature=0.0,
                max_tokens=500,
            )

            # Parse result
            is_relevant = result.get("relevant", True)
            score = result.get("score", 10)
            issues = result.get("issues", [])
            explanation = result.get("explanation", "")

            if not is_relevant or score < 6:
                return self._failure(
                    severity=Severity.HIGH if score < 4 else Severity.MEDIUM,
                    failure_type=FailureType.LOGIC_ERROR,
                    message=explanation or "Response not relevant to prompt",
                    recommended_fix="Refine system prompt to be more specific about expected output format and content",
                    details={
                        "relevance_score": score,
                        "issues": issues,
                    },
                )

            if score < 8:
                return self._warning(
                    message=f"Partial relevance (score: {score}/10): {explanation}",
                    severity=Severity.LOW,
                    details={
                        "relevance_score": score,
                        "issues": issues,
                    },
                )

            return self._success(f"Response is relevant (score: {score}/10)")

        except Exception as e:
            logger.warning(
                "relevance_check_failed",
                error=str(e),
                call_id=capture.call_id,
            )
            return self._skipped(f"Relevance check failed: {e}")

    def _build_analysis_prompt(self, capture: AICallCapture) -> str:
        """Build the prompt for relevance analysis."""
        prompt_preview = capture.prompt[:self.MAX_PROMPT_LENGTH]
        if len(capture.prompt) > self.MAX_PROMPT_LENGTH:
            prompt_preview += "... [truncated]"

        response_preview = capture.response_text[:self.MAX_RESPONSE_LENGTH]
        if len(capture.response_text) > self.MAX_RESPONSE_LENGTH:
            response_preview += "... [truncated]"

        system_info = ""
        if capture.system_prompt:
            system_preview = capture.system_prompt[:1000]
            if len(capture.system_prompt) > 1000:
                system_preview += "... [truncated]"
            system_info = f"\n\nSYSTEM INSTRUCTIONS:\n{system_preview}"

        return f"""Analyze if this AI response appropriately addresses the given prompt.

PROMPT:
{prompt_preview}
{system_info}

RESPONSE:
{response_preview}

Evaluate relevance and provide your assessment as JSON."""


class HallucinationDetector(BaseValidator):
    """
    Detect if the AI response contains hallucinated information.

    Uses AI to check whether claims in the response are grounded
    in the provided context or are fabricated.
    """

    name = "hallucination_detection"
    check_type = "probabilistic"

    # Truncation limits
    MAX_CONTEXT_LENGTH = 3000
    MAX_RESPONSE_LENGTH = 2000

    async def validate(
        self,
        capture: AICallCapture,
        ai_provider: Optional[AIProvider] = None,
    ) -> ValidationResult:
        if ai_provider is None:
            return self._skipped("No AI provider for probabilistic check")

        # Build the analysis prompt
        analysis_prompt = self._build_analysis_prompt(capture)

        try:
            result = await ai_provider.generate_json(
                prompt=analysis_prompt,
                system_prompt=HALLUCINATION_CHECK_SYSTEM,
                temperature=0.0,
                max_tokens=500,
            )

            # Parse result
            is_grounded = result.get("grounded", True)
            hallucinations = result.get("hallucinations", [])
            confidence = result.get("confidence", 1.0)
            explanation = result.get("explanation", "")

            if not is_grounded and hallucinations:
                # Severity depends on number and nature of hallucinations
                severity = Severity.HIGH if len(hallucinations) > 2 else Severity.MEDIUM

                return self._failure(
                    severity=severity,
                    failure_type=FailureType.HALLUCINATION,
                    message=f"Found {len(hallucinations)} ungrounded claim(s)",
                    recommended_fix="Add 'Only use information explicitly provided in the context' to system prompt",
                    details={
                        "hallucinations": hallucinations[:5],  # Limit to 5
                        "confidence": confidence,
                        "explanation": explanation,
                    },
                )

            if confidence < 0.8:
                return self._warning(
                    message=f"Low confidence in grounding check ({confidence:.0%})",
                    severity=Severity.LOW,
                    details={
                        "confidence": confidence,
                        "explanation": explanation,
                    },
                )

            return self._success("Response appears grounded in provided context")

        except Exception as e:
            logger.warning(
                "hallucination_check_failed",
                error=str(e),
                call_id=capture.call_id,
            )
            return self._skipped(f"Hallucination check failed: {e}")

    def _build_analysis_prompt(self, capture: AICallCapture) -> str:
        """Build the prompt for hallucination detection."""
        # Combine prompt and system prompt as context
        context_parts = []

        if capture.system_prompt:
            system_preview = capture.system_prompt[:1000]
            context_parts.append(f"System instructions: {system_preview}")

        prompt_preview = capture.prompt[:self.MAX_CONTEXT_LENGTH - len("".join(context_parts))]
        context_parts.append(f"User prompt: {prompt_preview}")

        context = "\n\n".join(context_parts)

        response_preview = capture.response_text[:self.MAX_RESPONSE_LENGTH]
        if len(capture.response_text) > self.MAX_RESPONSE_LENGTH:
            response_preview += "... [truncated]"

        return f"""Check if this AI response contains any hallucinated or ungrounded information.

PROVIDED CONTEXT:
{context}

AI RESPONSE:
{response_preview}

Analyze for hallucinations and provide your assessment as JSON."""


# Export all probabilistic validators
PROBABILISTIC_VALIDATORS = [
    PromptRelevanceValidator,
    HallucinationDetector,
]
