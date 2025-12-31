"""
Industry Research Agent for AI Readiness Compass.

Analyzes AI adoption patterns, benchmarks, and opportunities
specific to the client's industry sector.
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


INDUSTRY_RESEARCH_SYSTEM = """You are an Industry Research Agent specializing in AI adoption analysis.

Your task is to analyze AI adoption patterns, success stories, and opportunities
specific to the client's industry sector.

ANALYSIS APPROACH:
1. Industry AI Maturity: How advanced is AI adoption in this industry overall?
2. Common AI Use Cases: What AI applications are succeeding in this industry?
3. Competitive Landscape: Are competitors using AI? What's the risk of falling behind?
4. Regulatory Considerations: Any AI-related compliance requirements?
5. Skill Availability: Is AI talent available for this industry?

PROVIDE ACTIONABLE INSIGHTS:
- What are industry leaders doing with AI?
- What's the typical ROI for AI projects in this industry?
- What are the most impactful AI use cases for this sector?

OUTPUT FORMAT (JSON):
{
    "industry_ai_maturity": "early" | "growing" | "mature" | "advanced",
    "common_use_cases": ["use case 1", "use case 2", ...],
    "competitor_adoption_level": "low" | "medium" | "high",
    "regulatory_considerations": ["consideration1", "consideration2", ...],
    "skill_availability": "scarce" | "limited" | "available" | "abundant",
    "industry_benchmarks": {
        "typical_roi_range": "X-Y%",
        "implementation_timeline": "X-Y months",
        "adoption_rate": "X%"
    },
    "top_opportunities": ["opportunity1", "opportunity2", ...],
    "industry_readiness_score": <1-100>
}
"""


@dataclass
class IndustryResearchResult:
    """Result from industry research analysis."""

    industry_ai_maturity: str  # early, growing, mature, advanced
    common_use_cases: list[str]
    competitor_adoption_level: str  # low, medium, high
    regulatory_considerations: list[str]
    skill_availability: str  # scarce, limited, available, abundant
    industry_benchmarks: dict[str, str]
    top_opportunities: list[str]
    industry_readiness_score: float  # 0-100


class IndustryResearchAgent:
    """
    Analyzes AI adoption patterns in the client's industry.

    Contributes to the 70% research portion of AI Readiness Score.
    """

    def __init__(self, ai_provider: AIProvider):
        self._ai = ai_provider

    async def research(
        self,
        industry: str,
        company_size: str,
        pain_point: str,
    ) -> IndustryResearchResult:
        """
        Analyze industry AI adoption patterns.

        Args:
            industry: Industry sector
            company_size: Size of company
            pain_point: Primary business challenge

        Returns:
            IndustryResearchResult with analysis
        """
        logger.info(
            "industry_research_started",
            industry=industry,
            company_size=company_size,
        )

        prompt = f"""Analyze AI adoption patterns for this industry context:

INDUSTRY: {industry}
COMPANY SIZE: {company_size}
PRIMARY CHALLENGE: {pain_point}

Provide insights on:
1. How mature is AI adoption in {industry}?
2. What are the most successful AI use cases in this industry?
3. What should companies of this size focus on?
4. What's the competitive risk of not adopting AI?

Provide your analysis in the specified JSON format."""

        try:
            result = await self._ai.generate_json(
                prompt=prompt,
                system_prompt=INDUSTRY_RESEARCH_SYSTEM,
                max_tokens=2048,
            )

            research_result = IndustryResearchResult(
                industry_ai_maturity=result.get("industry_ai_maturity", "growing"),
                common_use_cases=result.get("common_use_cases", []),
                competitor_adoption_level=result.get("competitor_adoption_level", "medium"),
                regulatory_considerations=result.get("regulatory_considerations", []),
                skill_availability=result.get("skill_availability", "limited"),
                industry_benchmarks=result.get("industry_benchmarks", {}),
                top_opportunities=result.get("top_opportunities", []),
                industry_readiness_score=result.get("industry_readiness_score", 50.0),
            )

            logger.info(
                "industry_research_completed",
                industry=industry,
                maturity=research_result.industry_ai_maturity,
                readiness_score=research_result.industry_readiness_score,
            )

            return research_result

        except Exception as e:
            logger.error(
                "industry_research_failed",
                industry=industry,
                error=str(e),
            )
            return IndustryResearchResult(
                industry_ai_maturity="growing",
                common_use_cases=["Customer service automation", "Data analytics"],
                competitor_adoption_level="medium",
                regulatory_considerations=[],
                skill_availability="limited",
                industry_benchmarks={
                    "typical_roi_range": "20-40%",
                    "implementation_timeline": "3-6 months",
                    "adoption_rate": "30%",
                },
                top_opportunities=["Process automation", "Customer experience"],
                industry_readiness_score=50.0,
            )
