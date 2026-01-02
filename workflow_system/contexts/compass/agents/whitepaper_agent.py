"""
White Paper Research Agent for AI Readiness Compass.

UPGRADED: Uses RAG Orchestrator with Claude's native web search
to find REAL case studies and research with verifiable citations.
"""

import structlog
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable, Optional

from infrastructure.research.rag_orchestrator import (
    RAGOrchestrator,
    CaseStudyResearch as RAGCaseStudyResearch,
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


WHITEPAPER_ANALYSIS_SYSTEM = """You are a Senior Research Analyst specializing in AI implementation case studies.

ANALYSIS FRAMEWORK:
You have been provided with REAL web search results. Extract and analyze:

1. Case studies with specific companies and outcomes
2. ROI metrics and implementation timelines
3. Success factors and failure patterns
4. Vendor recommendations and pricing insights

CRITICAL REQUIREMENTS:
- Only cite information that appears in the search results provided
- Include source_url for every case study and statistic
- If information is not found, say "Not found in provided search results"
- Name REAL companies with REAL outcomes from the sources
- Quote specific metrics (percentages, dollar amounts, timelines)

OUTPUT FORMAT (JSON):
{
    "case_studies": [
        {
            "title": "Actual title from source",
            "company": "Real company name",
            "industry": "Their industry",
            "challenge": "What problem they faced",
            "solution": "What AI solution they implemented",
            "vendor_tools": ["specific tools mentioned"],
            "results": {
                "primary_metric": "e.g., 40% cost reduction",
                "secondary_metrics": ["other metrics mentioned"],
                "timeline": "implementation duration if mentioned"
            },
            "source_title": "Article/report title",
            "source_url": "URL from search results",
            "credibility": "high|medium"
        }
    ],
    "implementation_insights": {
        "average_timeline": "X months based on sources",
        "common_success_factors": ["factor from research"],
        "common_failure_reasons": ["reason from research"],
        "budget_ranges": {
            "small": "$X-$Y for small implementations",
            "medium": "$X-$Y for medium",
            "enterprise": "$X-$Y for enterprise"
        }
    },
    "methodology_recommendations": [
        {
            "name": "Methodology name",
            "description": "What it involves",
            "best_for": "When to use it",
            "source": "Where this recommendation comes from",
            "source_url": "URL"
        }
    ],
    "vendor_landscape": {
        "leaders": ["Vendor 1 - why", "Vendor 2 - why"],
        "challengers": ["Emerging vendors"],
        "pricing_models": ["Common pricing approaches"]
    },
    "risk_mitigation": {
        "top_risks": ["Risk with mitigation"],
        "regulatory_considerations": ["If applicable"],
        "change_management": ["Key considerations"]
    },
    "confidence_score": <1-100>,
    "executive_summary": "Key takeaways with specific citations from sources"
}
"""


@dataclass
class RealCaseStudy:
    """A documented, citable case study."""
    title: str
    company: str
    industry: str
    challenge: str
    solution: str
    vendor_tools: list[str]
    primary_result: str
    secondary_results: list[str]
    timeline: str
    source_title: str
    source_url: str
    credibility: str  # high, medium


@dataclass
class ImplementationInsight:
    """Insights from research about implementation."""
    average_timeline: str
    success_factors: list[str]
    failure_reasons: list[str]
    budget_small: str
    budget_medium: str
    budget_enterprise: str


@dataclass
class VendorInfo:
    """Information about AI solution vendors."""
    leaders: list[str]
    challengers: list[str]
    pricing_models: list[str]


@dataclass
class WhitePaperResearchResult:
    """Result from white paper research with REAL citations."""

    # Case Studies - the crown jewel
    case_studies: list[RealCaseStudy] = field(default_factory=list)

    # Implementation Insights
    implementation: Optional[ImplementationInsight] = None

    # Methodology Recommendations
    methodologies: list[dict] = field(default_factory=list)

    # Vendor Landscape
    vendors: Optional[VendorInfo] = None

    # Risk Mitigation
    top_risks: list[str] = field(default_factory=list)
    regulatory_considerations: list[str] = field(default_factory=list)
    change_management: list[str] = field(default_factory=list)

    # Overall
    confidence_score: float = 50.0
    executive_summary: str = ""

    # Citations for report
    all_citations: list[dict] = field(default_factory=list)


class WhitePaperResearchAgent:
    """
    Searches for REAL published case studies using RAG Orchestrator
    with Claude's native web search for verifiable citations.

    Contributes to the 70% research portion of AI Readiness Score
    and provides evidence-based recommendations.
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
        description: str,
    ) -> WhitePaperResearchResult:
        """
        Search for REAL case studies and research with citations.

        Args:
            industry: Industry sector
            company_size: Size of company
            pain_point: Primary business challenge
            description: Detailed description of situation

        Returns:
            WhitePaperResearchResult with REAL, CITABLE case studies
        """
        logger.info(
            "whitepaper_research_started_rag",
            industry=industry,
            pain_point=pain_point,
        )

        # Gather REAL data via RAG Orchestrator
        rag_research = None
        all_citations = []

        if self._rag:
            try:
                rag_research = await self._rag.research_case_studies(
                    industry=industry,
                    pain_point=pain_point,
                    company_size=company_size,
                )
                all_citations = rag_research.all_citations
                logger.info(
                    "whitepaper_rag_research_complete",
                    industry=industry,
                    citation_count=len(all_citations),
                )
            except Exception as e:
                logger.error(
                    "whitepaper_rag_research_failed",
                    industry=industry,
                    error=str(e),
                )

        # Build analysis prompt with REAL search results
        prompt = self._build_analysis_prompt(
            industry=industry,
            company_size=company_size,
            pain_point=pain_point,
            description=description,
            rag_research=rag_research,
        )

        try:
            result = await self._ai.generate_json(
                prompt=prompt,
                system_prompt=WHITEPAPER_ANALYSIS_SYSTEM,
                max_tokens=5000,
            )

            research_result = self._parse_result(result, all_citations)

            logger.info(
                "whitepaper_research_completed_rag",
                industry=industry,
                case_study_count=len(research_result.case_studies),
                confidence=research_result.confidence_score,
                citation_count=len(research_result.all_citations),
            )

            return research_result

        except Exception as e:
            logger.error(
                "whitepaper_research_failed",
                industry=industry,
                error=str(e),
            )
            return self._get_fallback_result(industry, all_citations)

    def _build_analysis_prompt(
        self,
        industry: str,
        company_size: str,
        pain_point: str,
        description: str,
        rag_research: Optional[RAGCaseStudyResearch],
    ) -> str:
        """Build prompt with REAL RAG search results."""

        # Format RAG search results
        search_section = "NO SEARCH RESULTS AVAILABLE"
        if rag_research and rag_research.all_citations:
            formatted = []
            for i, citation in enumerate(rag_research.all_citations[:30], 1):
                formatted.append(f"""
SOURCE {i}:
Title: {citation.get('title', 'Unknown')}
URL: {citation.get('url', '')}
Credibility: {citation.get('credibility', 'medium')}
Snippet: {citation.get('snippet', '')[:400]}
""")
            search_section = f"""=== REAL WEB SEARCH RESULTS ({len(rag_research.all_citations)} sources found) ===
{''.join(formatted)}
=== END SEARCH RESULTS ==="""

        return f"""Extract REAL case studies and insights from these search results:

CLIENT CONTEXT:
- Industry: {industry}
- Company Size: {company_size}
- Primary Challenge: {pain_point}
- Detailed Situation: {description}

{search_section}

INSTRUCTIONS:
1. Extract ONLY case studies that appear in these search results
2. Include the SOURCE URL for every case study
3. Quote specific metrics and outcomes when available
4. Name real companies - do NOT invent company names
5. If a source mentions a case study but lacks details, note what's missing
6. Prioritize high-credibility sources (analyst reports, major publications)
7. For recommendations, cite which source they come from

CRITICAL: Only include information that exists in the search results above.
If you cannot find relevant case studies, say "No relevant case studies found in search results"
rather than making them up.

Provide your analysis in the specified JSON format."""

    def _parse_result(
        self,
        result: dict,
        all_citations: list[dict],
    ) -> WhitePaperResearchResult:
        """Parse AI analysis into structured result."""

        # Parse case studies
        case_studies = []
        for cs in result.get("case_studies", []):
            if isinstance(cs, dict) and cs.get("company"):
                results_data = cs.get("results", {})
                case_studies.append(RealCaseStudy(
                    title=cs.get("title", ""),
                    company=cs.get("company", ""),
                    industry=cs.get("industry", ""),
                    challenge=cs.get("challenge", ""),
                    solution=cs.get("solution", ""),
                    vendor_tools=cs.get("vendor_tools", []),
                    primary_result=results_data.get("primary_metric", ""),
                    secondary_results=results_data.get("secondary_metrics", []),
                    timeline=results_data.get("timeline", ""),
                    source_title=cs.get("source_title", ""),
                    source_url=cs.get("source_url", ""),
                    credibility=cs.get("credibility", "medium"),
                ))

        # Parse implementation insights
        impl_data = result.get("implementation_insights", {})
        implementation = ImplementationInsight(
            average_timeline=impl_data.get("average_timeline", ""),
            success_factors=impl_data.get("common_success_factors", []),
            failure_reasons=impl_data.get("common_failure_reasons", []),
            budget_small=impl_data.get("budget_ranges", {}).get("small", ""),
            budget_medium=impl_data.get("budget_ranges", {}).get("medium", ""),
            budget_enterprise=impl_data.get("budget_ranges", {}).get("enterprise", ""),
        )

        # Parse vendor info
        vendor_data = result.get("vendor_landscape", {})
        vendors = VendorInfo(
            leaders=vendor_data.get("leaders", []),
            challengers=vendor_data.get("challengers", []),
            pricing_models=vendor_data.get("pricing_models", []),
        )

        # Parse risk mitigation
        risk_data = result.get("risk_mitigation", {})

        return WhitePaperResearchResult(
            case_studies=case_studies,
            implementation=implementation,
            methodologies=result.get("methodology_recommendations", []),
            vendors=vendors,
            top_risks=risk_data.get("top_risks", []),
            regulatory_considerations=risk_data.get("regulatory_considerations", []),
            change_management=risk_data.get("change_management", []),
            confidence_score=result.get("confidence_score", 50.0),
            executive_summary=result.get("executive_summary", ""),
            all_citations=all_citations,
        )

    def _get_fallback_result(
        self,
        industry: str,
        all_citations: list[dict],
    ) -> WhitePaperResearchResult:
        """Return fallback result if research fails."""
        return WhitePaperResearchResult(
            executive_summary=f"Research for {industry} based on available sources.",
            confidence_score=30.0,
            all_citations=all_citations,
        )
