"""
Call 2 Validator - Synthesis Specificity Validation.

Validates that Strategic Synthesis (Call 2) output is specific to the client,
not generic boilerplate, and includes proper research citations.
"""

from __future__ import annotations

import json
from typing import Any

from contexts.compass.models import CompassRequest
from contexts.compass.validators.models import CallQAResult


# Generic tool names that indicate lazy recommendations
GENERIC_TOOLS = frozenset({
    "chatgpt",
    "gpt",
    "copilot",
    "generic ai tool",
    "ai assistant",
    "machine learning",
    "artificial intelligence",
})


class Call2Validator:
    """
    Validates Call 2 (Strategic Synthesis) output for specificity.

    Checks:
    1. Company name mentioned in synthesis
    2. Priorities have research support citations
    3. Minimum number of priorities (3)
    4. Roadmap exists
    5. Tool recommendations are specific, not generic
    """

    # Scoring thresholds
    PASS_THRESHOLD = 7
    MIN_PRIORITIES = 3

    def validate(
        self,
        request: CompassRequest,
        synthesis_output: dict[str, Any],
        call_id: str,
    ) -> CallQAResult:
        """
        Validate synthesis output for specificity.

        Args:
            request: Original client request
            synthesis_output: Call 2 output JSON
            call_id: ID of the API call

        Returns:
            CallQAResult with validation details
        """
        issues: list[str] = []
        recommendations: list[str] = []
        score = 10  # Start perfect, deduct for issues

        # Extract key entities
        company = request.company_name.lower()
        synthesis_text = json.dumps(synthesis_output).lower()

        # Check 1: Company mentioned
        company_mentioned = self._check_company_mention(
            company, synthesis_text, issues, recommendations
        )
        if not company_mentioned:
            score -= 2

        # Check 2: Minimum priorities
        priorities = synthesis_output.get("priorities", [])
        has_enough_priorities = self._check_priority_count(
            priorities, issues, recommendations
        )
        if not has_enough_priorities:
            score -= 2

        # Check 3: Priorities have research citations
        has_citations = self._check_research_citations(
            priorities, issues, recommendations
        )
        if not has_citations:
            score -= 2

        # Check 4: Roadmap exists
        roadmap = synthesis_output.get("roadmap", [])
        has_roadmap = self._check_roadmap(roadmap, issues, recommendations)
        if not has_roadmap:
            score -= 2

        # Check 5: No generic tool recommendations
        generic_count = self._check_generic_tools(
            priorities, issues, recommendations
        )
        if generic_count > 0:
            score -= min(generic_count, 2)  # Max 2 point deduction

        # Determine pass/fail
        score = max(1, score)  # Floor at 1
        passed = score >= self.PASS_THRESHOLD
        is_relevant = company_mentioned
        is_specific = has_citations and generic_count == 0
        is_complete = has_enough_priorities and has_roadmap

        return CallQAResult(
            call_id=call_id,
            call_number=2,
            call_type="Synthesis",
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
        synthesis_text: str,
        issues: list[str],
        recommendations: list[str],
    ) -> bool:
        """Check if company name is mentioned in synthesis."""
        # Check for company name or significant parts
        company_words = [w for w in company.split() if len(w) >= 3]

        if company in synthesis_text:
            return True

        # Check for partial matches (at least half the words)
        matches = sum(1 for w in company_words if w in synthesis_text)
        if matches >= len(company_words) * 0.5:
            return True

        issues.append("Synthesis doesn't mention company name")
        recommendations.append(
            "Add instruction: 'Reference {company_name} specifically in recommendations'"
        )
        return False

    def _check_priority_count(
        self,
        priorities: list[dict],
        issues: list[str],
        recommendations: list[str],
    ) -> bool:
        """Check if there are enough priorities."""
        if len(priorities) >= self.MIN_PRIORITIES:
            return True

        issues.append(f"Only {len(priorities)} priorities (minimum {self.MIN_PRIORITIES})")
        recommendations.append(
            f"Add instruction: 'Provide at least {self.MIN_PRIORITIES} prioritized recommendations'"
        )
        return False

    def _check_research_citations(
        self,
        priorities: list[dict],
        issues: list[str],
        recommendations: list[str],
    ) -> bool:
        """Check if priorities have research support citations."""
        if not priorities:
            return False

        missing_citations = 0
        for i, priority in enumerate(priorities):
            has_support = (
                priority.get("research_support")
                or priority.get("supporting_evidence")
                or priority.get("evidence")
            )
            if not has_support:
                missing_citations += 1

        if missing_citations == 0:
            return True

        issues.append(f"{missing_citations} priorities lack research citations")
        recommendations.append(
            "Add instruction: 'Each priority must cite supporting research from Call 1'"
        )
        return False

    def _check_roadmap(
        self,
        roadmap: list[dict],
        issues: list[str],
        recommendations: list[str],
    ) -> bool:
        """Check if roadmap exists and has content."""
        if roadmap and len(roadmap) >= 1:
            return True

        issues.append("Missing or empty roadmap")
        recommendations.append(
            "Add instruction: 'Include a 90-day implementation roadmap'"
        )
        return False

    def _check_generic_tools(
        self,
        priorities: list[dict],
        issues: list[str],
        recommendations: list[str],
    ) -> int:
        """Check for generic tool recommendations. Returns count of generic tools."""
        generic_found: list[str] = []

        for priority in priorities:
            solution = priority.get("solution", {})

            # Check solution name
            solution_name = solution.get("name", "").lower()
            for generic in GENERIC_TOOLS:
                if generic in solution_name:
                    generic_found.append(solution_name)
                    break

            # Check recommended tools
            tools = solution.get("recommended_tools", [])
            for tool in tools:
                tool_name = tool.get("name", "").lower() if isinstance(tool, dict) else str(tool).lower()
                for generic in GENERIC_TOOLS:
                    if generic in tool_name:
                        generic_found.append(tool_name)
                        break

        if generic_found:
            issues.append(f"Generic tool recommendations: {', '.join(generic_found[:3])}")
            recommendations.append(
                "Add instruction: 'Recommend specific tools (e.g., Claude API, Pinecone) not generic terms'"
            )

        return len(generic_found)
