"""
Cross-Call Validator - Integration Validation.

Validates that Call 2 (Strategic Synthesis) actually uses the research
findings from Call 1, detecting when AI ignores provided context.
"""

from __future__ import annotations

import json
import re
from typing import Any

from contexts.compass.validators.models import CrossCallQAResult


class CrossCallValidator:
    """
    Validates that Call 2 synthesis references Call 1 research.

    This is the CRITICAL validator that ensures the synthesis
    actually uses the research findings, not generic responses.

    Checks:
    1. Keywords from research appear in synthesis
    2. Research utilization percentage is above threshold
    3. Priorities have research_support citations
    """

    # Scoring thresholds
    PASS_THRESHOLD = 7
    MIN_RESEARCH_UTILIZATION = 0.30  # 30% of research should be cited

    def validate(
        self,
        research_findings: dict[str, Any],
        synthesis_output: dict[str, Any],
    ) -> CrossCallQAResult:
        """
        Validate that synthesis references research findings.

        Args:
            research_findings: Call 1 output JSON
            synthesis_output: Call 2 output JSON

        Returns:
            CrossCallQAResult with validation details
        """
        issues: list[str] = []
        recommendations: list[str] = []
        score = 10  # Start perfect, deduct for issues

        # Extract all meaningful keywords from research
        research_keywords = self._extract_research_keywords(research_findings)
        research_total = len(research_keywords)

        # If no research, can't validate citations
        if research_total == 0:
            return CrossCallQAResult(
                passed=True,
                score=10,
                call_2_references_call_1=True,
                research_used_count=0,
                research_total_count=0,
                orphaned_findings_count=0,
                issues=[],
                recommendations=[],
            )

        # Convert synthesis to searchable text
        synthesis_text = json.dumps(synthesis_output).lower()

        # Count how many research keywords appear in synthesis
        research_used = sum(
            1 for kw in research_keywords
            if kw in synthesis_text
        )

        # Calculate utilization
        utilization = research_used / research_total if research_total > 0 else 0
        orphaned = research_total - research_used

        # Check 1: Research utilization threshold
        if utilization < self.MIN_RESEARCH_UTILIZATION:
            issues.append(
                f"Low research utilization: only {utilization:.0%} of research findings cited"
            )
            recommendations.append(
                "Add instruction: 'Every priority MUST cite specific findings from the research phase'"
            )
            score -= 4

        # Check 2: Priorities have explicit citations
        priorities = synthesis_output.get("priorities", [])
        missing_citations = self._count_missing_citations(priorities)

        if missing_citations > 0 and len(priorities) > 0:
            citation_ratio = missing_citations / len(priorities)
            if citation_ratio > 0.5:  # More than half missing
                issues.append(
                    f"{missing_citations}/{len(priorities)} priorities lack explicit research citations"
                )
                recommendations.append(
                    "Add instruction: 'Include research_support field for each priority'"
                )
                score -= 3

        # Check 3: Empty synthesis
        if not priorities:
            issues.append("Synthesis has no priorities")
            recommendations.append(
                "Add instruction: 'Generate at least 3 priorities based on research'"
            )
            score -= 3

        # Determine overall status
        score = max(1, score)  # Floor at 1
        passed = score >= self.PASS_THRESHOLD
        call_2_references_call_1 = utilization >= self.MIN_RESEARCH_UTILIZATION

        return CrossCallQAResult(
            passed=passed,
            score=score,
            call_2_references_call_1=call_2_references_call_1,
            research_used_count=research_used,
            research_total_count=research_total,
            orphaned_findings_count=orphaned,
            issues=issues,
            recommendations=recommendations,
        )

    def _extract_research_keywords(
        self, research: dict[str, Any]
    ) -> list[str]:
        """
        Extract meaningful keywords from research findings.

        Extracts multi-word phrases and significant terms that
        should appear in the synthesis if it's using the research.
        """
        keywords: set[str] = set()

        # Convert to text for extraction
        research_text = json.dumps(research)

        # Extract findings, trends, and key phrases
        self._extract_from_section(
            research.get("company_analysis", {}),
            keywords
        )
        self._extract_from_section(
            research.get("industry_intelligence", {}),
            keywords
        )
        self._extract_from_section(
            research.get("implementation_patterns", {}),
            keywords
        )

        # Filter to meaningful keywords (lowercase)
        filtered = [
            kw.lower() for kw in keywords
            if len(kw) >= 4 and not kw.isdigit()
        ]

        return filtered

    def _extract_from_section(
        self,
        section: dict[str, Any],
        keywords: set[str],
    ) -> None:
        """Extract keywords from a research section."""
        if not section:
            return

        for key, value in section.items():
            if isinstance(value, str):
                # Extract significant words from string values
                words = self._extract_significant_words(value)
                keywords.update(words)

            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        words = self._extract_significant_words(item)
                        keywords.update(words)
                    elif isinstance(item, dict):
                        # Recurse into nested dicts
                        for v in item.values():
                            if isinstance(v, str):
                                words = self._extract_significant_words(v)
                                keywords.update(words)

    def _extract_significant_words(self, text: str) -> list[str]:
        """
        Extract significant words/phrases from text.

        Returns words that are meaningful for citation matching.
        """
        # Split on word boundaries
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter out common stop words and short words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "can", "and", "or",
            "but", "for", "with", "from", "about", "into", "through",
            "during", "before", "after", "above", "below", "this", "that",
            "these", "those", "such", "very", "just", "also", "only",
        }

        significant = [
            w for w in words
            if len(w) >= 4 and w not in stop_words
        ]

        return significant

    def _count_missing_citations(self, priorities: list[dict]) -> int:
        """Count priorities that lack explicit research citations."""
        missing = 0

        for priority in priorities:
            has_citation = (
                priority.get("research_support")
                or priority.get("supporting_evidence")
                or priority.get("evidence")
                or priority.get("citations")
            )
            if not has_citation:
                missing += 1

        return missing
