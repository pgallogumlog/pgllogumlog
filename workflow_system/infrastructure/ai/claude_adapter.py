"""
Claude AI Provider Adapter.
Implements the AIProvider interface for Anthropic's Claude API.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import anthropic
import structlog

logger = structlog.get_logger()

# Rate limiting configuration
MAX_RETRIES = 5
BASE_DELAY = 2.0  # seconds
MAX_DELAY = 60.0  # seconds
PARALLEL_STAGGER_DELAY = 0.5  # seconds between parallel requests


class ClaudeAdapter:
    """
    Adapter for Anthropic Claude API.

    Implements the AIProvider protocol for dependency injection.
    Includes rate limiting with exponential backoff.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "claude-sonnet-4-20250514",
    ):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._default_model = default_model

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> str:
        """
        Generate a text response from Claude with retry logic.

        Args:
            prompt: The user message/prompt
            system_prompt: Optional system instructions
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum response length
            model: Model to use (defaults to instance default)

        Returns:
            The generated text response
        """
        content, _ = await self.generate_with_metadata(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )
        return content

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Generate a text response from Claude with full response metadata.

        This method exposes the complete API response metadata including
        token usage and stop reason, enabling QA validation of responses.

        Args:
            prompt: The user message/prompt
            system_prompt: Optional system instructions
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum response length
            model: Model to use (defaults to instance default)

        Returns:
            Tuple of (response_text, metadata_dict)
            metadata includes: input_tokens, output_tokens, stop_reason, model
        """
        # Clamp temperature to valid range
        temperature = max(0.0, min(1.0, temperature))

        use_model = model or self._default_model

        kwargs: dict[str, Any] = {
            "model": use_model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

        # Only add temperature if not using extended thinking
        if temperature > 0:
            kwargs["temperature"] = temperature

        if system_prompt:
            kwargs["system"] = system_prompt

        logger.debug(
            "claude_generate_request",
            model=use_model,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_length=len(prompt),
        )

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = await self._client.messages.create(**kwargs)

                # Safely extract content - handle empty responses
                if not response.content:
                    logger.warning(
                        "claude_empty_response",
                        model=use_model,
                        stop_reason=response.stop_reason,
                    )
                    content = ""
                else:
                    # Find first text block (response may have multiple content types)
                    content = ""
                    for block in response.content:
                        if hasattr(block, "text"):
                            content = block.text
                            break
                    if not content:
                        logger.warning(
                            "claude_no_text_content",
                            model=use_model,
                            content_types=[type(b).__name__ for b in response.content],
                        )

                metadata = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "stop_reason": response.stop_reason,
                    "model": response.model,
                }

                logger.debug(
                    "claude_generate_response",
                    response_length=len(content),
                    stop_reason=response.stop_reason,
                    usage_input=response.usage.input_tokens,
                    usage_output=response.usage.output_tokens,
                )

                return content, metadata

            except anthropic.RateLimitError as e:
                last_error = e
                delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                logger.warning(
                    "claude_rate_limited",
                    attempt=attempt + 1,
                    max_retries=MAX_RETRIES,
                    delay_seconds=delay,
                )
                await asyncio.sleep(delay)

            except anthropic.APIError as e:
                # Don't retry other API errors
                logger.error("claude_api_error", error=str(e))
                raise

        # All retries exhausted
        logger.error(
            "claude_rate_limit_exhausted",
            max_retries=MAX_RETRIES,
            error=str(last_error),
        )
        raise last_error

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> dict:
        """
        Generate a JSON response from Claude.

        Automatically parses the response and handles JSON extraction
        from markdown code blocks.

        Args:
            prompt: The user message/prompt
            system_prompt: Optional system instructions (should request JSON)
            temperature: Creativity level (lower is more deterministic)
            max_tokens: Maximum response length
            model: Model to use

        Returns:
            Parsed JSON as a dictionary
        """
        parsed, _ = await self.generate_json_with_metadata(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )
        return parsed

    async def generate_json_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> tuple[dict, dict[str, Any]]:
        """
        Generate a JSON response from Claude with full response metadata.

        Args:
            prompt: The user message/prompt
            system_prompt: Optional system instructions (should request JSON)
            temperature: Creativity level (lower is more deterministic)
            max_tokens: Maximum response length
            model: Model to use

        Returns:
            Tuple of (parsed_json, metadata_dict)
            metadata includes: input_tokens, output_tokens, stop_reason, model, raw_response
        """
        # Enhance system prompt to request JSON
        json_system = system_prompt or ""
        if "json" not in json_system.lower():
            json_system += "\n\nRespond with valid JSON only. No markdown, no explanation."

        response, metadata = await self.generate_with_metadata(
            prompt=prompt,
            system_prompt=json_system,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )

        # Add raw response to metadata for QA validation
        metadata["raw_response"] = response

        parsed = self._parse_json_response(response)
        return parsed, metadata

    def _parse_json_response(self, response: str) -> dict:
        """
        Parse JSON from response, handling markdown code blocks.

        Returns empty dict on failure for graceful degradation.

        Args:
            response: Raw response text

        Returns:
            Parsed JSON dictionary, or empty dict if parsing fails
        """
        # Handle None or empty response
        if not response or not isinstance(response, str):
            logger.warning("json_parse_empty_input")
            return {}

        response = response.strip()
        if not response:
            logger.warning("json_parse_empty_after_strip")
            return {}

        # Limit response size to prevent regex performance issues
        if len(response) > 100_000:
            logger.warning(
                "json_parse_response_truncated",
                original_length=len(response),
            )
            response = response[:100_000]

        # Try direct parse first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try finding JSON object in response
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Return empty dict instead of raising - graceful degradation
        logger.error(
            "json_parse_failed",
            response_preview=response[:200] if response else "empty",
            response_length=len(response) if response else 0,
        )
        return {}

    async def generate_parallel(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperatures: list[float] | None = None,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> list[str]:
        """
        Generate multiple responses in parallel with different temperatures.
        Used for self-consistency voting. Includes staggered delays to avoid rate limits.

        Args:
            prompt: The user message/prompt
            system_prompt: Optional system instructions
            temperatures: List of temperature values to use
            max_tokens: Maximum response length per call
            model: Model to use

        Returns:
            List of generated responses (one per temperature)
        """
        results_with_metadata = await self.generate_parallel_with_metadata(
            prompt=prompt,
            system_prompt=system_prompt,
            temperatures=temperatures,
            max_tokens=max_tokens,
            model=model,
        )
        # Return just the response texts
        return [r[0] for r in results_with_metadata]

    async def generate_parallel_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperatures: list[float] | None = None,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> list[tuple[str, dict[str, Any]]]:
        """
        Generate multiple responses in parallel with metadata for each.

        Used for self-consistency voting with QA capture.
        Includes staggered delays to avoid rate limits.

        Args:
            prompt: The user message/prompt
            system_prompt: Optional system instructions
            temperatures: List of temperature values to use
            max_tokens: Maximum response length per call
            model: Model to use

        Returns:
            List of (response_text, metadata) tuples
        """
        temps = temperatures or [0.3, 0.5, 0.7, 0.85, 1.0]

        logger.info(
            "claude_parallel_generation",
            num_requests=len(temps),
            temperatures=temps,
        )

        # Stagger requests to reduce rate limit pressure
        async def staggered_generate(temp: float, index: int) -> tuple[str, dict[str, Any]]:
            # Add small delay based on index to stagger requests
            await asyncio.sleep(index * PARALLEL_STAGGER_DELAY)
            return await self.generate_with_metadata(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temp,
                max_tokens=max_tokens,
                model=model,
            )

        tasks = [
            staggered_generate(temp, i)
            for i, temp in enumerate(temps)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors and log them
        valid_results: list[tuple[str, dict[str, Any]]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "parallel_generation_error",
                    temperature=temps[i],
                    error=str(result),
                )
            else:
                valid_results.append(result)

        return valid_results

    async def generate_with_tools(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, str] | None = None,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a response with tool use capability.

        This method enables Claude to use tools like web_search, returning
        structured responses that may include tool calls. Used for RAG patterns.

        Args:
            messages: List of message dicts with role and content
            system_prompt: Optional system instructions
            tools: List of tool definitions (each with name, description, input_schema)
            tool_choice: Tool selection strategy ({"type": "auto|any|tool", "name": "..."})
            max_tokens: Maximum response length
            model: Model to use (defaults to instance default)

        Returns:
            Dict containing:
                - content: List of content blocks (text, tool_use)
                - stop_reason: Why generation stopped (end_turn, tool_use)
                - usage: Token usage info
                - model: Model used
        """
        use_model = model or self._default_model

        kwargs: dict[str, Any] = {
            "model": use_model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if tools:
            kwargs["tools"] = tools

        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        logger.info(
            "claude_tool_request",
            model=use_model,
            max_tokens=max_tokens,
            tool_count=len(tools) if tools else 0,
            message_count=len(messages),
        )

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = await self._client.messages.create(**kwargs)

                # Parse response content blocks
                content_blocks = []
                for block in response.content:
                    if hasattr(block, "text"):
                        content_blocks.append({
                            "type": "text",
                            "text": block.text,
                        })
                    elif hasattr(block, "type") and block.type == "tool_use":
                        content_blocks.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })

                result = {
                    "content": content_blocks,
                    "stop_reason": response.stop_reason,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                    "model": response.model,
                }

                logger.info(
                    "claude_tool_response",
                    stop_reason=response.stop_reason,
                    content_block_count=len(content_blocks),
                    usage_input=response.usage.input_tokens,
                    usage_output=response.usage.output_tokens,
                )

                return result

            except anthropic.RateLimitError as e:
                last_error = e
                delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                logger.warning(
                    "claude_tool_rate_limited",
                    attempt=attempt + 1,
                    max_retries=MAX_RETRIES,
                    delay_seconds=delay,
                )
                await asyncio.sleep(delay)

            except anthropic.APIError as e:
                logger.error("claude_tool_api_error", error=str(e))
                raise

        logger.error(
            "claude_tool_rate_limit_exhausted",
            max_retries=MAX_RETRIES,
            error=str(last_error),
        )
        raise last_error

    async def run_tool_loop(
        self,
        initial_messages: list[dict[str, Any]],
        system_prompt: str,
        tools: list[dict[str, Any]],
        tool_executor: Any,  # Callable that takes (tool_name, tool_input) -> result
        max_iterations: int = 10,
        model: str | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Run a multi-turn tool use loop until completion.

        This method handles the iterative pattern where Claude may call tools
        multiple times before producing a final text response.

        Args:
            initial_messages: Starting messages
            system_prompt: System instructions
            tools: Available tools
            tool_executor: Async function to execute tools: (name, input) -> result
            max_iterations: Maximum tool call rounds
            model: Model to use

        Returns:
            Tuple of (final_text_response, full_message_history)
        """
        messages = list(initial_messages)

        for iteration in range(max_iterations):
            response = await self.generate_with_tools(
                messages=messages,
                system_prompt=system_prompt,
                tools=tools,
                model=model,
            )

            # Add assistant response to messages
            messages.append({
                "role": "assistant",
                "content": response["content"],
            })

            # Check if we're done (no tool use)
            if response["stop_reason"] == "end_turn":
                # Extract final text
                final_text = ""
                for block in response["content"]:
                    if block["type"] == "text":
                        final_text += block["text"]
                return final_text, messages

            # Process tool calls
            tool_results = []
            for block in response["content"]:
                if block["type"] == "tool_use":
                    tool_name = block["name"]
                    tool_input = block["input"]
                    tool_id = block["id"]

                    logger.info(
                        "executing_tool",
                        tool_name=tool_name,
                        iteration=iteration + 1,
                    )

                    # Execute the tool
                    try:
                        result = await tool_executor(tool_name, tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": str(result),
                        })
                    except Exception as e:
                        logger.error(
                            "tool_execution_failed",
                            tool_name=tool_name,
                            error=str(e),
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": f"Error: {str(e)}",
                            "is_error": True,
                        })

            # Add tool results to messages
            if tool_results:
                messages.append({
                    "role": "user",
                    "content": tool_results,
                })

        # Max iterations reached
        logger.warning(
            "tool_loop_max_iterations",
            max_iterations=max_iterations,
        )
        return "", messages
