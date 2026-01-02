"""
Call 1 Validator - Research Relevance Validation.

Validates that Deep Research (Call 1) output is semantically relevant
to the client's company, industry, and pain point.
"""

from __future__ import annotations

import json
import re
from typing import Any

from contexts.compass.models import CompassRequest
from contexts.compass.validators.models import CallQAResult


# Common stop words to exclude from keyword matching
STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "and", "but", "or", "nor", "for", "yet", "so",
    "in", "on", "at", "by", "from", "with", "about", "against", "between",
    "into", "through", "during", "before", "after", "above", "below",
    "of", "up", "down", "out", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all",
    "each", "few", "more", "most", "other", "some", "such", "no", "not",
    "only", "own", "same", "than", "too", "very", "just", "also", "now",
    "our", "we", "us", "they", "them", "their", "this", "that", "these",
    "those", "what", "which", "who", "whom", "it", "its", "i", "me", "my",
    "you", "your", "he", "him", "his", "she", "her", "hers",
})

# Generic phrases that indicate boilerplate
GENERIC_PHRASES = [
    "for example",
    "such as",
    "in general",
    "typically",
    "companies like yours",
    "businesses can benefit",
    "organizations generally",
    "usually",
    "commonly",
    "most companies",
    "many businesses",
]


class Call1Validator:
    """
    Validates Call 1 (Deep Research) output for semantic relevance.

    Checks:
    1. Company name mentioned in research
    2. Industry mentioned in findings
    3. Pain point addressed in research
    4. Research has sufficient depth (metadata checks)
    5. No generic boilerplate responses
    """

    # Scoring thresholds
    PASS_THRESHOLD = 7
    MIN_FINDINGS = 5
    MIN_SOURCES = 3

    def validate(
        self,
        request: CompassRequest,
        research_findings: dict[str, Any],
        call_id: str,
    ) -> CallQAResult:
        """
        Validate research findings for semantic relevance.

        Args:
            request: Original client request
            research_findings: Call 1 output JSON
            call_id: ID of the API call

        Returns:
            CallQAResult with validation details
        """
        issues: list[str] = []
        recommendations: list[str] = []
        score = 10  # Start perfect, deduct for issues

        # Extract key entities from request
        company = request.company_name.lower()
        industry = request.industry.lower()
        pain_point = request.pain_point.lower()

        # Convert research to searchable text
        research_text = json.dumps(research_findings).lower()

        # Check 1: Company mentioned
        company_mentioned = self._check_company_mention(
            company, research_text, issues, recommendations
        )
        if not company_mentioned:
            score -= 2

        # Check 2: Industry mentioned
        industry_mentioned = self._check_industry_mention(
            industry, research_text, issues, recommendations
        )
        if not industry_mentioned:
            score -= 2

        # Check 3: Pain point addressed
        pain_point_addressed = self._check_pain_point(
            pain_point, research_text, issues, recommendations
        )
        if not pain_point_addressed:
            score -= 3

        # Check 4: Metadata quality (depth)
        is_complete = self._check_research_depth(
            research_findings, issues, recommendations
        )
        if not is_complete:
            score -= 2

        # Check 5: Generic response detection
        is_specific = self._check_specificity(
            research_text, company, industry, pain_point, issues, recommendations
        )
        if not is_specific:
            score -= 2

        # Determine pass/fail
        score = max(1, score)  # Floor at 1
        passed = score >= self.PASS_THRESHOLD
        is_relevant = company_mentioned and industry_mentioned

        return CallQAResult(
            call_id=call_id,
            call_number=1,
            call_type="Research",
            passed=passed,
            score=score,
            is_relevant=is_relevant,
            is_specific=is_specific,
            is_complete=is_complete,
            company_name=request.company_name,
            industry=request.industry,
            pain_point=request.pain_point,
            issues=issues,
            recommendations=recommendations,
        )

    def _check_company_mention(
        self,
        company: str,
        research_text: str,
        issues: list[str],
        recommendations: list[str],
    ) -> bool:
        """Check if company name is mentioned in research."""
        # Check for full company name
        if company in research_text:
            return True

        # Check for significant parts of company name (3+ char words)
        company_words = [w for w in company.split() if len(w) >= 3 and w not in STOP_WORDS]
        matches = sum(1 for w in company_words if w in research_text)

        if matches >= len(company_words) * 0.5:  # At least half the words match
            return True

        issues.append(f"Research doesn't mention company name")
        recommendations.append(
            "Add instruction: 'Research MUST specifically reference {company_name}'"
        )
        return False

    def _check_industry_mention(
        self,
        industry: str,
        research_text: str,
        issues: list[str],
        recommendations: list[str],
    ) -> bool:
        """Check if industry is mentioned in research."""
        # Check for exact industry
        if industry in research_text:
            return True

        # Check for industry keywords
        industry_words = [w for w in industry.split() if len(w) >= 3 and w not in STOP_WORDS]
        matches = sum(1 for w in industry_words if w in research_text)

        if matches >= 1:  # At least one industry word matches
            return True

        issues.append(f"Research doesn't mention industry '{industry}'")
        recommendations.append(
            "Add instruction: 'Focus research on {industry} sector specifically'"
        )
        return False

    def _check_pain_point(
        self,
        pain_point: str,
        research_text: str,
        issues: list[str],
        recommendations: list[str],
    ) -> bool:
        """Check if pain point is addressed in research."""
        # Extract meaningful keywords from pain point
        pain_keywords = self._extract_keywords(pain_point)

        if not pain_keywords:
            return True  # Can't validate without keywords

        # Count matches
        matches = sum(1 for kw in pain_keywords if kw in research_text)
        match_ratio = matches / len(pain_keywords)

        if match_ratio >= 0.3:  # At least 30% of keywords match
            return True

        issues.append(f"Research doesn't address pain point: '{pain_point[:50]}...'")
        recommendations.append(
            "Add instruction: 'Research must address the client's specific challenge: {pain_point}'"
        )
        return False

    def _check_research_depth(
        self,
        research_findings: dict[str, Any],
        issues: list[str],
        recommendations: list[str],
    ) -> bool:
        """Check if research has sufficient depth."""
        metadata = research_findings.get("research_metadata", {})
        total_findings = metadata.get("total_findings", 0)
        sources = metadata.get("sources_consulted", 0)

        is_complete = True

        if total_findings < self.MIN_FINDINGS:
            issues.append(f"Insufficient research depth: only {total_findings} findings (minimum {self.MIN_FINDINGS})")
            recommendations.append(
                f"Add instruction: 'Provide at least {self.MIN_FINDINGS} specific findings'"
            )
            is_complete = False

        if sources < self.MIN_SOURCES:
            issues.append(f"Insufficient sources: only {sources} consulted (minimum {self.MIN_SOURCES})")
            recommendations.append(
                f"Add instruction: 'Consult at least {self.MIN_SOURCES} sources'"
            )
            is_complete = False

        # Check for required sections
        if not research_findings.get("company_analysis"):
            issues.append("Missing company_analysis section")
            is_complete = False

        if not research_findings.get("industry_intelligence"):
            issues.append("Missing industry_intelligence section")
            is_complete = False

        return is_complete

    def _check_specificity(
        self,
        research_text: str,
        company: str,
        industry: str,
        pain_point: str,
        issues: list[str],
        recommendations: list[str],
    ) -> bool:
        """Check if research is specific vs generic boilerplate."""
        # Count generic phrases
        generic_count = sum(
            1 for phrase in GENERIC_PHRASES
            if phrase in research_text
        )

        # Count specific references
        specific_count = 0
        if company in research_text:
            specific_count += 2
        if industry in research_text:
            specific_count += 1

        pain_keywords = self._extract_keywords(pain_point)
        specific_count += sum(1 for kw in pain_keywords if kw in research_text)

        # If generic phrases outweigh specific references, it's boilerplate
        if generic_count > specific_count and generic_count >= 3:
            issues.append(
                f"Research appears generic: {generic_count} generic phrases vs {specific_count} specific references"
            )
            recommendations.append(
                "Add instruction: 'Avoid generic advice. All findings must be specific to {company_name} context'"
            )
            return False

        return True

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract meaningful keywords from text."""
        # Split on non-word characters
        words = re.findall(r'\w+', text.lower())

        # Filter out stop words and short words
        keywords = [
            w for w in words
            if len(w) >= 3 and w not in STOP_WORDS
        ]

        return list(set(keywords))  # Deduplicate
