"""
Web Research Service for AI Readiness Compass.

Provides real web search and website analysis capabilities using multiple APIs.

Also provides research_company, research_industry, research_case_studies methods
for compatibility with the RAGOrchestrator interface expected by compass agents.
"""

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Protocol, runtime_checkable
from urllib.parse import urlparse, urljoin

import httpx
import structlog

logger = structlog.get_logger()

# Timeout for web requests
REQUEST_TIMEOUT = 30.0


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    snippet: str
    source: str = ""


@dataclass
class WebPageContent:
    """Extracted content from a web page."""
    url: str
    title: str
    text_content: str
    meta_description: str = ""
    technologies: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


@dataclass
class CompanyWebPresence:
    """Analyzed web presence of a company."""
    website_content: Optional[WebPageContent]
    careers_content: Optional[WebPageContent]
    tech_stack: list[str]
    digital_signals: list[str]
    social_presence: dict[str, str]


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


class WebResearchService:
    """
    Service for conducting real web research.

    Capabilities:
    - Web search via multiple providers (Tavily, SerpAPI, or fallback)
    - Website content extraction and analysis
    - Technology stack detection
    - Competitive intelligence gathering
    """

    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        serp_api_key: Optional[str] = None,
        ai_provider: Optional[AIProvider] = None,
    ):
        self._tavily_key = tavily_api_key
        self._serp_key = serp_api_key
        self._ai = ai_provider
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "general",
    ) -> list[SearchResult]:
        """
        Search the web for information.

        Args:
            query: Search query
            num_results: Number of results to return
            search_type: Type of search (general, news, academic)

        Returns:
            List of SearchResult objects
        """
        logger.info("web_search_started", query=query[:50], num_results=num_results)

        results = []

        # Try Tavily first (best for AI research)
        if self._tavily_key:
            results = await self._search_tavily(query, num_results)
            if results:
                return results

        # Try SerpAPI as fallback
        if self._serp_key:
            results = await self._search_serp(query, num_results)
            if results:
                return results

        # No API keys - use DuckDuckGo HTML scraping as last resort
        results = await self._search_duckduckgo(query, num_results)

        logger.info("web_search_completed", query=query[:50], result_count=len(results))
        return results

    async def _search_tavily(self, query: str, num_results: int) -> list[SearchResult]:
        """Search using Tavily API."""
        try:
            client = await self._get_client()
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self._tavily_key,
                    "query": query,
                    "max_results": num_results,
                    "search_depth": "advanced",
                    "include_answer": False,
                }
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", "")[:500],
                    source="tavily"
                ))
            return results

        except Exception as e:
            logger.warning("tavily_search_failed", error=str(e))
            return []

    async def _search_serp(self, query: str, num_results: int) -> list[SearchResult]:
        """Search using SerpAPI."""
        try:
            client = await self._get_client()
            response = await client.get(
                "https://serpapi.com/search",
                params={
                    "api_key": self._serp_key,
                    "q": query,
                    "num": num_results,
                    "engine": "google",
                }
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("organic_results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="serpapi"
                ))
            return results

        except Exception as e:
            logger.warning("serp_search_failed", error=str(e))
            return []

    async def _search_duckduckgo(self, query: str, num_results: int) -> list[SearchResult]:
        """Search using DuckDuckGo HTML (no API key needed)."""
        try:
            client = await self._get_client()
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query}
            )
            response.raise_for_status()

            # Parse results from HTML
            results = []
            html = response.text

            # Simple regex extraction for DuckDuckGo results
            # Pattern for result blocks
            result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>.*?<a class="result__snippet"[^>]*>([^<]*)</a>'
            matches = re.findall(result_pattern, html, re.DOTALL)

            for url, title, snippet in matches[:num_results]:
                # DuckDuckGo redirects through their URL
                if "uddg=" in url:
                    actual_url = re.search(r'uddg=([^&]+)', url)
                    if actual_url:
                        from urllib.parse import unquote
                        url = unquote(actual_url.group(1))

                results.append(SearchResult(
                    title=title.strip(),
                    url=url,
                    snippet=snippet.strip(),
                    source="duckduckgo"
                ))

            return results

        except Exception as e:
            logger.warning("duckduckgo_search_failed", error=str(e))
            return []

    async def fetch_webpage(self, url: str) -> WebPageContent:
        """
        Fetch and extract content from a webpage.

        Args:
            url: URL to fetch

        Returns:
            WebPageContent with extracted information
        """
        logger.info("webpage_fetch_started", url=url[:100])

        try:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()

            html = response.text

            # Extract title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else ""

            # Extract meta description
            meta_match = re.search(
                r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
                html, re.IGNORECASE
            )
            meta_desc = meta_match.group(1) if meta_match else ""

            # Extract visible text (simplified)
            # Remove scripts, styles, and HTML tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

            # Detect technologies from HTML
            technologies = self._detect_technologies(html)

            # Extract links
            links = re.findall(r'href=["\']([^"\']+)["\']', html)
            links = [urljoin(url, link) for link in links[:50]]  # Limit to 50 links

            return WebPageContent(
                url=url,
                title=title,
                text_content=text[:10000],  # Limit text length
                meta_description=meta_desc,
                technologies=technologies,
                links=links,
                success=True
            )

        except Exception as e:
            logger.warning("webpage_fetch_failed", url=url[:100], error=str(e))
            return WebPageContent(
                url=url,
                title="",
                text_content="",
                success=False,
                error=str(e)
            )

    def _detect_technologies(self, html: str) -> list[str]:
        """Detect technologies used on a website from HTML."""
        technologies = []

        tech_patterns = {
            "React": [r'react', r'__NEXT_DATA__', r'_next/', r'reactjs'],
            "Angular": [r'ng-app', r'angular', r'ng-controller'],
            "Vue.js": [r'vue\.js', r'v-bind', r'v-model', r'vuejs'],
            "Next.js": [r'__NEXT_DATA__', r'_next/'],
            "WordPress": [r'wp-content', r'wordpress', r'wp-includes'],
            "Shopify": [r'shopify', r'cdn\.shopify'],
            "Salesforce": [r'salesforce', r'force\.com', r'pardot'],
            "HubSpot": [r'hubspot', r'hs-scripts', r'hbspt'],
            "Google Analytics": [r'google-analytics', r'gtag', r'UA-\d+'],
            "Google Tag Manager": [r'googletagmanager', r'GTM-'],
            "Segment": [r'segment\.com', r'analytics\.js'],
            "Intercom": [r'intercom', r'intercomSettings'],
            "Drift": [r'drift\.com', r'driftt'],
            "Zendesk": [r'zendesk', r'zdassets'],
            "Freshdesk": [r'freshdesk', r'freshworks'],
            "Stripe": [r'stripe\.com', r'stripe\.js'],
            "AWS": [r'amazonaws\.com', r'aws-'],
            "Azure": [r'azure', r'microsoft\.com/en-us/azure'],
            "Google Cloud": [r'googleapis\.com', r'google-cloud'],
            "Cloudflare": [r'cloudflare', r'cdnjs\.cloudflare'],
            "Akamai": [r'akamai', r'akam'],
            "jQuery": [r'jquery'],
            "Bootstrap": [r'bootstrap'],
            "Tailwind CSS": [r'tailwind'],
            "Slack Integration": [r'slack\.com', r'slack-'],
            "Microsoft 365": [r'office\.com', r'microsoft365', r'sharepoint'],
            "Zoom": [r'zoom\.us'],
        }

        html_lower = html.lower()
        for tech, patterns in tech_patterns.items():
            for pattern in patterns:
                if re.search(pattern, html_lower):
                    technologies.append(tech)
                    break

        return list(set(technologies))

    async def analyze_company_web_presence(
        self,
        company_name: str,
        website: Optional[str],
    ) -> CompanyWebPresence:
        """
        Comprehensive analysis of a company's web presence.

        Args:
            company_name: Name of the company
            website: Company website URL (optional)

        Returns:
            CompanyWebPresence with analysis results
        """
        logger.info("company_web_analysis_started", company=company_name)

        website_content = None
        careers_content = None
        tech_stack = []
        digital_signals = []
        social_presence = {}

        # Analyze main website
        if website:
            website_content = await self.fetch_webpage(website)
            if website_content.success:
                tech_stack.extend(website_content.technologies)

                # Try to find careers page
                careers_urls = [
                    link for link in website_content.links
                    if any(kw in link.lower() for kw in ['career', 'job', 'hiring', 'work-with-us'])
                ]
                if careers_urls:
                    careers_content = await self.fetch_webpage(careers_urls[0])

        # Search for additional company information
        search_queries = [
            f"{company_name} technology stack",
            f"{company_name} digital transformation",
            f"{company_name} AI initiatives",
        ]

        for query in search_queries:
            results = await self.search(query, num_results=3)
            for result in results:
                digital_signals.append(f"{result.title}: {result.snippet[:200]}")

        # Detect social presence from website links
        if website_content and website_content.links:
            social_patterns = {
                "LinkedIn": r'linkedin\.com',
                "Twitter": r'twitter\.com|x\.com',
                "Facebook": r'facebook\.com',
                "YouTube": r'youtube\.com',
                "GitHub": r'github\.com',
            }
            for platform, pattern in social_patterns.items():
                for link in website_content.links:
                    if re.search(pattern, link):
                        social_presence[platform] = link
                        break

        return CompanyWebPresence(
            website_content=website_content,
            careers_content=careers_content,
            tech_stack=list(set(tech_stack)),
            digital_signals=digital_signals[:10],  # Top 10 signals
            social_presence=social_presence,
        )

    async def search_industry_data(
        self,
        industry: str,
        topic: str = "AI adoption",
    ) -> list[SearchResult]:
        """
        Search for industry-specific data and statistics.

        Args:
            industry: Industry sector
            topic: Specific topic to research

        Returns:
            List of relevant search results
        """
        queries = [
            f"{industry} {topic} statistics 2024",
            f"{industry} {topic} case study",
            f"{industry} {topic} ROI benchmark",
            f"{industry} digital transformation trends 2024",
        ]

        all_results = []
        for query in queries:
            results = await self.search(query, num_results=5)
            all_results.extend(results)

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        return unique_results[:15]  # Top 15 unique results

    async def search_case_studies(
        self,
        industry: str,
        use_case: str,
        company_size: str = "",
    ) -> list[SearchResult]:
        """
        Search for real case studies with citations.

        Args:
            industry: Industry sector
            use_case: AI use case (e.g., "customer service automation")
            company_size: Company size for relevance

        Returns:
            List of case study search results
        """
        queries = [
            f"{industry} AI {use_case} case study success story",
            f"{industry} {use_case} implementation results ROI",
            f"enterprise {use_case} case study {industry}",
        ]

        if company_size:
            queries.append(f"{company_size} company {use_case} AI implementation")

        all_results = []
        for query in queries:
            results = await self.search(query, num_results=5)
            all_results.extend(results)

        # Deduplicate
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        return unique_results[:10]

    async def search_competitors(
        self,
        company_name: str,
        industry: str,
    ) -> list[SearchResult]:
        """
        Search for competitor AI initiatives.

        Args:
            company_name: Name of the company
            industry: Industry sector

        Returns:
            List of competitor-related search results
        """
        queries = [
            f"{industry} top companies AI initiatives 2024",
            f"{industry} leaders digital transformation",
            f"{industry} AI adoption examples",
        ]

        all_results = []
        for query in queries:
            results = await self.search(query, num_results=5)
            all_results.extend(results)

        return all_results[:10]

    # =========================================================================
    # RAGOrchestrator-compatible interface
    # These methods provide the same interface as RAGOrchestrator for use
    # by compass agents that expect research_company, research_industry, etc.
    # =========================================================================

    async def research_company(
        self,
        company_name: str,
        website: str,
        industry: str,
    ) -> "CompanyResearch":
        """
        Research a specific company's AI/technology initiatives.

        Compatible with RAGOrchestrator.research_company() interface.

        Args:
            company_name: Name of the company
            website: Company website URL
            industry: Industry sector

        Returns:
            CompanyResearch with citations
        """
        logger.info("web_research_company_started", company=company_name)

        # Gather company web presence
        web_presence = await self.analyze_company_web_presence(company_name, website)

        # Search for company technology news
        tech_results = await self.search(
            f"{company_name} technology digital transformation AI initiatives",
            num_results=5,
        )

        news_results = await self.search(
            f"{company_name} AI announcements technology investments news",
            num_results=5,
        )

        initiative_results = await self.search(
            f"{company_name} artificial intelligence implementation automation",
            num_results=5,
        )

        # Convert SearchResults to WebSearchResultCompat
        tech_findings = [
            WebSearchResultCompat(
                title=r.title,
                url=r.url,
                snippet=r.snippet,
                source=r.source,
                credibility=self._assess_credibility(r.url),
            )
            for r in tech_results
        ]

        news_findings = [
            WebSearchResultCompat(
                title=r.title,
                url=r.url,
                snippet=r.snippet,
                source=r.source,
                credibility=self._assess_credibility(r.url),
            )
            for r in news_results
        ]

        ai_findings = [
            WebSearchResultCompat(
                title=r.title,
                url=r.url,
                snippet=r.snippet,
                source=r.source,
                credibility=self._assess_credibility(r.url),
            )
            for r in initiative_results
        ]

        research = CompanyResearch(
            company_name=company_name,
            website_url=website,
            technology_initiatives=tech_findings,
            news_mentions=news_findings,
            ai_initiatives=ai_findings,
            summary=f"Research on {company_name}: {len(tech_findings)} tech findings, "
                    f"{len(news_findings)} news items, {len(ai_findings)} AI initiatives.",
        )

        logger.info(
            "web_research_company_complete",
            company=company_name,
            total_citations=len(research.all_citations),
        )

        return research

    async def research_industry(
        self,
        industry: str,
        pain_point: str,
    ) -> "IndustryResearch":
        """
        Research industry AI adoption and trends.

        Compatible with RAGOrchestrator.research_industry() interface.

        Args:
            industry: Industry sector
            pain_point: Specific challenge to research

        Returns:
            IndustryResearch with citations
        """
        logger.info("web_research_industry_started", industry=industry)

        # Search for industry statistics
        stats_results = await self.search(
            f"{industry} AI adoption statistics percentages market research",
            num_results=5,
        )

        trends_results = await self.search(
            f"{industry} digital transformation AI trends forecast",
            num_results=5,
        )

        competitor_results = await self.search(
            f"{industry} companies AI implementation examples leaders",
            num_results=5,
        )

        adoption_results = await self.search(
            f"{industry} AI {pain_point} ROI results case studies",
            num_results=5,
        )

        # Convert to WebSearchResultCompat
        def to_compat(results: list[SearchResult]) -> list[WebSearchResultCompat]:
            return [
                WebSearchResultCompat(
                    title=r.title,
                    url=r.url,
                    snippet=r.snippet,
                    source=r.source,
                    credibility=self._assess_credibility(r.url),
                )
                for r in results
            ]

        research = IndustryResearch(
            industry=industry,
            statistics=to_compat(stats_results),
            trends=to_compat(trends_results),
            competitor_initiatives=to_compat(competitor_results),
            adoption_data=to_compat(adoption_results),
            summary=f"Industry research for {industry}: {len(stats_results)} statistics, "
                    f"{len(trends_results)} trends, {len(competitor_results)} competitors, "
                    f"{len(adoption_results)} adoption examples.",
        )

        logger.info(
            "web_research_industry_complete",
            industry=industry,
            total_citations=len(research.all_citations),
        )

        return research

    async def research_case_studies(
        self,
        industry: str,
        pain_point: str,
        company_size: str,
    ) -> "CaseStudyResearch":
        """
        Research relevant AI case studies with ROI data.

        Compatible with RAGOrchestrator.research_case_studies() interface.

        Args:
            industry: Industry sector
            pain_point: Specific challenge
            company_size: Company size for relevance

        Returns:
            CaseStudyResearch with citations
        """
        logger.info("web_research_case_studies_started", industry=industry)

        # Search for case studies
        case_results = await self.search(
            f"{industry} AI case study results ROI {pain_point} success story",
            num_results=8,
        )

        roi_results = await self.search(
            f"{industry} AI implementation ROI savings metrics percentage",
            num_results=5,
        )

        guide_results = await self.search(
            f"{industry} AI implementation guide best practices {company_size}",
            num_results=5,
        )

        # Convert to WebSearchResultCompat
        def to_compat(results: list[SearchResult]) -> list[WebSearchResultCompat]:
            return [
                WebSearchResultCompat(
                    title=r.title,
                    url=r.url,
                    snippet=r.snippet,
                    source=r.source,
                    credibility=self._assess_credibility(r.url),
                )
                for r in results
            ]

        research = CaseStudyResearch(
            industry=industry,
            pain_point=pain_point,
            case_studies=to_compat(case_results),
            roi_data=to_compat(roi_results),
            implementation_guides=to_compat(guide_results),
            summary=f"Case study research: {len(case_results)} case studies, "
                    f"{len(roi_results)} ROI data points, {len(guide_results)} implementation guides.",
        )

        logger.info(
            "web_research_case_studies_complete",
            industry=industry,
            total_citations=len(research.all_citations),
        )

        return research

    def _assess_credibility(self, url: str) -> str:
        """Assess credibility based on URL domain."""
        url_lower = url.lower()

        high_cred_domains = [
            "mckinsey.com", "gartner.com", "deloitte.com", "accenture.com",
            "pwc.com", "bain.com", "bcg.com", "forrester.com", "idc.com",
            "hbr.org", "mit.edu", "stanford.edu", "harvard.edu",
            "reuters.com", "bloomberg.com", "wsj.com", "ft.com",
        ]

        medium_cred_domains = [
            "forbes.com", "businessinsider.com", "cio.com", "zdnet.com",
            "techcrunch.com", "wired.com", "venturebeat.com",
        ]

        for domain in high_cred_domains:
            if domain in url_lower:
                return "high"
        for domain in medium_cred_domains:
            if domain in url_lower:
                return "medium"
        return "medium"


# =========================================================================
# Dataclasses for RAGOrchestrator compatibility
# These mirror the structures in rag_orchestrator.py
# =========================================================================

@dataclass
class WebSearchResultCompat:
    """A search result compatible with RAGOrchestrator.WebSearchResult."""
    title: str
    url: str
    snippet: str
    source: str = "web_search"
    credibility: str = "medium"
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
class CompanyResearch:
    """Research results specific to a company."""
    company_name: str
    website_url: str
    technology_initiatives: list[WebSearchResultCompat] = field(default_factory=list)
    news_mentions: list[WebSearchResultCompat] = field(default_factory=list)
    ai_initiatives: list[WebSearchResultCompat] = field(default_factory=list)
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
    statistics: list[WebSearchResultCompat] = field(default_factory=list)
    trends: list[WebSearchResultCompat] = field(default_factory=list)
    competitor_initiatives: list[WebSearchResultCompat] = field(default_factory=list)
    adoption_data: list[WebSearchResultCompat] = field(default_factory=list)
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
    case_studies: list[WebSearchResultCompat] = field(default_factory=list)
    roi_data: list[WebSearchResultCompat] = field(default_factory=list)
    implementation_guides: list[WebSearchResultCompat] = field(default_factory=list)
    summary: str = ""

    @property
    def all_citations(self) -> list[dict]:
        """Get all case study citations."""
        citations = []
        for result in self.case_studies + self.roi_data + self.implementation_guides:
            citations.append(result.to_citation())
        return citations
