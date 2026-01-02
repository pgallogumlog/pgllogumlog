"""
Research Orchestrator for AI Readiness Compass.

UPGRADED: Runs all three research agents in parallel with REAL web research
and aggregates their results into the 70% research portion of the AI Readiness Score.
"""

import asyncio
import structlog
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable, Optional, Any


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float with fallback default.

    Handles strings, None, and invalid types gracefully.
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    return default

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
    """Aggregated research insights from all agents with REAL data."""

    company: CompanyResearchResult
    industry: IndustryResearchResult
    whitepaper: WhitePaperResearchResult
    aggregated_score: float  # 0-100, weighted combination

    # Aggregated sources for report citations
    all_sources: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for report generation with REAL data."""
        return {
            "company": {
                # Technology
                "detected_technologies": getattr(self.company, 'detected_technologies', []),
                "stack_maturity": getattr(self.company, 'stack_maturity', 'modern'),
                "integration_level": getattr(self.company, 'integration_level', 'medium'),
                "tech_findings": [
                    {"finding": f.finding, "source_url": f.source_url, "credibility": f.credibility}
                    for f in getattr(self.company, 'tech_findings', [])
                ],
                # Digital Maturity
                "digital_maturity_score": getattr(self.company, 'digital_maturity_score', 5),
                "digital_strengths": getattr(self.company, 'digital_strengths', []),
                "digital_gaps": getattr(self.company, 'digital_gaps', []),
                # AI Readiness
                "positive_ai_signals": [
                    {"finding": s.finding, "source_url": s.source_url}
                    for s in getattr(self.company, 'positive_ai_signals', [])
                ],
                "negative_ai_signals": [
                    {"finding": s.finding, "source_url": s.source_url}
                    for s in getattr(self.company, 'negative_ai_signals', [])
                ],
                "hiring_indicators": getattr(self.company, 'hiring_indicators', []),
                "automation_tools": getattr(self.company, 'automation_tools', []),
                # Data Infrastructure
                "data_infrastructure_score": getattr(self.company, 'data_infrastructure_score', 5),
                "detected_platforms": getattr(self.company, 'detected_platforms', []),
                # Competitive
                "digital_vs_industry": getattr(self.company, 'digital_vs_industry', 'average'),
                "key_differentiators": getattr(self.company, 'key_differentiators', []),
                "vulnerability_areas": getattr(self.company, 'vulnerability_areas', []),
                # Overall
                "readiness_score": getattr(self.company, 'overall_readiness_score', 50.0),
                "executive_summary": getattr(self.company, 'executive_summary', ''),
                # Citations
                "all_citations": getattr(self.company, 'all_citations', []),
            },
            "industry": {
                # Landscape
                "maturity_level": getattr(self.industry, 'maturity_level', 'growing'),
                "adoption_rate": getattr(self.industry, 'adoption_rate', ''),
                "trend_direction": getattr(self.industry, 'trend_direction', 'accelerating'),
                "key_statistics": [
                    {
                        "stat": getattr(s, 'stat', ''),
                        "source": getattr(s, 'source', ''),
                        "source_url": getattr(s, 'source_url', ''),
                        "credibility": getattr(s, 'credibility', 'medium'),
                    }
                    for s in getattr(self.industry, 'key_statistics', [])
                ],
                # Competitors
                "leading_competitors": [
                    {
                        "company_name": getattr(c, 'company_name', ''),
                        "ai_initiative": getattr(c, 'ai_initiative', ''),
                        "source": getattr(c, 'source', ''),
                        "source_url": getattr(c, 'source_url', ''),
                        "credibility": getattr(c, 'credibility', 'medium'),
                    }
                    for c in getattr(self.industry, 'leading_competitors', [])
                ],
                "adoption_level": getattr(self.industry, 'adoption_level', 'medium'),
                "competitive_urgency": getattr(self.industry, 'competitive_urgency', 'medium'),
                # Use Cases
                "proven_use_cases": [
                    {
                        "use_case": getattr(uc, 'use_case', ''),
                        "example_company": getattr(uc, 'example_company', ''),
                        "result": getattr(uc, 'result', ''),
                        "source_url": getattr(uc, 'source_url', ''),
                    }
                    for uc in getattr(self.industry, 'proven_use_cases', [])
                ],
                "emerging_use_cases": getattr(self.industry, 'emerging_use_cases', []),
                "use_case_relevance": getattr(self.industry, 'use_case_relevance', ''),
                # ROI
                "typical_roi": getattr(self.industry, 'typical_roi', ''),
                "time_to_value": getattr(self.industry, 'time_to_value', ''),
                "cost_range": getattr(self.industry, 'cost_range', ''),
                "success_rate": getattr(self.industry, 'success_rate', ''),
                # Regulatory
                "key_regulations": getattr(self.industry, 'key_regulations', []),
                "compliance_requirements": getattr(self.industry, 'compliance_requirements', []),
                "risk_factors": getattr(self.industry, 'risk_factors', []),
                # Forecast
                "growth_projection": getattr(self.industry, 'growth_projection', ''),
                "key_drivers": getattr(self.industry, 'key_drivers', []),
                "emerging_technologies": getattr(self.industry, 'emerging_technologies', []),
                # Overall
                "readiness_score": getattr(self.industry, 'industry_readiness_score', 50.0),
                "executive_summary": getattr(self.industry, 'executive_summary', ''),
                # Citations (fixed from search_sources)
                "all_citations": getattr(self.industry, 'all_citations', []),
            },
            "whitepaper": {
                # Case Studies - the premium content
                "case_studies": [
                    {
                        "title": getattr(cs, 'title', ''),
                        "company": getattr(cs, 'company', ''),
                        "industry": getattr(cs, 'industry', ''),
                        "challenge": getattr(cs, 'challenge', ''),
                        "solution": getattr(cs, 'solution', ''),
                        "vendor_tools": getattr(cs, 'vendor_tools', []),
                        "primary_result": getattr(cs, 'primary_result', ''),
                        "secondary_results": getattr(cs, 'secondary_results', []),
                        "timeline": getattr(cs, 'timeline', ''),
                        "source_title": getattr(cs, 'source_title', ''),
                        "source_url": getattr(cs, 'source_url', ''),
                        "credibility": getattr(cs, 'credibility', 'medium'),
                    }
                    for cs in getattr(self.whitepaper, 'case_studies', [])
                ],
                # Implementation
                "implementation": self._get_implementation_dict(),
                # Methodologies
                "methodologies": getattr(self.whitepaper, 'methodologies', []),
                # Vendors
                "vendors": self._get_vendors_dict(),
                # Risks
                "top_risks": getattr(self.whitepaper, 'top_risks', []),
                "regulatory_considerations": getattr(self.whitepaper, 'regulatory_considerations', []),
                "change_management": getattr(self.whitepaper, 'change_management', []),
                # Overall
                "confidence": getattr(self.whitepaper, 'confidence_score', 50.0),
                "executive_summary": getattr(self.whitepaper, 'executive_summary', ''),
                # Citations (fixed from all_sources)
                "all_citations": getattr(self.whitepaper, 'all_citations', []),
            },
            "aggregated_score": self.aggregated_score,
            "all_sources": self.all_sources,
        }

    def _get_implementation_dict(self) -> dict:
        """Safely get implementation data with defaults."""
        impl = getattr(self.whitepaper, 'implementation', None)
        if not impl:
            return {
                "average_timeline": "",
                "success_factors": [],
                "failure_reasons": [],
                "budget_small": "",
                "budget_medium": "",
                "budget_enterprise": "",
            }
        return {
            "average_timeline": getattr(impl, 'average_timeline', ''),
            "success_factors": getattr(impl, 'success_factors', []),
            "failure_reasons": getattr(impl, 'failure_reasons', []),
            "budget_small": getattr(impl, 'budget_small', ''),
            "budget_medium": getattr(impl, 'budget_medium', ''),
            "budget_enterprise": getattr(impl, 'budget_enterprise', ''),
        }

    def _get_vendors_dict(self) -> dict:
        """Safely get vendors data with defaults."""
        vendors = getattr(self.whitepaper, 'vendors', None)
        if not vendors:
            return {
                "leaders": [],
                "challengers": [],
                "pricing_models": [],
            }
        return {
            "leaders": getattr(vendors, 'leaders', []),
            "challengers": getattr(vendors, 'challengers', []),
            "pricing_models": getattr(vendors, 'pricing_models', []),
        }


class ResearchOrchestrator:
    """
    Orchestrates parallel execution of all research agents WITH REAL WEB RESEARCH.

    Runs CompanyResearchAgent, IndustryResearchAgent, and WhitePaperResearchAgent
    concurrently with actual web searches and aggregates their results.
    """

    # Weights for combining agent scores into research_score
    WEIGHTS = {
        "company": 0.40,  # Company-specific signals most important
        "industry": 0.35,  # Industry context important
        "whitepaper": 0.25,  # Best practices confidence
    }

    def __init__(
        self,
        ai_provider: AIProvider,
        web_research=None,  # WebResearchService (optional to avoid import cycle)
    ):
        self._ai = ai_provider
        self._web_research = web_research

        # Initialize agents with RAG orchestrator (parameter name is rag_orchestrator)
        self._company_agent = CompanyResearchAgent(
            ai_provider=ai_provider,
            rag_orchestrator=web_research,
        )
        self._industry_agent = IndustryResearchAgent(
            ai_provider=ai_provider,
            rag_orchestrator=web_research,
        )
        self._whitepaper_agent = WhitePaperResearchAgent(
            ai_provider=ai_provider,
            rag_orchestrator=web_research,
        )

    async def run_research(
        self,
        request: CompassRequest,
    ) -> tuple[ResearchInsights, float]:
        """
        Run all research agents in parallel with REAL web research.

        Args:
            request: CompassRequest with all submission data

        Returns:
            Tuple of (ResearchInsights, research_score)
            - ResearchInsights: Aggregated results from all agents
            - research_score: 0-100 score for 70% of AI Readiness Score
        """
        logger.info(
            "research_orchestration_started_real",
            company_name=request.company_name,
            industry=request.industry,
            web_research_enabled=self._web_research is not None,
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

        # Execute in parallel with exception handling
        results = await asyncio.gather(
            company_task,
            industry_task,
            whitepaper_task,
            return_exceptions=True,
        )

        # Handle partial failures gracefully
        company_result = results[0] if not isinstance(results[0], Exception) else self._get_fallback_company(request.company_name)
        industry_result = results[1] if not isinstance(results[1], Exception) else self._get_fallback_industry(request.industry)
        whitepaper_result = results[2] if not isinstance(results[2], Exception) else self._get_fallback_whitepaper(request.industry)

        # Log any failures
        for i, (result, name) in enumerate(zip(results, ["company", "industry", "whitepaper"])):
            if isinstance(result, Exception):
                logger.error(
                    f"research_agent_failed",
                    agent=name,
                    error=str(result),
                    error_type=type(result).__name__,
                )

        # Calculate aggregated research score
        research_score = self._calculate_research_score(
            company_result,
            industry_result,
            whitepaper_result,
        )

        # Aggregate all sources for citations (use all_citations attribute)
        all_sources = []
        all_sources.extend(getattr(industry_result, 'all_citations', []))
        all_sources.extend(getattr(whitepaper_result, 'all_citations', []))
        all_sources.extend(getattr(company_result, 'all_citations', []))
        # Deduplicate by URL
        seen_urls = set()
        unique_sources = []
        for s in all_sources:
            if s.get("url") and s["url"] not in seen_urls:
                seen_urls.add(s["url"])
                unique_sources.append(s)

        insights = ResearchInsights(
            company=company_result,
            industry=industry_result,
            whitepaper=whitepaper_result,
            aggregated_score=research_score,
            all_sources=unique_sources[:25],  # Top 25 sources
        )

        logger.info(
            "research_orchestration_completed_real",
            company_name=request.company_name,
            research_score=research_score,
            company_score=company_result.overall_readiness_score,
            industry_score=industry_result.industry_readiness_score,
            whitepaper_confidence=whitepaper_result.confidence_score,
            case_study_count=len(whitepaper_result.case_studies),
            source_count=len(unique_sources),
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
        # Use safe_float for type-safe score extraction
        company_score = safe_float(
            getattr(company, 'overall_readiness_score', 50.0),
            default=50.0
        )
        industry_score = safe_float(
            getattr(industry, 'industry_readiness_score', 50.0),
            default=50.0
        )
        whitepaper_score = safe_float(
            getattr(whitepaper, 'confidence_score', 50.0),
            default=50.0
        )

        weighted_score = (
            company_score * self.WEIGHTS["company"]
            + industry_score * self.WEIGHTS["industry"]
            + whitepaper_score * self.WEIGHTS["whitepaper"]
        )

        return round(weighted_score, 1)

    async def close(self):
        """Close web research service if initialized."""
        if self._web_research:
            await self._web_research.close()

    def _get_fallback_company(self, company_name: str) -> CompanyResearchResult:
        """Return fallback company result when research fails."""
        logger.warning("using_fallback_company_result", company_name=company_name)
        return CompanyResearchResult(
            overall_readiness_score=50.0,
            executive_summary=f"Research for {company_name} could not be completed. Using baseline assessment.",
            digital_maturity_score=5,
            data_infrastructure_score=5,
        )

    def _get_fallback_industry(self, industry: str) -> IndustryResearchResult:
        """Return fallback industry result when research fails."""
        logger.warning("using_fallback_industry_result", industry=industry)
        return IndustryResearchResult(
            maturity_level="growing",
            industry_readiness_score=50.0,
            executive_summary=f"Industry analysis for {industry} could not be completed. Using baseline assessment.",
            competitive_urgency="medium",
        )

    def _get_fallback_whitepaper(self, industry: str) -> WhitePaperResearchResult:
        """Return fallback whitepaper result when research fails."""
        logger.warning("using_fallback_whitepaper_result", industry=industry)
        return WhitePaperResearchResult(
            confidence_score=40.0,
            executive_summary=f"Case study research for {industry} could not be completed. General best practices apply.",
        )
