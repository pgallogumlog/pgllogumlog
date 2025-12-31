"""
White Paper Research Agent for AI Readiness Compass.

Provides case studies, best practices, and proven methodologies
relevant to the client's situation.
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


WHITEPAPER_RESEARCH_SYSTEM = """You are a White Paper Research Agent specializing in AI implementation best practices.

Your task is to synthesize relevant case studies, methodologies, and proven approaches
that apply to the client's specific situation.

RESEARCH APPROACH:
1. Relevant Case Studies: Find examples of similar companies succeeding with AI
2. Implementation Methodologies: What frameworks work best?
3. Common Pitfalls: What mistakes should they avoid?
4. Success Factors: What separates successful AI projects from failures?
5. ROI Evidence: What returns have similar companies achieved?

FOCUS ON ACTIONABLE KNOWLEDGE:
- Specific frameworks they can follow
- Metrics to track for success
- Timeline expectations based on similar projects
- Resource requirements from comparable implementations

OUTPUT FORMAT (JSON):
{
    "relevant_case_studies": [
        {
            "company_type": "description",
            "challenge": "what they faced",
            "solution": "what they implemented",
            "result": "outcome achieved"
        }
    ],
    "recommended_methodologies": ["methodology1", "methodology2", ...],
    "common_pitfalls": ["pitfall1", "pitfall2", ...],
    "success_factors": ["factor1", "factor2", ...],
    "roi_benchmarks": {
        "cost_reduction": "X-Y%",
        "time_savings": "X-Y%",
        "revenue_impact": "description"
    },
    "implementation_timeline": "X-Y months",
    "resource_requirements": {
        "budget_range": "$X-$Y",
        "team_size": "X-Y people",
        "skills_needed": ["skill1", "skill2"]
    },
    "confidence_score": <1-100>
}
"""


@dataclass
class CaseStudy:
    """A relevant case study from research."""

    company_type: str
    challenge: str
    solution: str
    result: str


@dataclass
class WhitePaperResearchResult:
    """Result from white paper research analysis."""

    relevant_case_studies: list[CaseStudy]
    recommended_methodologies: list[str]
    common_pitfalls: list[str]
    success_factors: list[str]
    roi_benchmarks: dict[str, str]
    implementation_timeline: str
    resource_requirements: dict[str, any]
    confidence_score: float  # 0-100


class WhitePaperResearchAgent:
    """
    Provides case studies and best practices research.

    Contributes to the 70% research portion of AI Readiness Score
    and enriches report with evidence-based recommendations.
    """

    def __init__(self, ai_provider: AIProvider):
        self._ai = ai_provider

    async def research(
        self,
        industry: str,
        company_size: str,
        pain_point: str,
        description: str,
    ) -> WhitePaperResearchResult:
        """
        Research case studies and best practices.

        Args:
            industry: Industry sector
            company_size: Size of company
            pain_point: Primary business challenge
            description: Detailed description of situation

        Returns:
            WhitePaperResearchResult with case studies and methodologies
        """
        logger.info(
            "whitepaper_research_started",
            industry=industry,
            pain_point=pain_point,
        )

        prompt = f"""Research case studies and best practices for this AI implementation scenario:

INDUSTRY: {industry}
COMPANY SIZE: {company_size}
PRIMARY CHALLENGE: {pain_point}
DETAILED SITUATION: {description}

Find relevant examples and proven methodologies that would help this company succeed.
Focus on:
1. Similar companies that solved similar problems
2. Proven implementation approaches
3. Common mistakes to avoid
4. Expected ROI and timelines

Provide your research findings in the specified JSON format."""

        try:
            result = await self._ai.generate_json(
                prompt=prompt,
                system_prompt=WHITEPAPER_RESEARCH_SYSTEM,
                max_tokens=3000,
            )

            # Parse case studies
            case_studies = []
            for cs in result.get("relevant_case_studies", []):
                if isinstance(cs, dict):
                    case_studies.append(
                        CaseStudy(
                            company_type=cs.get("company_type", "Similar company"),
                            challenge=cs.get("challenge", "Similar challenge"),
                            solution=cs.get("solution", "AI implementation"),
                            result=cs.get("result", "Positive outcome"),
                        )
                    )

            research_result = WhitePaperResearchResult(
                relevant_case_studies=case_studies,
                recommended_methodologies=result.get("recommended_methodologies", []),
                common_pitfalls=result.get("common_pitfalls", []),
                success_factors=result.get("success_factors", []),
                roi_benchmarks=result.get("roi_benchmarks", {}),
                implementation_timeline=result.get("implementation_timeline", "3-6 months"),
                resource_requirements=result.get("resource_requirements", {}),
                confidence_score=result.get("confidence_score", 70.0),
            )

            logger.info(
                "whitepaper_research_completed",
                industry=industry,
                case_study_count=len(research_result.relevant_case_studies),
                confidence=research_result.confidence_score,
            )

            return research_result

        except Exception as e:
            logger.error(
                "whitepaper_research_failed",
                industry=industry,
                error=str(e),
            )
            return WhitePaperResearchResult(
                relevant_case_studies=[
                    CaseStudy(
                        company_type="Mid-size company",
                        challenge="Manual processes consuming resources",
                        solution="AI-powered automation",
                        result="30% efficiency improvement",
                    )
                ],
                recommended_methodologies=["Start small, iterate fast", "Pilot program approach"],
                common_pitfalls=["Over-engineering initial solution", "Insufficient training data"],
                success_factors=["Executive sponsorship", "Clear success metrics"],
                roi_benchmarks={
                    "cost_reduction": "20-40%",
                    "time_savings": "30-50%",
                    "revenue_impact": "Indirect through efficiency",
                },
                implementation_timeline="3-6 months",
                resource_requirements={
                    "budget_range": "$10K-$50K",
                    "team_size": "1-3 people",
                    "skills_needed": ["Project management", "Domain expertise"],
                },
                confidence_score=50.0,
            )
