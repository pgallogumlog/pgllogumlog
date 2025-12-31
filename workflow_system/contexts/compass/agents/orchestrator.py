"""
Research Orchestrator for AI Readiness Compass.

Runs all three research agents in parallel and aggregates their results
into the 70% research portion of the AI Readiness Score.
"""

import asyncio
import structlog
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from contexts.compass.models import CompassRequest
from contexts.compass.agents.company_agent import CompanyResearchAgent, CompanyResearchResult
from contexts.compass.agents.industry_agent import IndustryResearchAgent, IndustryResearchResult
from contexts.compass.agents.whitepaper_agent import WhitePaperResearchAgent, WhitePaperResearchResult

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


@dataclass
class ResearchInsights:
    """Aggregated research insights from all agents."""

    company: CompanyResearchResult
    industry: IndustryResearchResult
    whitepaper: WhitePaperResearchResult
    aggregated_score: float  # 0-100, weighted combination

    def to_dict(self) -> dict:
        """Convert to dictionary for report generation."""
        return {
            "company": {
                "tech_signals": self.company.tech_stack_signals,
                "automation_indicators": self.company.automation_indicators,
                "data_infrastructure_score": self.company.data_infrastructure_score,
                "digital_maturity_score": self.company.digital_maturity_score,
                "integration_complexity": self.company.integration_complexity,
                "key_findings": self.company.key_findings,
                "ai_opportunities": self.company.ai_opportunity_areas,
                "readiness_score": self.company.overall_readiness_score,
            },
            "industry": {
                "ai_maturity": self.industry.industry_ai_maturity,
                "common_use_cases": self.industry.common_use_cases,
                "competitor_adoption": self.industry.competitor_adoption_level,
                "regulatory": self.industry.regulatory_considerations,
                "skill_availability": self.industry.skill_availability,
                "benchmarks": self.industry.industry_benchmarks,
                "opportunities": self.industry.top_opportunities,
                "readiness_score": self.industry.industry_readiness_score,
            },
            "whitepaper": {
                "case_studies": [
                    {
                        "company_type": cs.company_type,
                        "challenge": cs.challenge,
                        "solution": cs.solution,
                        "result": cs.result,
                    }
                    for cs in self.whitepaper.relevant_case_studies
                ],
                "methodologies": self.whitepaper.recommended_methodologies,
                "pitfalls": self.whitepaper.common_pitfalls,
                "success_factors": self.whitepaper.success_factors,
                "roi_benchmarks": self.whitepaper.roi_benchmarks,
                "timeline": self.whitepaper.implementation_timeline,
                "resources": self.whitepaper.resource_requirements,
                "confidence": self.whitepaper.confidence_score,
            },
            "aggregated_score": self.aggregated_score,
        }


class ResearchOrchestrator:
    """
    Orchestrates parallel execution of all research agents.

    Runs CompanyResearchAgent, IndustryResearchAgent, and WhitePaperResearchAgent
    concurrently and aggregates their results.
    """

    # Weights for combining agent scores into research_score
    WEIGHTS = {
        "company": 0.40,  # Company-specific signals most important
        "industry": 0.35,  # Industry context important
        "whitepaper": 0.25,  # Best practices less weighted (more qualitative)
    }

    def __init__(self, ai_provider: AIProvider):
        self._ai = ai_provider
        self._company_agent = CompanyResearchAgent(ai_provider)
        self._industry_agent = IndustryResearchAgent(ai_provider)
        self._whitepaper_agent = WhitePaperResearchAgent(ai_provider)

    async def run_research(
        self,
        request: CompassRequest,
    ) -> tuple[ResearchInsights, float]:
        """
        Run all research agents in parallel.

        Args:
            request: CompassRequest with all submission data

        Returns:
            Tuple of (ResearchInsights, research_score)
            - ResearchInsights: Aggregated results from all agents
            - research_score: 0-100 score for 70% of AI Readiness Score
        """
        logger.info(
            "research_orchestration_started",
            company_name=request.company_name,
            industry=request.industry,
        )

        # Run all three agents in parallel
        company_task = self._company_agent.research(
            company_name=request.company_name,
            website=request.website,
            industry=request.industry,
            description=request.description,
        )

        industry_task = self._industry_agent.research(
            industry=request.industry,
            company_size=request.company_size,
            pain_point=request.pain_point,
        )

        whitepaper_task = self._whitepaper_agent.research(
            industry=request.industry,
            company_size=request.company_size,
            pain_point=request.pain_point,
            description=request.description,
        )

        # Execute in parallel
        company_result, industry_result, whitepaper_result = await asyncio.gather(
            company_task,
            industry_task,
            whitepaper_task,
        )

        # Calculate aggregated research score
        research_score = self._calculate_research_score(
            company_result,
            industry_result,
            whitepaper_result,
        )

        insights = ResearchInsights(
            company=company_result,
            industry=industry_result,
            whitepaper=whitepaper_result,
            aggregated_score=research_score,
        )

        logger.info(
            "research_orchestration_completed",
            company_name=request.company_name,
            research_score=research_score,
            company_score=company_result.overall_readiness_score,
            industry_score=industry_result.industry_readiness_score,
            whitepaper_confidence=whitepaper_result.confidence_score,
        )

        return insights, research_score

    def _calculate_research_score(
        self,
        company: CompanyResearchResult,
        industry: IndustryResearchResult,
        whitepaper: WhitePaperResearchResult,
    ) -> float:
        """
        Calculate weighted research score from all agents.

        Weights:
        - Company: 40% (direct company analysis)
        - Industry: 35% (industry context)
        - Whitepaper: 25% (best practices confidence)

        Returns:
            Score from 0-100
        """
        weighted_score = (
            company.overall_readiness_score * self.WEIGHTS["company"]
            + industry.industry_readiness_score * self.WEIGHTS["industry"]
            + whitepaper.confidence_score * self.WEIGHTS["whitepaper"]
        )

        return round(weighted_score, 1)

    def to_insights_dict(self, insights: ResearchInsights) -> dict:
        """
        Convert research insights to dictionary for report generation.

        Used by report templates to access research data.
        """
        return {
            "company": {
                "tech_signals": insights.company.tech_stack_signals,
                "automation_indicators": insights.company.automation_indicators,
                "data_infrastructure_score": insights.company.data_infrastructure_score,
                "digital_maturity_score": insights.company.digital_maturity_score,
                "integration_complexity": insights.company.integration_complexity,
                "key_findings": insights.company.key_findings,
                "ai_opportunities": insights.company.ai_opportunity_areas,
                "readiness_score": insights.company.overall_readiness_score,
            },
            "industry": {
                "ai_maturity": insights.industry.industry_ai_maturity,
                "common_use_cases": insights.industry.common_use_cases,
                "competitor_adoption": insights.industry.competitor_adoption_level,
                "regulatory": insights.industry.regulatory_considerations,
                "skill_availability": insights.industry.skill_availability,
                "benchmarks": insights.industry.industry_benchmarks,
                "opportunities": insights.industry.top_opportunities,
                "readiness_score": insights.industry.industry_readiness_score,
            },
            "whitepaper": {
                "case_studies": [
                    {
                        "company_type": cs.company_type,
                        "challenge": cs.challenge,
                        "solution": cs.solution,
                        "result": cs.result,
                    }
                    for cs in insights.whitepaper.relevant_case_studies
                ],
                "methodologies": insights.whitepaper.recommended_methodologies,
                "pitfalls": insights.whitepaper.common_pitfalls,
                "success_factors": insights.whitepaper.success_factors,
                "roi_benchmarks": insights.whitepaper.roi_benchmarks,
                "timeline": insights.whitepaper.implementation_timeline,
                "resources": insights.whitepaper.resource_requirements,
                "confidence": insights.whitepaper.confidence_score,
            },
            "aggregated_score": insights.aggregated_score,
        }
