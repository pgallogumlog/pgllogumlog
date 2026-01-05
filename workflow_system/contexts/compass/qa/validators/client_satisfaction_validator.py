"""
Client Satisfaction Validator - Reviews final report against client expectations.

Validates that the Compass report:
1. Fulfills what the client requested
2. Addresses their specific pain point
3. Meets quality standards for a premium report
"""

import structlog
from html.parser import HTMLParser
from typing import Protocol, runtime_checkable

from contexts.compass.models import CompassRequest
from contexts.compass.qa_models import ClientSatisfactionQAResult

logger = structlog.get_logger()


@runtime_checkable
class AIProvider(Protocol):
    """Protocol for AI provider dependency."""

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> dict:
        """Generate JSON response from AI."""
        ...


class HTMLTextExtractor(HTMLParser):
    """Extract text content from HTML for Claude review."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {"script", "style", "head"}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_endtag(self, tag):
        self.current_tag = None

    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)

    def get_text(self) -> str:
        return "\n".join(self.text_parts)


class ClientSatisfactionValidator:
    """
    Validates final Compass report meets client expectations.

    Uses Claude to perform semantic review of:
    - Request fulfillment (does report answer what they asked?)
    - Pain point resolution (does report address their specific pain?)
    - Overall quality (is it professional and valuable?)
    """

    SYSTEM_PROMPT = """You are a Client Success Manager reviewing a final AI Readiness report.

TASK: Evaluate if the report meets the client's expectations and needs.

You will evaluate the final report on three dimensions:

1. REQUEST FULFILLMENT (0-10)
   - Does report answer what client asked for?
   - Are all requested topics covered?
   - Is scope appropriate for a premium $497 report?
   Score: 10 = fully fulfills request, 0 = misses the mark

2. PAIN POINT RESOLUTION (0-10)
   - Does report address client's specific pain point?
   - Are recommendations actionable for their situation?
   - Will client find this valuable?
   Score: 10 = directly solves pain point, 0 = doesn't help

3. OVERALL REPORT QUALITY (0-10)
   - Is report professional and polished?
   - Is structure clear and easy to navigate?
   - Are insights valuable and actionable?
   Score: 10 = excellent deliverable, 0 = poor quality

Return your evaluation as JSON with this exact structure:
{
  "fulfillment_score": <0-10>,
  "pain_point_score": <0-10>,
  "quality_score": <0-10>,
  "feedback": "<brief 2-3 sentence explanation of scores>",
  "client_likely_satisfied": <true/false>,
  "suggestions": ["<improvement 1>", "<improvement 2>"]
}"""

    USER_PROMPT_TEMPLATE = """CLIENT REQUEST:
Company: {company_name}
Industry: {industry}
Website: {website_url}
Pain Point: {pain_point}
Description: {description}

FINAL REPORT (text extraction from HTML):
{final_report_text}

Evaluate the report and return JSON with your assessment."""

    def __init__(self, ai_provider: AIProvider):
        """
        Initialize client satisfaction validator.

        Args:
            ai_provider: AI provider for semantic validation
        """
        self._ai = ai_provider

    def _extract_text_from_html(self, html: str) -> str:
        """
        Extract readable text from HTML report.

        Args:
            html: HTML report content

        Returns:
            Extracted text content
        """
        parser = HTMLTextExtractor()
        parser.feed(html)
        text = parser.get_text()

        # Truncate if too long (Claude context limits)
        max_chars = 50000
        if len(text) > max_chars:
            logger.warning(
                "html_text_truncated",
                original_length=len(text),
                truncated_length=max_chars,
            )
            text = text[:max_chars] + "\n\n[... truncated for length ...]"

        return text

    async def validate(
        self,
        request: CompassRequest,
        final_report_html: str,
    ) -> ClientSatisfactionQAResult:
        """
        Validate final report against client expectations.

        Args:
            request: Original client request
            final_report_html: Generated HTML report

        Returns:
            ClientSatisfactionQAResult with scores and feedback
        """
        logger.info(
            "client_satisfaction_validation_started",
            company=request.company_name,
        )

        try:
            # Extract text from HTML for Claude review
            report_text = self._extract_text_from_html(final_report_html)

            # Build user prompt
            user_prompt = self.USER_PROMPT_TEMPLATE.format(
                company_name=request.company_name,
                industry=request.industry,
                website_url=request.website,
                pain_point=request.pain_point,
                description=request.description,
                final_report_text=report_text,
            )

            # Call Claude for semantic validation
            response = await self._ai.generate_json(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.0,  # Deterministic scoring
                max_tokens=2048,
            )

            # Parse response
            fulfillment_score = float(response.get("fulfillment_score", 0))
            pain_point_score = float(response.get("pain_point_score", 0))
            quality_score = float(response.get("quality_score", 0))
            feedback = response.get("feedback", "No feedback provided")
            client_likely_satisfied = bool(
                response.get("client_likely_satisfied", False)
            )
            suggestions = response.get("suggestions", [])

            # Create result
            result = ClientSatisfactionQAResult(
                fulfillment_score=fulfillment_score,
                pain_point_score=pain_point_score,
                quality_score=quality_score,
                feedback=feedback,
                client_likely_satisfied=client_likely_satisfied,
                suggestions=suggestions if isinstance(suggestions, list) else [],
            )

            logger.info(
                "client_satisfaction_validation_completed",
                company=request.company_name,
                overall_score=result.overall_score,
                passed=result.passed,
                likely_satisfied=result.client_likely_satisfied,
            )

            return result

        except Exception as e:
            logger.error(
                "client_satisfaction_validation_failed",
                company=request.company_name,
                error=str(e),
            )
            # Return failed result
            return ClientSatisfactionQAResult(
                fulfillment_score=0.0,
                pain_point_score=0.0,
                quality_score=0.0,
                feedback=f"Validation failed: {str(e)}",
                client_likely_satisfied=False,
                suggestions=[],
            )
