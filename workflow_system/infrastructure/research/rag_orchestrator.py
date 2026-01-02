"""
RAG Orchestrator for AI Readiness Compass.

This module implements a RAG (Retrieval-Augmented Generation) pattern
using Claude's knowledge base to gather authoritative research with citations.

Architecture:
- Agents call RAGOrchestrator methods
- RAGOrchestrator calls Claude with structured research prompts
- Claude returns synthesized research with known source citations
- Results are structured into citation-ready format

NOTE: Real-time web search requires external APIs (Tavily, SerpAPI).
When not configured, uses Claude's training knowledge with attributions.
"""

from __future__ import annotations

import json
import asyncio
import os
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

import anthropic
import structlog

logger = structlog.get_logger()


@dataclass
class WebSearchResult:
    """A search result with citation information."""
    title: str
    url: str
    snippet: str
    source: str = "claude_knowledge"  # or "web_search" when live search enabled
    credibility: str = "medium"  # high, medium, low
    retrieved_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_citation(self) -> dict:
        """Convert to citation format for report templates."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "credibility": self.credibility,
            "retrieved_at": self.retrieved_at,
        }


@dataclass
class ResearchResult:
    """Aggregated research results with citations."""
    query: str
    results: list[WebSearchResult]
    summary: str = ""
    confidence: float = 0.0

    @property
    def citations(self) -> list[dict]:
        """Get all citations in template-ready format."""
        return [r.to_citation() for r in self.results]

    @property
    def has_results(self) -> bool:
        return len(self.results) > 0


@dataclass
class CompanyResearch:
    """Research results specific to a company."""
    company_name: str
    website_url: str
    technology_initiatives: list[WebSearchResult] = field(default_factory=list)
    news_mentions: list[WebSearchResult] = field(default_factory=list)
    ai_initiatives: list[WebSearchResult] = field(default_factory=list)
    summary: str = ""

    @property
    def all_citations(self) -> list[dict]:
        """Get all company research citations."""
        citations = []
        for result in self.technology_initiatives + self.news_mentions + self.ai_initiatives:
            citations.append(result.to_citation())
        return citations


@dataclass
class IndustryResearch:
    """Research results for industry analysis."""
    industry: str
    statistics: list[WebSearchResult] = field(default_factory=list)
    trends: list[WebSearchResult] = field(default_factory=list)
    competitor_initiatives: list[WebSearchResult] = field(default_factory=list)
    adoption_data: list[WebSearchResult] = field(default_factory=list)
    summary: str = ""

    @property
    def all_citations(self) -> list[dict]:
        """Get all industry research citations."""
        citations = []
        for result in self.statistics + self.trends + self.competitor_initiatives + self.adoption_data:
            citations.append(result.to_citation())
        return citations


@dataclass
class CaseStudyResearch:
    """Research results for case studies."""
    industry: str
    pain_point: str
    case_studies: list[WebSearchResult] = field(default_factory=list)
    roi_data: list[WebSearchResult] = field(default_factory=list)
    implementation_guides: list[WebSearchResult] = field(default_factory=list)
    summary: str = ""

    @property
    def all_citations(self) -> list[dict]:
        """Get all case study citations."""
        citations = []
        for result in self.case_studies + self.roi_data + self.implementation_guides:
            citations.append(result.to_citation())
        return citations


# Credibility scoring based on domain
HIGH_CREDIBILITY_DOMAINS = [
    "mckinsey.com", "gartner.com", "deloitte.com", "accenture.com",
    "pwc.com", "bain.com", "bcg.com", "forrester.com", "idc.com",
    "hbr.org", "mit.edu", "stanford.edu", "harvard.edu",
    "reuters.com", "bloomberg.com", "wsj.com", "ft.com",
    "techcrunch.com", "wired.com", "venturebeat.com",
]

MEDIUM_CREDIBILITY_DOMAINS = [
    "forbes.com", "businessinsider.com", "cio.com", "zdnet.com",
    "infoworld.com", "computerworld.com", "entrepreneur.com",
]


def assess_credibility(url: str) -> str:
    """Assess credibility based on URL domain."""
    url_lower = url.lower()
    for domain in HIGH_CREDIBILITY_DOMAINS:
        if domain in url_lower:
            return "high"
    for domain in MEDIUM_CREDIBILITY_DOMAINS:
        if domain in url_lower:
            return "medium"
    return "medium"  # Default to medium for knowledge-based results


RESEARCH_SYSTEM_PROMPT = """You are a Senior Industry Research Analyst with extensive knowledge of:
- McKinsey Global AI Survey reports and State of AI research
- Gartner Magic Quadrants, Hype Cycles, and market research
- Deloitte AI Institute research and case studies
- Accenture Technology Vision reports
- Harvard Business Review AI case studies
- MIT Sloan Management Review digital transformation research
- Published vendor case studies (Microsoft, Google, AWS, Salesforce, etc.)
- Industry-specific AI implementation reports

CRITICAL INSTRUCTIONS:
1. Provide REAL statistics and data from your knowledge of published research
2. Name REAL companies with DOCUMENTED outcomes
3. Include proper source attribution (e.g., "McKinsey State of AI 2024")
4. Provide realistic URLs to known publication pages (e.g., mckinsey.com/capabilities/quantumblack/our-insights)
5. NEVER fabricate statistics - only cite what you know from training data
6. When uncertain, say "Based on industry patterns" rather than inventing numbers

OUTPUT FORMAT (JSON):
{
    "findings": [
        {
            "title": "Finding/Article title",
            "url": "Known URL pattern for source",
            "snippet": "Key excerpt with specific data",
            "source_name": "Publication name (e.g., McKinsey)",
            "credibility": "high|medium"
        }
    ],
    "summary": "Executive summary of key findings"
}
"""


class RAGOrchestrator:
    """
    RAG Orchestrator using Claude's knowledge base for research.

    This orchestrator provides research using Claude's training knowledge
    of published reports, case studies, and industry research. Each method:
    1. Constructs targeted research prompts
    2. Calls Claude to synthesize knowledge from training data
    3. Structures results with source attributions
    4. Returns citation-ready data for report generation

    NOTE: For real-time web search, configure TAVILY_API_KEY or SERP_API_KEY.

    Usage:
        rag = RAGOrchestrator(api_key="sk-ant-...")
        results = await rag.search_web("commercial real estate AI adoption")
        # results.citations contains attributed sources
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        use_web_search: bool = True,
    ):
        """
        Initialize RAG Orchestrator.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            use_web_search: Enable Claude's native web search tool
        """
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model
        self._use_web_search = use_web_search

    async def _research_with_knowledge(
        self,
        query: str,
        context: str = "",
        max_tokens: int = 4096,
    ) -> tuple[str, list[WebSearchResult]]:
        """
        Research using Claude's knowledge base.

        Args:
            query: The research query
            context: Additional context for the research
            max_tokens: Maximum response tokens

        Returns:
            Tuple of (summary_text, list of WebSearchResults)
        """
        logger.info("rag_knowledge_research", query=query[:100])

        full_prompt = f"""Research the following topic and provide findings with proper attributions:

RESEARCH QUERY: {query}

{f"ADDITIONAL CONTEXT: {context}" if context else ""}

Provide your research findings in the specified JSON format.
Include specific statistics, company examples, and source attributions.
Only include information you are confident about from known publications."""

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=RESEARCH_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": full_prompt}],
            )

            # Extract text content
            result_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    result_text += block.text

            # Parse JSON response
            search_results = self._parse_research_response(result_text)

            logger.info(
                "rag_knowledge_research_complete",
                query=query[:50],
                result_count=len(search_results),
            )

            return result_text, search_results

        except Exception as e:
            logger.error("rag_knowledge_research_failed", query=query[:50], error=str(e))
            raise

    async def _research_with_web_search(
        self,
        query: str,
        max_tokens: int = 4096,
    ) -> tuple[str, list[WebSearchResult]]:
        """
        Research using Claude's native web search tool.

        Args:
            query: The research query
            max_tokens: Maximum response tokens

        Returns:
            Tuple of (summary_text, list of WebSearchResults)
        """
        logger.info("rag_web_search_started", query=query[:100])

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                tools=[{"type": "web_search_20250305"}],
                messages=[{
                    "role": "user",
                    "content": f"""Search the web for current information about: {query}

Find relevant statistics, case studies, and industry data.
Summarize your findings with specific citations."""
                }],
            )

            # Extract text and web search results
            result_text = ""
            search_results = []

            for block in response.content:
                if hasattr(block, "text"):
                    result_text += block.text
                elif block.type == "web_search_tool_result":
                    # Extract citations from web search results
                    for search_result in getattr(block, "search_results", []):
                        url = getattr(search_result, "url", "")
                        search_results.append(WebSearchResult(
                            title=getattr(search_result, "title", ""),
                            url=url,
                            snippet=getattr(search_result, "snippet", "")[:500],
                            source="claude_web_search",
                            credibility=assess_credibility(url),
                        ))

            logger.info(
                "rag_web_search_complete",
                query=query[:50],
                result_count=len(search_results),
            )

            return result_text, search_results

        except Exception as e:
            logger.warning("rag_web_search_failed", query=query[:50], error=str(e))
            # Fall back to knowledge-based research
            return await self._research_with_knowledge(query)

    def _parse_research_response(self, response_text: str) -> list[WebSearchResult]:
        """Parse Claude's research response into WebSearchResults."""
        results = []

        try:
            # Extract JSON from response
            json_str = self._extract_json(response_text)
            if json_str:
                data = json.loads(json_str)
                for finding in data.get("findings", []):
                    url = finding.get("url", "")
                    results.append(WebSearchResult(
                        title=finding.get("title", ""),
                        url=url,
                        snippet=finding.get("snippet", ""),
                        source="claude_knowledge",
                        credibility=finding.get("credibility", assess_credibility(url)),
                    ))
        except json.JSONDecodeError as e:
            logger.warning("json_parse_warning", error=str(e))
            # Return empty results if parse fails
            pass

        return results

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON object from text."""
        # Find JSON block
        start = text.find('{')
        if start == -1:
            return None

        # Find matching closing brace
        depth = 0
        for i, char in enumerate(text[start:], start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
        return None

    async def search_web(
        self,
        query: str,
        num_results: int = 10,
    ) -> ResearchResult:
        """
        Research a topic and return structured results.

        Uses Claude's native web search when enabled, otherwise uses knowledge base.

        Args:
            query: Search query
            num_results: Target number of results

        Returns:
            ResearchResult with citations
        """
        if self._use_web_search:
            response_text, search_results = await self._research_with_web_search(
                query=query,
            )
        else:
            response_text, search_results = await self._research_with_knowledge(
                query=query,
                context=f"Provide approximately {num_results} relevant findings.",
            )

        # Calculate confidence based on result quality
        high_cred_count = sum(1 for r in search_results if r.credibility == "high")
        confidence = min(0.85, 0.5 + (high_cred_count * 0.08) + (len(search_results) * 0.02))

        # Extract summary from response
        summary = ""
        try:
            json_str = self._extract_json(response_text)
            if json_str:
                data = json.loads(json_str)
                summary = data.get("summary", "")
        except:
            pass

        return ResearchResult(
            query=query,
            results=search_results[:num_results],
            summary=summary,
            confidence=confidence,
        )

    async def research_company(
        self,
        company_name: str,
        website: str,
        industry: str,
    ) -> CompanyResearch:
        """
        Research a specific company's AI/technology initiatives.

        Args:
            company_name: Name of the company
            website: Company website URL
            industry: Industry sector

        Returns:
            CompanyResearch with citations
        """
        logger.info("rag_company_research_started", company=company_name)

        # Research queries for different aspects
        queries = {
            "tech": f"{company_name} technology digital transformation AI initiatives {industry}",
            "news": f"{company_name} AI announcements recent news technology investments",
            "initiatives": f"{company_name} artificial intelligence implementation strategy automation",
        }

        # Run research in parallel
        async def research_category(category: str, query: str) -> tuple[str, list[WebSearchResult]]:
            try:
                result = await self.search_web(query, num_results=5)
                return category, result.results
            except Exception as e:
                logger.warning("company_research_failed", category=category, error=str(e))
                return category, []

        tasks = [research_category(cat, q) for cat, q in queries.items()]
        results = await asyncio.gather(*tasks)

        # Organize results by category
        tech_results = []
        news_results = []
        initiative_results = []

        for category, search_results in results:
            if category == "tech":
                tech_results = search_results
            elif category == "news":
                news_results = search_results
            elif category == "initiatives":
                initiative_results = search_results

        research = CompanyResearch(
            company_name=company_name,
            website_url=website,
            technology_initiatives=tech_results,
            news_mentions=news_results,
            ai_initiatives=initiative_results,
            summary=f"Research on {company_name}: {len(tech_results)} tech findings, "
                    f"{len(news_results)} news items, {len(initiative_results)} AI initiatives.",
        )

        logger.info(
            "rag_company_research_complete",
            company=company_name,
            total_citations=len(research.all_citations),
        )

        return research

    async def research_industry(
        self,
        industry: str,
        pain_point: str,
    ) -> IndustryResearch:
        """
        Research industry AI adoption and trends.

        Args:
            industry: Industry sector
            pain_point: Specific challenge to research

        Returns:
            IndustryResearch with citations
        """
        logger.info("rag_industry_research_started", industry=industry)

        # Targeted queries
        queries = {
            "stats": f"{industry} AI adoption statistics McKinsey Gartner Deloitte percentages",
            "trends": f"{industry} digital transformation AI trends forecast market growth",
            "competitors": f"{industry} companies AI implementation examples leading companies",
            "adoption": f"{industry} AI {pain_point} ROI results case studies metrics",
        }

        # Run research in parallel
        async def research_category(category: str, query: str) -> tuple[str, list[WebSearchResult]]:
            try:
                result = await self.search_web(query, num_results=5)
                return category, result.results
            except Exception as e:
                logger.warning("industry_research_failed", category=category, error=str(e))
                return category, []

        tasks = [research_category(cat, q) for cat, q in queries.items()]
        results = await asyncio.gather(*tasks)

        # Organize results
        stats_results = []
        trends_results = []
        competitor_results = []
        adoption_results = []

        for category, search_results in results:
            if category == "stats":
                stats_results = search_results
            elif category == "trends":
                trends_results = search_results
            elif category == "competitors":
                competitor_results = search_results
            elif category == "adoption":
                adoption_results = search_results

        research = IndustryResearch(
            industry=industry,
            statistics=stats_results,
            trends=trends_results,
            competitor_initiatives=competitor_results,
            adoption_data=adoption_results,
            summary=f"Industry research for {industry}: {len(stats_results)} statistics, "
                    f"{len(trends_results)} trends, {len(competitor_results)} competitors, "
                    f"{len(adoption_results)} adoption examples.",
        )

        logger.info(
            "rag_industry_research_complete",
            industry=industry,
            total_citations=len(research.all_citations),
        )

        return research

    async def research_case_studies(
        self,
        industry: str,
        pain_point: str,
        company_size: str,
    ) -> CaseStudyResearch:
        """
        Research relevant AI case studies with ROI data.

        Args:
            industry: Industry sector
            pain_point: Specific challenge
            company_size: Company size for relevance

        Returns:
            CaseStudyResearch with citations
        """
        logger.info("rag_case_study_research_started", industry=industry)

        # Targeted queries for case studies
        queries = {
            "cases": f"{industry} AI case study results ROI {pain_point} success story real companies",
            "roi": f"{industry} AI implementation ROI savings metrics percentage documented results",
            "guides": f"{industry} AI implementation guide best practices {company_size} enterprise",
        }

        # Run research in parallel
        async def research_category(category: str, query: str) -> tuple[str, list[WebSearchResult]]:
            try:
                num = 8 if category == "cases" else 5
                result = await self.search_web(query, num_results=num)
                return category, result.results
            except Exception as e:
                logger.warning("case_study_research_failed", category=category, error=str(e))
                return category, []

        tasks = [research_category(cat, q) for cat, q in queries.items()]
        results = await asyncio.gather(*tasks)

        # Organize results
        case_results = []
        roi_results = []
        guide_results = []

        for category, search_results in results:
            if category == "cases":
                case_results = search_results
            elif category == "roi":
                roi_results = search_results
            elif category == "guides":
                guide_results = search_results

        research = CaseStudyResearch(
            industry=industry,
            pain_point=pain_point,
            case_studies=case_results,
            roi_data=roi_results,
            implementation_guides=guide_results,
            summary=f"Case study research: {len(case_results)} case studies, "
                    f"{len(roi_results)} ROI data points, {len(guide_results)} implementation guides.",
        )

        logger.info(
            "rag_case_study_research_complete",
            industry=industry,
            total_citations=len(research.all_citations),
        )

        return research


# Async wrapper for use in existing agent pattern
class AsyncRAGOrchestrator:
    """
    Async-compatible RAG Orchestrator wrapper.

    Provides the same interface as RAGOrchestrator for compatibility.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._rag = RAGOrchestrator(api_key=api_key, model=model)

    async def search(
        self,
        query: str,
        num_results: int = 10,
    ) -> list[WebSearchResult]:
        """Search and return results."""
        result = await self._rag.search_web(query, num_results)
        return result.results

    async def research_company(
        self,
        company_name: str,
        website: str,
        industry: str,
    ) -> CompanyResearch:
        """Research a company."""
        return await self._rag.research_company(company_name, website, industry)

    async def research_industry(
        self,
        industry: str,
        pain_point: str,
    ) -> IndustryResearch:
        """Research an industry."""
        return await self._rag.research_industry(industry, pain_point)

    async def research_case_studies(
        self,
        industry: str,
        pain_point: str,
        company_size: str,
    ) -> CaseStudyResearch:
        """Research case studies."""
        return await self._rag.research_case_studies(industry, pain_point, company_size)
