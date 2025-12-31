"""
Priority Analyzer for AI Readiness Compass.

Identifies top 3 business priorities and recommends ONE solution per priority,
plus 2-3 anti-recommendations ("what to avoid").
"""

import structlog
from typing import Protocol, runtime_checkable

from contexts.compass.models import (
    CompassRequest,
    AIReadinessScore,
    BusinessPriority,
    AISolution,
    AntiRecommendation,
    RoadmapPhase,
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


PRIORITY_ANALYZER_SYSTEM = """You are a Strategic AI Consultant creating a focused implementation plan.

Your task is to analyze the business context and create a PREMIUM strategic plan that includes:
1. Top 3 Business Priorities - the most impactful problems AI can solve
2. ONE focused solution per priority - matched to their AI readiness level
3. 2-3 Anti-Recommendations - "tempting but wrong" solutions they should AVOID
4. 90-Day Implementation Roadmap - month-by-month action plan

CRITICAL RULES:
- Each priority gets exactly ONE solution (not multiple options)
- Solutions must match their AI Readiness Score level
- Anti-recommendations show expertise ("we know what NOT to do")
- Roadmap must be actionable with specific decision gates

SOLUTION TYPES (choose appropriately):
- RAG: Knowledge bases, document Q&A, search enhancement
- Agentic: Autonomous workflows, multi-agent systems
- n8n/Automation: Workflow orchestration, integrations
- Adapter: API connectors, system integrations
- Open Source: Self-hosted solutions, open tools

OUTPUT FORMAT (JSON):
{
    "priorities": [
        {
            "rank": 1,
            "problem_name": "Clear problem name",
            "problem_description": "Why this matters to their business",
            "solution": {
                "name": "Specific solution name",
                "approach_type": "RAG|Agentic|n8n|Adapter|OpenSource",
                "description": "What it does and how",
                "why_this_fits": "Given your readiness score of X, this approach...",
                "tools": ["Tool1", "Tool2"],
                "expected_impact": "Quantified impact (e.g., 40% reduction)",
                "complexity": "Low|Medium|High"
            }
        }
    ],
    "avoid": [
        {
            "name": "Solution name to avoid",
            "why_tempting": "Why it seems attractive",
            "why_wrong_for_them": "Why it's wrong at their readiness level"
        }
    ],
    "roadmap": [
        {
            "month": 1,
            "focus": "Quick Win",
            "actions": ["Action 1", "Action 2", "Action 3"],
            "decision_gate": "Criteria to proceed"
        },
        {
            "month": 2,
            "focus": "Foundation",
            "actions": ["Action 1", "Action 2", "Action 3"],
            "decision_gate": "Criteria to proceed"
        },
        {
            "month": 3,
            "focus": "Scale or Iterate",
            "actions": ["Action 1", "Action 2", "Action 3"],
            "decision_gate": "Success criteria"
        }
    ]
}
"""


class PriorityAnalyzer:
    """
    Analyzes business context to identify priorities and recommend solutions.

    Creates the core content for the AI Readiness Compass report:
    - 3 Business Priorities with focused solutions
    - Anti-recommendations for credibility
    - 90-day implementation roadmap
    """

    def __init__(self, ai_provider: AIProvider):
        self._ai = ai_provider

    async def analyze(
        self,
        request: CompassRequest,
        research_insights: dict,
        ai_readiness: AIReadinessScore,
    ) -> tuple[list[BusinessPriority], list[AntiRecommendation], list[RoadmapPhase]]:
        """
        Analyze business and create strategic recommendations.

        Args:
            request: Original compass request with company info
            research_insights: Aggregated research from all agents
            ai_readiness: Calculated AI Readiness Score

        Returns:
            Tuple of (priorities, anti_recommendations, roadmap)
        """
        logger.info(
            "priority_analysis_started",
            company_name=request.company_name,
            readiness_score=ai_readiness.overall_score,
        )

        prompt = self._build_prompt(request, research_insights, ai_readiness)

        try:
            result = await self._ai.generate_json(
                prompt=prompt,
                system_prompt=PRIORITY_ANALYZER_SYSTEM,
                max_tokens=4096,
            )

            priorities = self._parse_priorities(result.get("priorities", []))
            avoid = self._parse_anti_recommendations(result.get("avoid", []))
            roadmap = self._parse_roadmap(result.get("roadmap", []))

            logger.info(
                "priority_analysis_completed",
                company_name=request.company_name,
                priority_count=len(priorities),
                anti_count=len(avoid),
            )

            return priorities, avoid, roadmap

        except Exception as e:
            logger.error(
                "priority_analysis_failed",
                company_name=request.company_name,
                error=str(e),
            )
            # Return sensible defaults on failure
            return self._get_default_analysis(request, ai_readiness)

    def _build_prompt(
        self,
        request: CompassRequest,
        research: dict,
        score: AIReadinessScore,
    ) -> str:
        """Build the analysis prompt with all context."""
        return f"""Create a strategic AI implementation plan for this company:

COMPANY CONTEXT:
- Company: {request.company_name}
- Industry: {request.industry}
- Size: {request.company_size}
- Website: {request.website or "Not provided"}

AI READINESS ASSESSMENT:
- Overall Score: {score.overall_score:.0f}/100
- Self-Assessment Score: {score.self_assessment_score:.0f}/100
- Research Score: {score.research_score:.0f}/100
- Readiness Level: {self._get_readiness_level(score.overall_score)}

THEIR PRIMARY CHALLENGE:
{request.pain_point}

DETAILED DESCRIPTION:
{request.description}

RESEARCH INSIGHTS:
{self._format_research(research)}

Based on this analysis, provide:
1. Top 3 business priorities where AI can have the most impact
2. ONE focused solution per priority (matched to their readiness level)
3. 2-3 solutions they should AVOID at their current readiness level
4. A 90-day implementation roadmap with decision gates

Remember: Lower readiness = simpler solutions. Higher readiness = more advanced options."""

    def _format_research(self, research: dict) -> str:
        """Format research insights for the prompt."""
        if not research:
            return "No research data available"

        sections = []

        if "company" in research:
            company = research["company"]
            sections.append(f"""Company Analysis:
- Tech Signals: {', '.join(company.get('tech_signals', [])[:3])}
- Key Findings: {', '.join(company.get('key_findings', [])[:3])}
- AI Opportunities: {', '.join(company.get('ai_opportunities', [])[:3])}""")

        if "industry" in research:
            industry = research["industry"]
            sections.append(f"""Industry Context:
- AI Maturity: {industry.get('ai_maturity', 'Unknown')}
- Common Use Cases: {', '.join(industry.get('common_use_cases', [])[:3])}
- Competitor Adoption: {industry.get('competitor_adoption', 'Unknown')}""")

        if "whitepaper" in research:
            wp = research["whitepaper"]
            sections.append(f"""Best Practices:
- Recommended Timeline: {wp.get('timeline', 'Unknown')}
- Success Factors: {', '.join(wp.get('success_factors', [])[:3])}
- Common Pitfalls: {', '.join(wp.get('pitfalls', [])[:3])}""")

        return "\n\n".join(sections) if sections else "Research data available"

    def _get_readiness_level(self, score: float) -> str:
        """Convert score to readiness level."""
        if score <= 30:
            return "Beginner (focus on simple, proven solutions)"
        elif score <= 50:
            return "Developing (build foundations, avoid complexity)"
        elif score <= 70:
            return "Established (ready for moderate complexity)"
        elif score <= 85:
            return "Advanced (can handle sophisticated solutions)"
        else:
            return "Leading (ready for cutting-edge implementations)"

    def _parse_priorities(self, priorities_data: list) -> list[BusinessPriority]:
        """Parse priorities from AI response."""
        priorities = []

        for p in priorities_data[:3]:  # Max 3 priorities
            if not isinstance(p, dict):
                continue

            solution_data = p.get("solution", {})
            solution = AISolution(
                name=solution_data.get("name", "AI Solution"),
                approach_type=solution_data.get("approach_type", "Automation"),
                description=solution_data.get("description", ""),
                why_this_fits=solution_data.get("why_this_fits", ""),
                tools=solution_data.get("tools", []),
                expected_impact=solution_data.get("expected_impact", "Efficiency improvement"),
                complexity=solution_data.get("complexity", "Medium"),
            )

            priority = BusinessPriority(
                rank=p.get("rank", len(priorities) + 1),
                problem_name=p.get("problem_name", "Business Priority"),
                problem_description=p.get("problem_description", ""),
                solution=solution,
            )
            priorities.append(priority)

        return priorities

    def _parse_anti_recommendations(self, avoid_data: list) -> list[AntiRecommendation]:
        """Parse anti-recommendations from AI response."""
        anti_recs = []

        for a in avoid_data[:3]:  # Max 3 anti-recommendations
            if not isinstance(a, dict):
                continue

            anti = AntiRecommendation(
                name=a.get("name", "Complex Solution"),
                why_tempting=a.get("why_tempting", "Promises quick results"),
                why_wrong_for_them=a.get("why_wrong_for_them", "Requires more preparation"),
            )
            anti_recs.append(anti)

        return anti_recs

    def _parse_roadmap(self, roadmap_data: list) -> list[RoadmapPhase]:
        """Parse roadmap phases from AI response."""
        phases = []

        for r in roadmap_data[:3]:  # Max 3 months
            if not isinstance(r, dict):
                continue

            phase = RoadmapPhase(
                month=r.get("month", len(phases) + 1),
                focus=r.get("focus", f"Month {len(phases) + 1}"),
                actions=r.get("actions", ["Define next steps"]),
                decision_gate=r.get("decision_gate", "Review progress"),
            )
            phases.append(phase)

        return phases

    def _get_default_analysis(
        self,
        request: CompassRequest,
        score: AIReadinessScore,
    ) -> tuple[list[BusinessPriority], list[AntiRecommendation], list[RoadmapPhase]]:
        """Return sensible defaults if AI analysis fails."""
        default_solution = AISolution(
            name="Process Automation Pilot",
            approach_type="n8n",
            description="Start with a focused automation of your most repetitive process",
            why_this_fits=f"At readiness score {score.overall_score:.0f}, starting small builds foundation",
            tools=["n8n", "Zapier", "Make"],
            expected_impact="20-30% time savings on target process",
            complexity="Low",
        )

        priorities = [
            BusinessPriority(
                rank=1,
                problem_name=request.pain_point or "Process Efficiency",
                problem_description="Address your primary challenge with a focused pilot",
                solution=default_solution,
            )
        ]

        avoid = [
            AntiRecommendation(
                name="Full AI Transformation",
                why_tempting="Promises to solve everything at once",
                why_wrong_for_them="Too complex without proven foundation; start small",
            )
        ]

        roadmap = [
            RoadmapPhase(
                month=1,
                focus="Discovery & Quick Win",
                actions=["Identify pilot process", "Set success metrics", "Begin implementation"],
                decision_gate="Pilot process automated and working",
            ),
            RoadmapPhase(
                month=2,
                focus="Measure & Learn",
                actions=["Track metrics", "Gather feedback", "Document learnings"],
                decision_gate="Clear ROI demonstrated",
            ),
            RoadmapPhase(
                month=3,
                focus="Expand or Iterate",
                actions=["Apply learnings", "Plan next automation", "Build team capability"],
                decision_gate="Ready for next phase",
            ),
        ]

        return priorities, avoid, roadmap
