"""
Capturing AI Adapter for QA system.

Wraps an AIProvider to capture all AI calls for validation and logging.
Uses decorator pattern to intercept calls without modifying ClaudeAdapter.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

import structlog

from contexts.qa.call_capture import AICallCapture, AICallStore
from contexts.qa.scoring import CallScorer, ValidationPipeline

if TYPE_CHECKING:
    from config.dependency_injection import AIProvider

logger = structlog.get_logger()


class CapturingAIAdapter:
    """
    Wrapper around AIProvider that captures all calls for QA.

    Uses decorator pattern to intercept calls without modifying the
    underlying adapter. Captures inputs, outputs, metadata, and runs
    validation pipeline on each call.
    """

    def __init__(
        self,
        wrapped: AIProvider,
        run_id: str,
        validation_pipeline: Optional[ValidationPipeline] = None,
        enable_capture: bool = True,
        min_pass_score: int = 7,
    ):
        """
        Initialize the capturing adapter.

        Args:
            wrapped: The underlying AI provider to wrap
            run_id: Unique identifier for this workflow run
            validation_pipeline: Pipeline for running validators (optional)
            enable_capture: Whether to capture calls (can be disabled for performance)
            min_pass_score: Minimum score to pass validation
        """
        self._wrapped = wrapped
        self._run_id = run_id
        self._pipeline = validation_pipeline
        self._enabled = enable_capture
        self._scorer = CallScorer(min_pass_score)

        # Call storage
        self._store = AICallStore(run_id=run_id)

        # Context tracking for caller identification
        self._caller_stack: list[str] = []

    @property
    def call_store(self) -> AICallStore:
        """Get the call store with all captured calls."""
        return self._store

    @property
    def captured_calls(self) -> list[AICallCapture]:
        """Get list of all captured calls."""
        return self._store.calls

    def push_context(self, context: str) -> None:
        """
        Push caller context onto stack.

        Use this to identify which component made an AI call.
        Example: push_context("WorkflowEngine._rewrite_input")
        """
        self._caller_stack.append(context)

    def pop_context(self) -> Optional[str]:
        """Pop caller context from stack."""
        if self._caller_stack:
            return self._caller_stack.pop()
        return None

    @property
    def current_context(self) -> str:
        """Get current caller context."""
        return self._caller_stack[-1] if self._caller_stack else "unknown"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ) -> str:
        """Generate a text response, capturing the call for QA."""
        if not self._enabled:
            return await self._wrapped.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
            )

        start_time = datetime.now()

        # Call with metadata to get full response info
        response, metadata = await self._wrapped.generate_with_metadata(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Create capture record
        capture = await self._create_capture(
            method="generate",
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model or metadata.get("model", "unknown"),
            response_text=response,
            parsed_json=None,
            metadata=metadata,
            start_time=start_time,
            duration_ms=duration_ms,
        )

        self._store.add(capture)

        logger.debug(
            "ai_call_captured",
            call_id=capture.call_id,
            method="generate",
            score=capture.call_score.overall_score if capture.call_score else None,
        )

        return response

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ) -> dict:
        """Generate a JSON response, capturing the call for QA."""
        if not self._enabled:
            return await self._wrapped.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
            )

        start_time = datetime.now()

        # Call with metadata to get full response info
        parsed, metadata = await self._wrapped.generate_json_with_metadata(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Get raw response from metadata
        raw_response = metadata.pop("raw_response", "")

        # Create capture record
        capture = await self._create_capture(
            method="generate_json",
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model or metadata.get("model", "unknown"),
            response_text=raw_response,
            parsed_json=parsed,
            metadata=metadata,
            start_time=start_time,
            duration_ms=duration_ms,
        )

        self._store.add(capture)

        logger.debug(
            "ai_call_captured",
            call_id=capture.call_id,
            method="generate_json",
            score=capture.call_score.overall_score if capture.call_score else None,
        )

        return parsed

    async def generate_parallel(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperatures: Optional[list[float]] = None,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ) -> list[str]:
        """Generate parallel responses, capturing each call for QA."""
        if not self._enabled:
            return await self._wrapped.generate_parallel(
                prompt=prompt,
                system_prompt=system_prompt,
                temperatures=temperatures,
                max_tokens=max_tokens,
                model=model,
            )

        start_time = datetime.now()
        temps = temperatures or [0.3, 0.5, 0.7, 0.85, 1.0]

        # Call with metadata
        results_with_metadata = await self._wrapped.generate_parallel_with_metadata(
            prompt=prompt,
            system_prompt=system_prompt,
            temperatures=temperatures,
            max_tokens=max_tokens,
            model=model,
        )

        total_duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Create capture records for each response
        responses = []
        for i, (response, metadata) in enumerate(results_with_metadata):
            # Estimate per-call duration (divide total by number of calls)
            per_call_duration = total_duration_ms / len(results_with_metadata)

            capture = await self._create_capture(
                method="generate_parallel",
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temps[i] if i < len(temps) else 0.7,
                max_tokens=max_tokens,
                model=model or metadata.get("model", "unknown"),
                response_text=response,
                parsed_json=None,
                metadata=metadata,
                start_time=start_time,
                duration_ms=per_call_duration,
            )

            self._store.add(capture)
            responses.append(response)

        logger.debug(
            "parallel_calls_captured",
            count=len(results_with_metadata),
            run_id=self._run_id,
        )

        return responses

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ) -> tuple[str, dict[str, Any]]:
        """Generate with metadata, capturing the call for QA."""
        if not self._enabled:
            return await self._wrapped.generate_with_metadata(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
            )

        start_time = datetime.now()

        response, metadata = await self._wrapped.generate_with_metadata(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        capture = await self._create_capture(
            method="generate",
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model or metadata.get("model", "unknown"),
            response_text=response,
            parsed_json=None,
            metadata=metadata,
            start_time=start_time,
            duration_ms=duration_ms,
        )

        self._store.add(capture)

        return response, metadata

    async def generate_json_with_metadata(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ) -> tuple[dict, dict[str, Any]]:
        """Generate JSON with metadata, capturing the call for QA."""
        if not self._enabled:
            return await self._wrapped.generate_json_with_metadata(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
            )

        start_time = datetime.now()

        parsed, metadata = await self._wrapped.generate_json_with_metadata(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        raw_response = metadata.pop("raw_response", "")

        capture = await self._create_capture(
            method="generate_json",
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model or metadata.get("model", "unknown"),
            response_text=raw_response,
            parsed_json=parsed,
            metadata=metadata,
            start_time=start_time,
            duration_ms=duration_ms,
        )

        self._store.add(capture)

        # Re-add raw_response for caller
        metadata["raw_response"] = raw_response

        return parsed, metadata

    async def generate_parallel_with_metadata(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperatures: Optional[list[float]] = None,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ) -> list[tuple[str, dict[str, Any]]]:
        """Generate parallel with metadata, capturing each call for QA."""
        if not self._enabled:
            return await self._wrapped.generate_parallel_with_metadata(
                prompt=prompt,
                system_prompt=system_prompt,
                temperatures=temperatures,
                max_tokens=max_tokens,
                model=model,
            )

        start_time = datetime.now()
        temps = temperatures or [0.3, 0.5, 0.7, 0.85, 1.0]

        results = await self._wrapped.generate_parallel_with_metadata(
            prompt=prompt,
            system_prompt=system_prompt,
            temperatures=temperatures,
            max_tokens=max_tokens,
            model=model,
        )

        total_duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        for i, (response, metadata) in enumerate(results):
            per_call_duration = total_duration_ms / len(results)

            capture = await self._create_capture(
                method="generate_parallel",
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temps[i] if i < len(temps) else 0.7,
                max_tokens=max_tokens,
                model=model or metadata.get("model", "unknown"),
                response_text=response,
                parsed_json=None,
                metadata=metadata,
                start_time=start_time,
                duration_ms=per_call_duration,
            )

            self._store.add(capture)

        return results

    async def _create_capture(
        self,
        method: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        model: str,
        response_text: str,
        parsed_json: Optional[dict],
        metadata: dict[str, Any],
        start_time: datetime,
        duration_ms: float,
    ) -> AICallCapture:
        """Create an AICallCapture and optionally run validation."""
        sequence = self._store.next_sequence()
        call_id = f"{self._run_id}-{sequence:03d}"

        capture = AICallCapture(
            call_id=call_id,
            run_id=self._run_id,
            sequence_number=sequence,
            method=method,
            caller_context=self.current_context,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            response_text=response_text,
            parsed_json=parsed_json,
            input_tokens=metadata.get("input_tokens", 0),
            output_tokens=metadata.get("output_tokens", 0),
            stop_reason=metadata.get("stop_reason", "unknown"),
            timestamp=start_time,
            duration_ms=duration_ms,
        )

        # Run validation pipeline if available
        if self._pipeline:
            capture.validation_results = await self._pipeline.validate(capture)
            capture.call_score = self._scorer.score(capture)

        return capture
