"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest and provides:
- Mock AI provider for testing without API calls
- Mock email/sheets clients
- Common test data
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from config.dependency_injection import Container


# ===================
# Mock Providers
# ===================


class MockAIProvider:
    """Mock AI provider for testing without API calls."""

    def __init__(self):
        self.generate_calls = []
        self.generate_json_calls = []
        self._responses = []
        self._json_responses = []

    def set_responses(self, responses: list[str]):
        """Set responses to return from generate()."""
        self._responses = list(responses)

    def set_json_responses(self, responses: list[dict]):
        """Set responses to return from generate_json()."""
        self._json_responses = list(responses)

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> str:
        """Mock generate - returns preset responses or a default."""
        self.generate_calls.append({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
        })

        if self._responses:
            return self._responses.pop(0)

        # Default response with a valid markdown table
        return """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | Customer Support Bot | Automate support tickets | High volume, slow response | AI chatbot | n8n, OpenAI | Response time | High |
| 2 | Lead Scoring | Prioritize sales leads | Manual scoring | ML model | Zapier, HubSpot | Conversion rate | Medium |
| 3 | Invoice Processing | Automate AP | Manual data entry | OCR + AI | Make, QuickBooks | Processing time | High |
| 4 | Email Triage | Route emails | Inbox overload | NLP classification | Gmail API | Routing accuracy | High |
| 5 | Report Generation | Automate reports | Time-consuming | Template + AI | n8n, Google Sheets | Time saved | Medium |

The answer is Customer Support Bot"""

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> dict:
        """Mock generate_json - returns preset responses or a default."""
        self.generate_json_calls.append({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
        })

        if self._json_responses:
            return self._json_responses.pop(0)

        # Default JSON response
        return {
            "businessSummary": "Test business summary",
            "customerSegments": ["Segment 1", "Segment 2"],
            "operationalPainPoints": ["Pain point 1"],
            "growthOpportunities": ["Opportunity 1"],
        }

    async def generate_parallel(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperatures: list[float] | None = None,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> list[str]:
        """Mock parallel generation - returns multiple responses."""
        temps = temperatures or [0.4, 0.6, 0.8, 1.0, 1.2]
        responses = []

        for _ in temps:
            response = await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=max_tokens,
            )
            responses.append(response)

        return responses

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> tuple[str, dict]:
        """Mock generate with metadata for QA capture."""
        response = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )
        metadata = {
            "model": model or "claude-sonnet-4-20250514",
            "input_tokens": len(prompt) // 4,  # Rough estimate
            "output_tokens": len(response) // 4,
            "stop_reason": "end_turn",
        }
        return response, metadata

    async def generate_json_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> tuple[dict, dict]:
        """Mock generate_json with metadata for QA capture."""
        import json
        response = await self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )
        raw_response = json.dumps(response)
        metadata = {
            "model": model or "claude-sonnet-4-20250514",
            "input_tokens": len(prompt) // 4,
            "output_tokens": len(raw_response) // 4,
            "stop_reason": "end_turn",
            "raw_response": raw_response,
        }
        return response, metadata

    async def generate_parallel_with_metadata(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperatures: list[float] | None = None,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> list[tuple[str, dict]]:
        """Mock parallel generation with metadata."""
        temps = temperatures or [0.4, 0.6, 0.8, 1.0, 1.2]
        results = []

        for temp in temps:
            response, metadata = await self.generate_with_metadata(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temp,
                max_tokens=max_tokens,
                model=model,
            )
            results.append((response, metadata))

        return results

    async def generate_json_with_web_search(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 8192,
        max_searches: int = 15,
        model: str | None = None,
    ) -> tuple[dict, dict, list[dict]]:
        """
        Mock generate_json with web search for testing.

        Returns a tuple of (parsed_json, metadata, citations) where
        citations simulate real web search results with verifiable URLs.
        """
        import json

        # Generate mock JSON response
        response = await self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.0,
            max_tokens=max_tokens,
            model=model,
        )

        raw_response = json.dumps(response)

        # Build metadata
        metadata = {
            "model": model or "claude-sonnet-4-20250514",
            "input_tokens": len(prompt) // 4,
            "output_tokens": len(raw_response) // 4,
            "stop_reason": "end_turn",
            "web_searches_performed": max_searches,
            "raw_response": raw_response,
        }

        # Generate mock citations (simulating real web search results)
        # Use real domains so URL verification can pass in tests if needed
        citations = [
            {
                "title": "McKinsey AI Report 2025",
                "url": "https://www.mckinsey.com/business-functions/mckinsey-digital/our-insights/ai-adoption-report",
                "snippet": "AI adoption in enterprises increased 47% in 2024...",
                "source": "claude_web_search",
            },
            {
                "title": "Gartner AI Trends",
                "url": "https://www.gartner.com/en/newsroom/press-releases/ai-trends",
                "snippet": "By 2025, 75% of enterprises will shift from piloting to operationalizing AI...",
                "source": "claude_web_search",
            },
            {
                "title": "Industry Digital Transformation",
                "url": "https://www.forbes.com/digital-transformation",
                "snippet": "Digital transformation spending reached $2.3 trillion globally...",
                "source": "claude_web_search",
            },
            {
                "title": "AI Implementation Best Practices",
                "url": "https://hbr.org/ai-implementation-guide",
                "snippet": "Companies that invest in AI change management see 3x higher ROI...",
                "source": "claude_web_search",
            },
            {
                "title": "Enterprise AI Case Studies",
                "url": "https://www.microsoft.com/en-us/ai/customer-stories",
                "snippet": "Learn how businesses are transforming with AI solutions...",
                "source": "claude_web_search",
            },
        ]

        # Extend citations to meet minimum requirements (10+)
        for i in range(5, max_searches):
            citations.append({
                "title": f"AI Research Finding {i + 1}",
                "url": f"https://research.example{i}.com/ai-study",
                "snippet": f"Research finding {i + 1} about AI implementation...",
                "source": "claude_web_search",
            })

        return response, metadata, citations[:max_searches]


class MockEmailClient:
    """Mock email client for testing."""

    def __init__(self):
        self.sent_emails = []
        self.unread_emails = []

    async def fetch_unread(self) -> list[dict]:
        return self.unread_emails

    async def send(self, to: str, subject: str, body: str, html: bool = True) -> bool:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
        return True

    async def mark_read(self, message_id: str) -> bool:
        return True


class MockSheetsClient:
    """Mock Google Sheets client for testing."""

    def __init__(self):
        self.appended_rows = []
        self.sheet_data = {}

    async def append_row(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        values: list,
    ) -> bool:
        self.appended_rows.append({
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name,
            "values": values,
        })
        return True

    async def read_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
    ) -> list[dict]:
        key = f"{spreadsheet_id}:{sheet_name}"
        return self.sheet_data.get(key, [])


# ===================
# Fixtures
# ===================


@pytest.fixture
def mock_ai_provider():
    """Provide a mock AI provider."""
    return MockAIProvider()


@pytest.fixture
def mock_email_client():
    """Provide a mock email client."""
    return MockEmailClient()


@pytest.fixture
def mock_sheets_client():
    """Provide a mock sheets client."""
    return MockSheetsClient()


@pytest.fixture
def test_container(mock_ai_provider, mock_email_client, mock_sheets_client):
    """Provide a container with all mocked dependencies."""
    container = Container()
    container.override("ai_provider", mock_ai_provider)
    container.override("email_client", mock_email_client)
    container.override("sheets_client", mock_sheets_client)
    return container


