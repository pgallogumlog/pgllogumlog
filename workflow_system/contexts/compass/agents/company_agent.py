"""
Company Research Agent for AI Readiness Compass.

Analyzes a company's website and digital presence to assess
technical sophistication and AI readiness signals.
"""

import structlog
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

logger = structlog.get_logger()


@runtime_checkable
class AIProvider(Protocol):
    """Protocol for AI provider dependency."""

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 4096,
    ) -> dict:
        ...


COMPANY_RESEARCH_SYSTEM = """You are a Company Research Agent analyzing a business for AI readiness.

Your task is to analyze the company's digital presence and infer their technical sophistication,
data maturity, and readiness for AI adoption.

ANALYSIS APPROACH:
1. Website Technology: Look for signs of modern tech stack, APIs, integrations
2. Data Infrastructure: Evidence of structured data, analytics, dashboards
3. Automation Signals: Existing tools (Zapier, HubSpot, Salesforce, etc.)
4. Digital Maturity: Mobile apps, modern UX, self-service capabilities
5. Scale Indicators: Company size, growth trajectory, market position

IMPORTANT: Base your analysis ONLY on observable signals. Don't make assumptions
about internal systems you cannot verify.

OUTPUT FORMAT (JSON):
{
    "tech_stack_signals": ["signal1", "signal2", ...],
    "automation_indicators": ["indicator1", "indicator2", ...],
    "data_infrastructure_score": <1-10>,
    "digital_maturity_score": <1-10>,
    "integration_complexity": "low" | "medium" | "high",
    "key_findings": ["finding1", "finding2", ...],
    "ai_opportunity_areas": ["area1", "area2", ...],
    "overall_readiness_score": <1-100>
}
"""


@dataclass
class CompanyResearchResult:
    """Result from company research analysis."""

    tech_stack_signals: list[str]
    automation_indicators: list[str]
    data_infrastructure_score: int  # 1-10
    digital_maturity_score: int  # 1-10
    integration_complexity: str  # low, medium, high
    key_findings: list[str]
    ai_opportunity_areas: list[str]
    overall_readiness_score: float  # 0-100


class CompanyResearchAgent:
    """
    Analyzes a company's website and digital presence.

    Contributes to the 70% research portion of AI Readiness Score.
    """

    def __init__(self, ai_provider: AIProvider):
        self._ai = ai_provider

    async def research(
        self,
        company_name: str,
        website: str,
        industry: str,
        description: str,
    ) -> CompanyResearchResult:
        """
        Analyze company for AI readiness signals.

        Args:
            company_name: Name of the company
            website: Company website URL
            industry: Industry sector
            description: User's description of their business/pain point

        Returns:
            CompanyResearchResult with analysis
        """
        logger.info(
            "company_research_started",
            company_name=company_name,
            website=website,
            industry=industry,
        )

        prompt = f"""Analyze this company for AI readiness:

COMPANY: {company_name}
WEBSITE: {website or "Not provided"}
INDUSTRY: {industry}
DESCRIPTION: {description}

Based on what you can infer about this company, assess their AI readiness.
If no website is provided, base your analysis on the industry and description.

Provide your analysis in the specified JSON format."""

        try:
            result = await self._ai.generate_json(
                prompt=prompt,
                system_prompt=COMPANY_RESEARCH_SYSTEM,
                max_tokens=2048,
            )

            research_result = CompanyResearchResult(
                tech_stack_signals=result.get("tech_stack_signals", []),
                automation_indicators=result.get("automation_indicators", []),
                data_infrastructure_score=result.get("data_infrastructure_score", 5),
                digital_maturity_score=result.get("digital_maturity_score", 5),
                integration_complexity=result.get("integration_complexity", "medium"),
                key_findings=result.get("key_findings", []),
                ai_opportunity_areas=result.get("ai_opportunity_areas", []),
                overall_readiness_score=result.get("overall_readiness_score", 50.0),
            )

            logger.info(
                "company_research_completed",
                company_name=company_name,
                readiness_score=research_result.overall_readiness_score,
            )

            return research_result

        except Exception as e:
            logger.error(
                "company_research_failed",
                company_name=company_name,
                error=str(e),
            )
            # Return default middle-ground result on failure
            return CompanyResearchResult(
                tech_stack_signals=["Unable to analyze"],
                automation_indicators=[],
                data_infrastructure_score=5,
                digital_maturity_score=5,
                integration_complexity="medium",
                key_findings=["Research unavailable - using industry defaults"],
                ai_opportunity_areas=[],
                overall_readiness_score=50.0,
            )
