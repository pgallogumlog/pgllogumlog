"""
Company Research Agent for AI Readiness Compass.

UPGRADED: Uses RAG Orchestrator with Claude's native web search
to gather REAL company data with verifiable citations.
"""

import structlog
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable, Optional

from infrastructure.research.rag_orchestrator import (
    RAGOrchestrator,
    CompanyResearch as RAGCompanyResearch,
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


COMPANY_ANALYSIS_SYSTEM = """You are a Senior Technical Analyst with extensive knowledge of enterprise technology landscapes.

ANALYSIS FRAMEWORK:
You have been provided with REAL web search results about the company. Use ONLY this data to assess:

1. Technology Sophistication: Based on detected OR typical technologies for their segment
2. Digital Maturity: Based on website presence and known company positioning
3. AI Readiness Signals: Job postings, tech partnerships, public announcements
4. Data Infrastructure: Evidence of analytics, CRM, data platforms
5. Growth Indicators: Hiring, expansion, digital investment signals

CRITICAL REQUIREMENTS:
- Only cite information that appears in the search results provided
- Include source_url for every fact you cite
- If information is not found, say "Not found in provided search results"
- Do NOT hallucinate or make up company information

OUTPUT FORMAT (JSON):
{
    "technology_assessment": {
        "detected_stack": ["tech1", "tech2"],
        "stack_maturity": "legacy|modern|cutting-edge",
        "integration_level": "low|medium|high",
        "key_findings": [
            {"finding": "specific finding", "source_url": "URL from search results"}
        ]
    },
    "digital_maturity": {
        "score": <1-10>,
        "strengths": ["strength1", "strength2"],
        "gaps": ["gap1", "gap2"],
        "evidence": [
            {"evidence": "specific evidence", "source_url": "URL from search results"}
        ]
    },
    "ai_readiness_signals": {
        "positive_signals": [
            {"signal": "signal description", "source_url": "URL"}
        ],
        "negative_signals": [
            {"concern": "concern description", "source_url": "URL"}
        ],
        "hiring_indicators": ["relevant job postings or tech roles"],
        "automation_tools_detected": ["tool1", "tool2"]
    },
    "data_infrastructure": {
        "score": <1-10>,
        "detected_platforms": ["CRM", "analytics tools found"],
        "data_maturity_evidence": [
            {"evidence": "specific finding", "source_url": "URL"}
        ]
    },
    "competitive_position": {
        "digital_vs_industry": "behind|average|ahead",
        "key_differentiators": ["what they do well"],
        "vulnerability_areas": ["where they lag"]
    },
    "overall_readiness_score": <1-100>,
    "executive_summary": "2-3 sentence summary citing specific sources"
}
"""


@dataclass
class TechFinding:
    """A technology finding with source citation."""
    finding: str
    source_url: str
    credibility: str = "medium"


@dataclass
class CompanyResearchResult:
    """Result from company research analysis with REAL data."""

    # Technology Assessment
    detected_technologies: list[str] = field(default_factory=list)
    stack_maturity: str = "modern"
    integration_level: str = "medium"
    tech_findings: list[TechFinding] = field(default_factory=list)

    # Digital Maturity
    digital_maturity_score: int = 5
    digital_strengths: list[str] = field(default_factory=list)
    digital_gaps: list[str] = field(default_factory=list)

    # AI Readiness Signals
    positive_ai_signals: list[TechFinding] = field(default_factory=list)
    negative_ai_signals: list[TechFinding] = field(default_factory=list)
    hiring_indicators: list[str] = field(default_factory=list)
    automation_tools: list[str] = field(default_factory=list)

    # Data Infrastructure
    data_infrastructure_score: int = 5
    detected_platforms: list[str] = field(default_factory=list)

    # Competitive Position
    digital_vs_industry: str = "average"
    key_differentiators: list[str] = field(default_factory=list)
    vulnerability_areas: list[str] = field(default_factory=list)

    # Overall
    overall_readiness_score: float = 50.0
    executive_summary: str = ""

    # Citations for report
    all_citations: list[dict] = field(default_factory=list)


class CompanyResearchAgent:
    """
    Analyzes a company's REAL web presence using RAG Orchestrator
    with Claude's native web search to assess AI readiness.

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
        company_name: str,
        website: str,
        industry: str,
        description: str,
    ) -> CompanyResearchResult:
        """
        Perform REAL analysis of company for AI readiness.

        Args:
            company_name: Name of the company
            website: Company website URL
            industry: Industry sector
            description: User's description of their business/pain point

        Returns:
            CompanyResearchResult with REAL analysis based on web search data
        """
        logger.info(
            "company_research_started_rag",
            company_name=company_name,
            website=website,
            industry=industry,
        )

        # Gather REAL data via RAG Orchestrator
        rag_research = None
        all_citations = []

        if self._rag:
            try:
                rag_research = await self._rag.research_company(
                    company_name=company_name,
                    website=website,
                    industry=industry,
                )
                all_citations = rag_research.all_citations
                logger.info(
                    "company_rag_research_complete",
                    company=company_name,
                    citation_count=len(all_citations),
                )
            except Exception as e:
                logger.error(
                    "company_rag_research_failed",
                    company=company_name,
                    error=str(e),
                )

        # Build analysis prompt with REAL search results
        prompt = self._build_analysis_prompt(
            company_name=company_name,
            website=website,
            industry=industry,
            description=description,
            rag_research=rag_research,
        )

        try:
            result = await self._ai.generate_json(
                prompt=prompt,
                system_prompt=COMPANY_ANALYSIS_SYSTEM,
                max_tokens=3000,
            )

            research_result = self._parse_result(result, all_citations)

            logger.info(
                "company_research_completed_rag",
                company_name=company_name,
                readiness_score=research_result.overall_readiness_score,
                tech_count=len(research_result.detected_technologies),
                citation_count=len(research_result.all_citations),
            )

            return research_result

        except Exception as e:
            logger.error(
                "company_research_failed",
                company_name=company_name,
                error=str(e),
            )
            return self._get_fallback_result(company_name, all_citations)

    def _build_analysis_prompt(
        self,
        company_name: str,
        website: str,
        industry: str,
        description: str,
        rag_research: Optional[RAGCompanyResearch],
    ) -> str:
        """Build prompt with REAL RAG search results."""

        # Format RAG search results
        search_section = "NO SEARCH RESULTS AVAILABLE"
        if rag_research and rag_research.all_citations:
            formatted = []
            for i, citation in enumerate(rag_research.all_citations[:20], 1):
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

        return f"""Analyze this company's AI readiness based on REAL web search results:

COMPANY: {company_name}
WEBSITE: {website or "Not provided"}
INDUSTRY: {industry}

USER DESCRIPTION OF BUSINESS:
{description}

{search_section}

INSTRUCTIONS:
1. Only cite information that appears in the search results above
2. Include the source URL for every claim you make
3. If information is not found, say "Not found in search results"
4. Focus on SPECIFIC findings from the actual search results
5. Do NOT make up or hallucinate company information

Provide your analysis in the specified JSON format."""

    def _parse_result(
        self,
        result: dict,
        all_citations: list[dict],
    ) -> CompanyResearchResult:
        """Parse AI analysis into structured result."""

        tech_assessment = result.get("technology_assessment", {})
        digital = result.get("digital_maturity", {})
        ai_signals = result.get("ai_readiness_signals", {})
        data_infra = result.get("data_infrastructure", {})
        competitive = result.get("competitive_position", {})

        # Parse tech findings with citations
        tech_findings = []
        for f in tech_assessment.get("key_findings", []):
            if isinstance(f, dict):
                tech_findings.append(TechFinding(
                    finding=f.get("finding", str(f)),
                    source_url=f.get("source_url", ""),
                    credibility="medium",
                ))
            elif isinstance(f, str):
                tech_findings.append(TechFinding(finding=f, source_url=""))

        # Parse AI signals with citations
        positive_signals = []
        for s in ai_signals.get("positive_signals", []):
            if isinstance(s, dict):
                positive_signals.append(TechFinding(
                    finding=s.get("signal", str(s)),
                    source_url=s.get("source_url", ""),
                ))
            elif isinstance(s, str):
                positive_signals.append(TechFinding(finding=s, source_url=""))

        negative_signals = []
        for s in ai_signals.get("negative_signals", []):
            if isinstance(s, dict):
                negative_signals.append(TechFinding(
                    finding=s.get("concern", str(s)),
                    source_url=s.get("source_url", ""),
                ))
            elif isinstance(s, str):
                negative_signals.append(TechFinding(finding=s, source_url=""))

        return CompanyResearchResult(
            # Technology
            detected_technologies=tech_assessment.get("detected_stack", []),
            stack_maturity=tech_assessment.get("stack_maturity", "modern"),
            integration_level=tech_assessment.get("integration_level", "medium"),
            tech_findings=tech_findings,

            # Digital Maturity
            digital_maturity_score=digital.get("score", 5),
            digital_strengths=digital.get("strengths", []),
            digital_gaps=digital.get("gaps", []),

            # AI Readiness
            positive_ai_signals=positive_signals,
            negative_ai_signals=negative_signals,
            hiring_indicators=ai_signals.get("hiring_indicators", []),
            automation_tools=ai_signals.get("automation_tools_detected", []),

            # Data Infrastructure
            data_infrastructure_score=data_infra.get("score", 5),
            detected_platforms=data_infra.get("detected_platforms", []),

            # Competitive
            digital_vs_industry=competitive.get("digital_vs_industry", "average"),
            key_differentiators=competitive.get("key_differentiators", []),
            vulnerability_areas=competitive.get("vulnerability_areas", []),

            # Overall
            overall_readiness_score=result.get("overall_readiness_score", 50.0),
            executive_summary=result.get("executive_summary", ""),

            # Citations
            all_citations=all_citations,
        )

    def _get_fallback_result(
        self,
        company_name: str,
        all_citations: list[dict],
    ) -> CompanyResearchResult:
        """Return fallback result if analysis fails."""
        return CompanyResearchResult(
            executive_summary=f"Analysis of {company_name} based on available data.",
            overall_readiness_score=50.0,
            all_citations=all_citations,
        )
