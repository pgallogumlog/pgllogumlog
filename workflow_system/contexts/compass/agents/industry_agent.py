"""
Industry Research Agent for AI Readiness Compass.

UPGRADED: Uses RAG Orchestrator with Claude's native web search
to gather REAL industry data with verifiable citations.
"""

import structlog
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable, Optional

from infrastructure.research.rag_orchestrator import (
    RAGOrchestrator,
    IndustryResearch as RAGIndustryResearch,
    WebSearchResult,
)

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


INDUSTRY_ANALYSIS_SYSTEM = """You are a Senior Industry Analyst specializing in AI adoption across industries.

ANALYSIS FRAMEWORK:
You have been provided with REAL web search results. Use ONLY this data to analyze:

1. Industry AI adoption statistics and trends
2. Competitor AI initiatives with specific examples
3. ROI benchmarks and implementation metrics
4. Regulatory considerations

CRITICAL REQUIREMENTS:
- Only cite information that appears in the search results provided
- Include source_url for every statistic or claim
- If information is not found, say "Not found in provided search results"
- Quote specific percentages and numbers from sources
- Name real companies found in the search results

OUTPUT FORMAT (JSON):
{
    "industry_ai_landscape": {
        "maturity_level": "early|growing|maturing|advanced",
        "adoption_rate": "X% (source name)",
        "trend_direction": "accelerating|steady|emerging",
        "key_statistics": [
            {"stat": "actual statistic", "source": "source name", "source_url": "URL"}
        ]
    },
    "competitor_intelligence": {
        "leading_companies": [
            {"name": "Company Name", "ai_initiative": "What they're doing", "source": "where found", "source_url": "URL"}
        ],
        "adoption_level": "low|medium|high",
        "competitive_urgency": "low|medium|high|critical"
    },
    "use_case_analysis": {
        "proven_use_cases": [
            {"use_case": "specific use case", "example_company": "company name", "result": "specific outcome", "source_url": "URL"}
        ],
        "emerging_use_cases": ["use case 1", "use case 2"],
        "relevance_to_client": "how these apply to their situation"
    },
    "roi_benchmarks": {
        "typical_roi": "X-Y% (source)",
        "time_to_value": "X months (source)",
        "cost_range": "$X-$Y (source)",
        "success_rate": "X% (source)"
    },
    "regulatory_landscape": {
        "key_regulations": ["regulation 1", "regulation 2"],
        "compliance_requirements": ["requirement 1"],
        "risk_factors": ["risk 1"]
    },
    "market_forecast": {
        "growth_projection": "X% CAGR (source)",
        "key_drivers": ["driver 1", "driver 2"],
        "emerging_technologies": ["tech 1", "tech 2"]
    },
    "industry_readiness_score": <1-100>,
    "executive_summary": "2-3 sentences with SPECIFIC data points citing sources"
}
"""


@dataclass
class IndustryStatistic:
    """A specific industry statistic with citation."""
    stat: str
    source: str
    source_url: str = ""
    credibility: str = "medium"


@dataclass
class CompetitorExample:
    """A real competitor AI initiative."""
    company_name: str
    ai_initiative: str
    source: str
    source_url: str = ""
    credibility: str = "medium"


@dataclass
class ProvenUseCase:
    """A proven AI use case with real example."""
    use_case: str
    example_company: str
    result: str
    source_url: str = ""
    credibility: str = "medium"


@dataclass
class IndustryResearchResult:
    """Result from industry research with REAL data and citations."""

    # Industry Landscape
    maturity_level: str = "growing"
    adoption_rate: str = ""
    trend_direction: str = "accelerating"
    key_statistics: list[IndustryStatistic] = field(default_factory=list)

    # Competitor Intelligence
    leading_competitors: list[CompetitorExample] = field(default_factory=list)
    adoption_level: str = "medium"
    competitive_urgency: str = "medium"

    # Use Cases
    proven_use_cases: list[ProvenUseCase] = field(default_factory=list)
    emerging_use_cases: list[str] = field(default_factory=list)
    use_case_relevance: str = ""

    # ROI Benchmarks
    typical_roi: str = ""
    time_to_value: str = ""
    cost_range: str = ""
    success_rate: str = ""

    # Regulatory
    key_regulations: list[str] = field(default_factory=list)
    compliance_requirements: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)

    # Forecast
    growth_projection: str = ""
    key_drivers: list[str] = field(default_factory=list)
    emerging_technologies: list[str] = field(default_factory=list)

    # Overall
    industry_readiness_score: float = 50.0
    executive_summary: str = ""

    # Citations for report
    all_citations: list[dict] = field(default_factory=list)


class IndustryResearchAgent:
    """
    Analyzes AI adoption patterns using RAG Orchestrator with
    Claude's native web search for REAL market data and citations.

    Contributes to the 70% research portion of AI Readiness Score.
    """

    def __init__(
        self,
        ai_provider: AIProvider,
        rag_orchestrator: Optional[RAGOrchestrator] = None,
    ):
        self._ai = ai_provider
        self._rag = rag_orchestrator

    async def research(
        self,
        industry: str,
        company_size: str,
        pain_point: str,
    ) -> IndustryResearchResult:
        """
        Perform REAL industry research with web searches.

        Args:
            industry: Industry sector
            company_size: Size of company
            pain_point: Primary business challenge

        Returns:
            IndustryResearchResult with REAL data and citations
        """
        logger.info(
            "industry_research_started_rag",
            industry=industry,
            company_size=company_size,
        )

        # Gather REAL data via RAG Orchestrator
        rag_research = None
        all_citations = []

        if self._rag:
            try:
                rag_research = await self._rag.research_industry(
                    industry=industry,
                    pain_point=pain_point,
                )
                all_citations = rag_research.all_citations
                logger.info(
                    "industry_rag_research_complete",
                    industry=industry,
                    citation_count=len(all_citations),
                )
            except Exception as e:
                logger.error(
                    "industry_rag_research_failed",
                    industry=industry,
                    error=str(e),
                )

        # Build analysis prompt with REAL search results
        prompt = self._build_analysis_prompt(
            industry=industry,
            company_size=company_size,
            pain_point=pain_point,
            rag_research=rag_research,
        )

        try:
            result = await self._ai.generate_json(
                prompt=prompt,
                system_prompt=INDUSTRY_ANALYSIS_SYSTEM,
                max_tokens=4000,
            )

            research_result = self._parse_result(result, all_citations)

            logger.info(
                "industry_research_completed_rag",
                industry=industry,
                readiness_score=research_result.industry_readiness_score,
                citation_count=len(research_result.all_citations),
            )

            return research_result

        except Exception as e:
            logger.error(
                "industry_research_failed",
                industry=industry,
                error=str(e),
            )
            return self._get_fallback_result(industry, all_citations)

    def _build_analysis_prompt(
        self,
        industry: str,
        company_size: str,
        pain_point: str,
        rag_research: Optional[RAGIndustryResearch],
    ) -> str:
        """Build prompt with REAL RAG search results."""

        # Format RAG search results
        search_section = "NO SEARCH RESULTS AVAILABLE"
        if rag_research and rag_research.all_citations:
            formatted = []
            for i, citation in enumerate(rag_research.all_citations[:25], 1):
                formatted.append(f"""
SOURCE {i}:
Title: {citation.get('title', 'Unknown')}
URL: {citation.get('url', '')}
Credibility: {citation.get('credibility', 'medium')}
Snippet: {citation.get('snippet', '')[:300]}
""")
            search_section = f"""=== REAL WEB SEARCH RESULTS ({len(rag_research.all_citations)} sources found) ===
{''.join(formatted)}
=== END SEARCH RESULTS ==="""

        return f"""Analyze AI adoption and trends for this industry based on REAL search results:

INDUSTRY: {industry}
COMPANY SIZE CONTEXT: {company_size}
PRIMARY CHALLENGE: {pain_point}

{search_section}

INSTRUCTIONS:
1. Only cite information that appears in the search results above
2. Include the source URL for every statistic or claim
3. Quote actual percentages and dollar amounts from sources
4. Name real companies found in the results
5. If specific data isn't found, say "Not found in search results"
6. Focus on actionable intelligence for a {company_size} company facing {pain_point}

Provide your analysis in the specified JSON format."""

    def _parse_result(
        self,
        result: dict,
        all_citations: list[dict],
    ) -> IndustryResearchResult:
        """Parse AI analysis into structured result."""

        landscape = result.get("industry_ai_landscape", {})
        competitors = result.get("competitor_intelligence", {})
        use_cases = result.get("use_case_analysis", {})
        roi = result.get("roi_benchmarks", {})
        regulatory = result.get("regulatory_landscape", {})
        forecast = result.get("market_forecast", {})

        # Parse key statistics
        key_stats = []
        for stat in landscape.get("key_statistics", []):
            if isinstance(stat, dict):
                key_stats.append(IndustryStatistic(
                    stat=stat.get("stat", ""),
                    source=stat.get("source", ""),
                    source_url=stat.get("source_url", ""),
                ))

        # Parse competitor examples
        leading_comps = []
        for comp in competitors.get("leading_companies", []):
            if isinstance(comp, dict):
                leading_comps.append(CompetitorExample(
                    company_name=comp.get("name", ""),
                    ai_initiative=comp.get("ai_initiative", ""),
                    source=comp.get("source", ""),
                    source_url=comp.get("source_url", ""),
                ))

        # Parse proven use cases
        proven_cases = []
        for uc in use_cases.get("proven_use_cases", []):
            if isinstance(uc, dict):
                proven_cases.append(ProvenUseCase(
                    use_case=uc.get("use_case", ""),
                    example_company=uc.get("example_company", ""),
                    result=uc.get("result", ""),
                    source_url=uc.get("source_url", ""),
                ))

        return IndustryResearchResult(
            # Landscape
            maturity_level=landscape.get("maturity_level", "growing"),
            adoption_rate=landscape.get("adoption_rate", ""),
            trend_direction=landscape.get("trend_direction", "accelerating"),
            key_statistics=key_stats,

            # Competitors
            leading_competitors=leading_comps,
            adoption_level=competitors.get("adoption_level", "medium"),
            competitive_urgency=competitors.get("competitive_urgency", "medium"),

            # Use Cases
            proven_use_cases=proven_cases,
            emerging_use_cases=use_cases.get("emerging_use_cases", []),
            use_case_relevance=use_cases.get("relevance_to_client", ""),

            # ROI
            typical_roi=roi.get("typical_roi", ""),
            time_to_value=roi.get("time_to_value", ""),
            cost_range=roi.get("cost_range", ""),
            success_rate=roi.get("success_rate", ""),

            # Regulatory
            key_regulations=regulatory.get("key_regulations", []),
            compliance_requirements=regulatory.get("compliance_requirements", []),
            risk_factors=regulatory.get("risk_factors", []),

            # Forecast
            growth_projection=forecast.get("growth_projection", ""),
            key_drivers=forecast.get("key_drivers", []),
            emerging_technologies=forecast.get("emerging_technologies", []),

            # Overall
            industry_readiness_score=result.get("industry_readiness_score", 50.0),
            executive_summary=result.get("executive_summary", ""),

            # Citations
            all_citations=all_citations,
        )

    def _get_fallback_result(
        self,
        industry: str,
        all_citations: list[dict],
    ) -> IndustryResearchResult:
        """Return fallback result if research fails."""
        return IndustryResearchResult(
            maturity_level="growing",
            executive_summary=f"Industry analysis for {industry} based on available sources.",
            industry_readiness_score=50.0,
            all_citations=all_citations,
        )
