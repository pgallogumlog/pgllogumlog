"""
Research Quality Gate - HARD blocker for report generation.

This is NOT a soft QA check. This BLOCKS report generation if
requirements are not met.

Principle: No research = No report = No charge

Requirements (ALL must pass):
1. >= 10 verified web sources (HTTP 200)
2. >= 3 unique domains
3. <= 30% NOT_FOUND in required fields
4. >= 1 company-specific finding
5. >= 1 industry statistic with source
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import aiohttp
import structlog

logger = structlog.get_logger()

# Quality gate thresholds - ALL must pass
MIN_VERIFIED_SOURCES = 10
MIN_UNIQUE_DOMAINS = 3
MAX_NOT_FOUND_RATIO = 0.30
URL_VERIFICATION_TIMEOUT = 5  # seconds


@dataclass
class ResearchQualityResult:
    """
    Result of research quality validation.

    If passed=False, report generation MUST be blocked.
    Payment authorization should be cancelled (not captured).
    """

    # Core result
    passed: bool
    verified_source_count: int
    unique_domain_count: int
    not_found_ratio: float

    # Checks
    has_company_data: bool = False
    has_industry_stats: bool = False

    # Issues (if any)
    issues: list[str] = field(default_factory=list)

    # When failed, cancel authorization (no charge, no refund needed)
    should_cancel_authorization: bool = False

    # Metadata
    total_citations: int = 0
    verification_duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_sheets_row(self) -> list[Any]:
        """
        Convert to row for logging.

        Columns:
        Timestamp, Passed, Verified Sources, Unique Domains,
        NOT_FOUND Ratio, Has Company Data, Has Industry Stats,
        Total Citations, Verification Duration (ms), Issues
        """
        return [
            self.timestamp.isoformat(),
            "PASS" if self.passed else "FAIL",
            self.verified_source_count,
            self.unique_domain_count,
            f"{self.not_found_ratio:.1%}",
            "TRUE" if self.has_company_data else "FALSE",
            "TRUE" if self.has_industry_stats else "FALSE",
            self.total_citations,
            round(self.verification_duration_ms, 1),
            "; ".join(self.issues[:5]) if self.issues else "",
        ]

    @staticmethod
    def get_headers() -> list[str]:
        """Get column headers."""
        return [
            "Timestamp",
            "Passed",
            "Verified Sources",
            "Unique Domains",
            "NOT_FOUND Ratio",
            "Has Company Data",
            "Has Industry Stats",
            "Total Citations",
            "Verification Duration (ms)",
            "Issues",
        ]


class ResearchFailedError(Exception):
    """
    Research quality gate failed - cancel payment authorization.

    When raised, the engine MUST:
    1. Cancel payment authorization (customer not charged)
    2. Send failure notification email
    3. NOT deliver any report
    """

    def __init__(self, issues: list[str]):
        self.issues = issues
        self.cancel_authorization = True
        super().__init__(f"Research failed: {'; '.join(issues)}")


class ResearchQualityGate:
    """
    HARD quality gate - blocks report if requirements not met.

    This is the final check before report generation. If validation
    fails, no report is generated and payment is cancelled.

    There is NO graceful degradation. Real research or no report.
    """

    def __init__(
        self,
        min_verified_sources: int = MIN_VERIFIED_SOURCES,
        min_unique_domains: int = MIN_UNIQUE_DOMAINS,
        max_not_found_ratio: float = MAX_NOT_FOUND_RATIO,
    ):
        """
        Initialize quality gate with thresholds.

        Args:
            min_verified_sources: Minimum URLs that must return HTTP 200
            min_unique_domains: Minimum unique domains in citations
            max_not_found_ratio: Maximum ratio of NOT_FOUND fields
        """
        self._min_verified = min_verified_sources
        self._min_domains = min_unique_domains
        self._max_not_found = max_not_found_ratio

    async def validate(
        self,
        research_findings: dict,
        citations: list[dict],
        company_name: str,
        industry: str,
    ) -> ResearchQualityResult:
        """
        Validate research quality. BLOCKS if any check fails.

        Args:
            research_findings: Output from Call 1 (deep research)
            citations: List of web search citations with URLs
            company_name: Company being researched
            industry: Industry being researched

        Returns:
            ResearchQualityResult with pass/fail and issues
        """
        start_time = datetime.now()
        issues: list[str] = []

        logger.info(
            "research_quality_gate_started",
            company_name=company_name,
            industry=industry,
            citation_count=len(citations),
        )

        # Check 1: Verify citations via HTTP HEAD
        verified_count = await self._verify_citations(citations)
        if verified_count < self._min_verified:
            issues.append(
                f"INSUFFICIENT SOURCES: {verified_count}/{self._min_verified} verified"
            )

        # Check 2: Domain diversity
        unique_domains = self._count_unique_domains(citations)
        if unique_domains < self._min_domains:
            issues.append(f"LOW DIVERSITY: Only {unique_domains} unique domains")

        # Check 3: NOT_FOUND ratio
        not_found_ratio = self._calculate_not_found_ratio(research_findings)
        if not_found_ratio > self._max_not_found:
            issues.append(f"HIGH DATA GAPS: {not_found_ratio:.0%} NOT_FOUND")

        # Check 4: Company-specific findings
        has_company = self._has_company_findings(research_findings, company_name)
        if not has_company:
            issues.append(f"NO COMPANY DATA: Nothing found about {company_name}")

        # Check 5: Industry statistics
        has_industry = self._has_industry_stats(research_findings, industry)
        if not has_industry:
            issues.append(f"NO INDUSTRY DATA: No {industry} statistics found")

        # Calculate duration
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        # All checks must pass
        passed = len(issues) == 0

        result = ResearchQualityResult(
            passed=passed,
            verified_source_count=verified_count,
            unique_domain_count=unique_domains,
            not_found_ratio=not_found_ratio,
            has_company_data=has_company,
            has_industry_stats=has_industry,
            issues=issues,
            should_cancel_authorization=not passed,
            total_citations=len(citations),
            verification_duration_ms=duration_ms,
        )

        logger.info(
            "research_quality_gate_completed",
            passed=passed,
            verified_sources=verified_count,
            unique_domains=unique_domains,
            not_found_ratio=f"{not_found_ratio:.1%}",
            has_company_data=has_company,
            has_industry_stats=has_industry,
            issue_count=len(issues),
            duration_ms=round(duration_ms, 1),
        )

        return result

    async def _verify_citations(self, citations: list[dict]) -> int:
        """
        Verify citations via HTTP HEAD requests.

        Returns count of URLs that return HTTP status < 400.
        """
        if not citations:
            return 0

        verified = 0

        async def check_url(url: str) -> bool:
            """Check if URL is accessible."""
            if not url or not url.startswith(("http://", "https://")):
                return False
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.head(
                        url,
                        timeout=aiohttp.ClientTimeout(total=URL_VERIFICATION_TIMEOUT),
                        allow_redirects=True,
                    ) as resp:
                        return resp.status < 400
            except Exception:
                return False

        # Run URL checks in parallel with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(10)

        async def check_with_limit(url: str) -> bool:
            async with semaphore:
                return await check_url(url)

        tasks = [check_with_limit(c.get("url", "")) for c in citations]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if result is True:
                verified += 1

        return verified

    def _count_unique_domains(self, citations: list[dict]) -> int:
        """Count unique domains in citations."""
        domains = set()
        for c in citations:
            url = c.get("url", "")
            if url:
                try:
                    parsed = urlparse(url)
                    if parsed.netloc:
                        # Extract base domain (e.g., "example.com" from "www.example.com")
                        domain_parts = parsed.netloc.split(".")
                        if len(domain_parts) >= 2:
                            base_domain = ".".join(domain_parts[-2:])
                            domains.add(base_domain.lower())
                except Exception:
                    pass
        return len(domains)

    def _calculate_not_found_ratio(self, research_findings: dict) -> float:
        """
        Calculate ratio of NOT_FOUND values in research findings.

        Checks for common patterns indicating missing data:
        - "Not Found"
        - "NOT_FOUND"
        - "No data"
        - "Unable to find"
        - Empty strings
        - None values
        """
        if not research_findings:
            return 1.0

        not_found_patterns = [
            r"not[\s_]*found",  # Matches "not found", "notfound", "NOT_FOUND"
            r"no[\s_]*data",
            r"unable[\s_]*to[\s_]*find",
            r"not[\s_]*available",
            r"n/a",
        ]
        combined_pattern = re.compile("|".join(not_found_patterns), re.IGNORECASE)

        total_fields = 0
        not_found_count = 0

        def check_value(value: Any) -> tuple[int, int]:
            """Check a value for NOT_FOUND. Returns (total, not_found)."""
            if value is None:
                return (1, 1)
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return (1, 1)
                if combined_pattern.search(value):
                    return (1, 1)
                return (1, 0)
            if isinstance(value, dict):
                t, n = 0, 0
                for v in value.values():
                    sub_t, sub_n = check_value(v)
                    t += sub_t
                    n += sub_n
                return (t, n)
            if isinstance(value, list):
                if not value:
                    return (1, 1)
                t, n = 0, 0
                for v in value:
                    sub_t, sub_n = check_value(v)
                    t += sub_t
                    n += sub_n
                return (t, n)
            return (1, 0)

        # Check all values in research findings
        total_fields, not_found_count = check_value(research_findings)

        if total_fields == 0:
            return 1.0
        return not_found_count / total_fields

    def _has_company_findings(
        self, research_findings: dict, company_name: str
    ) -> bool:
        """
        Check if research has company-specific findings.

        Looks for company name mentioned in actual data (not just prompts).
        """
        if not research_findings or not company_name:
            return False

        company_lower = company_name.lower()

        def search_for_company(value: Any) -> bool:
            """Recursively search for company name in value."""
            if isinstance(value, str):
                return company_lower in value.lower()
            if isinstance(value, dict):
                for v in value.values():
                    if search_for_company(v):
                        return True
            if isinstance(value, list):
                for v in value:
                    if search_for_company(v):
                        return True
            return False

        # Skip metadata keys and look for actual company data
        skip_keys = {"_citations", "research_metadata", "meta", "metadata"}
        for key, value in research_findings.items():
            if key.lower() not in skip_keys:
                if search_for_company(value):
                    return True

        return False

    def _has_industry_stats(
        self, research_findings: dict, industry: str
    ) -> bool:
        """
        Check if research has industry statistics.

        Looks for percentage, dollar amounts, or numerical data
        related to the industry.
        """
        if not research_findings or not industry:
            return False

        industry_lower = industry.lower()
        stat_patterns = [
            r"\d+%",  # Percentages
            r"\$[\d,]+",  # Dollar amounts
            r"\d+\.\d+\s*(?:billion|million|trillion)",  # Large numbers
            r"(?:increased|decreased|grew|declined)\s*by\s*\d+",  # Growth metrics
        ]
        combined_stat_pattern = re.compile("|".join(stat_patterns), re.IGNORECASE)

        def has_stats_and_industry(value: Any) -> bool:
            """Check if value contains both industry mention and statistics."""
            if isinstance(value, str):
                has_industry = industry_lower in value.lower()
                has_stat = bool(combined_stat_pattern.search(value))
                return has_industry and has_stat
            if isinstance(value, dict):
                for v in value.values():
                    if has_stats_and_industry(v):
                        return True
            if isinstance(value, list):
                for v in value:
                    if has_stats_and_industry(v):
                        return True
            return False

        return has_stats_and_industry(research_findings)
