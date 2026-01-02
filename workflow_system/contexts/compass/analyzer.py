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


PRIORITY_ANALYZER_SYSTEM = """You are a Strategic AI Consultant creating a PREMIUM implementation plan worth $1,000+.

Your task is to analyze the business context and create an EXCEPTIONALLY SPECIFIC strategic plan that includes:
1. Top 3 Business Priorities - the most impactful problems AI can solve
2. ONE focused solution per priority with SPECIFIC VENDOR RECOMMENDATIONS and PRICING
3. 2-3 Anti-Recommendations - "tempting but wrong" solutions they should AVOID
4. 90-Day Implementation Roadmap - month-by-month action plan with SPECIFIC DELIVERABLES

CRITICAL PREMIUM VALUE RULES:
- Name SPECIFIC PRODUCTS and VENDORS (not generic categories)
- Include ACTUAL PRICING or pricing ranges where possible
- Cite REAL INTEGRATIONS the solution offers
- Reference the RESEARCH DATA provided
- Solutions must match their AI Readiness Score level

SOLUTION VENDOR EXAMPLES (use these or similar real products):
LOW READINESS (Score < 40):
- Zapier ($20-50/mo), Make.com ($9-29/mo) - simple workflow automation
- HubSpot Free CRM - basic data centralization
- Notion AI ($10/user/mo) - knowledge management lite
- Typeform + Zapier - smart form routing

MEDIUM READINESS (Score 40-70):
- Microsoft Copilot ($30/user/mo) - enterprise AI assistant
- Intercom Fin ($0.99/resolution) - AI customer support
- Gong.io ($100-300/user/mo) - sales intelligence
- Salesforce Einstein - CRM AI layer
- Pinecone + LangChain - custom RAG solutions

HIGH READINESS (Score > 70):
- Azure OpenAI Service - enterprise LLM deployment
- Anthropic Claude API - custom AI applications
- Glean ($20/user/mo) - enterprise search AI
- Moveworks - IT automation platform
- Custom multi-agent systems with Claude/GPT-4

OUTPUT FORMAT (JSON):
{
    "priorities": [
        {
            "rank": 1,
            "problem_name": "Clear problem name",
            "problem_description": "Why this matters to their business - cite research data",
            "solution": {
                "name": "SPECIFIC Product Name (e.g., 'Intercom Fin AI Bot')",
                "vendor": "Company name",
                "approach_type": "RAG|Agentic|Automation|Integration|Platform",
                "description": "Exactly what it does and how it solves their problem",
                "why_this_fits": "Given your readiness score of X and research showing Y, this approach...",
                "specific_features": ["Feature 1 that addresses their pain", "Feature 2"],
                "integrations": ["System they already use 1", "System 2"],
                "pricing": {
                    "model": "per_user|per_usage|flat_rate",
                    "estimated_monthly": "$X-$Y/month",
                    "implementation_cost": "$X one-time (if applicable)"
                },
                "expected_impact": "Quantified impact with timeline (e.g., '40% ticket reduction in 60 days')",
                "complexity": "Low|Medium|High",
                "time_to_value": "X weeks/months"
            }
        }
    ],
    "avoid": [
        {
            "name": "Specific solution to avoid (e.g., 'Custom LLM Fine-tuning')",
            "vendor_examples": ["Vendors that offer this"],
            "why_tempting": "Why it seems attractive",
            "why_wrong_for_them": "Why it's wrong at their readiness level - cite research",
            "cost_of_mistake": "What they'd waste in time/money"
        }
    ],
    "roadmap": [
        {
            "month": 1,
            "focus": "Quick Win - [Specific Goal]",
            "specific_deliverables": ["Deliverable 1 with metric", "Deliverable 2"],
            "tools_to_implement": ["Tool 1", "Tool 2"],
            "budget": "$X",
            "decision_gate": "Specific metric to hit before proceeding"
        },
        {
            "month": 2,
            "focus": "Foundation - [Specific Goal]",
            "specific_deliverables": ["Deliverable 1", "Deliverable 2"],
            "tools_to_implement": ["Tool 1"],
            "budget": "$X",
            "decision_gate": "Specific metric"
        },
        {
            "month": 3,
            "focus": "Scale - [Specific Goal]",
            "specific_deliverables": ["Deliverable 1", "Deliverable 2"],
            "tools_to_implement": ["Tool 1"],
            "budget": "$X",
            "decision_gate": "Success criteria for continuing"
        }
    ],
    "total_90_day_budget": "$X-$Y range",
    "expected_roi": "X% or $X savings/gains based on research benchmarks"
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
        """Format ENHANCED research insights for the prompt."""
        if not research:
            return "No research data available"

        sections = []

        if "company" in research:
            company = research["company"]
            tech = company.get('detected_technologies', [])[:5]
            strengths = company.get('digital_strengths', [])[:3]
            gaps = company.get('digital_gaps', [])[:3]
            signals_raw = company.get('positive_ai_signals', [])[:3]
            # Handle both dict format (new API) and string format (old API)
            signals = [s.get('finding', s) if isinstance(s, dict) else s for s in signals_raw]

            sections.append(f"""=== COMPANY ANALYSIS (REAL DATA) ===
- Detected Technologies: {', '.join(tech) if tech else 'None detected'}
- Digital Maturity Score: {company.get('digital_maturity_score', 'N/A')}/10
- Data Infrastructure Score: {company.get('data_infrastructure_score', 'N/A')}/10
- Digital Strengths: {', '.join(strengths) if strengths else 'None identified'}
- Digital Gaps: {', '.join(gaps) if gaps else 'None identified'}
- Positive AI Signals: {', '.join(signals) if signals else 'None found'}
- Executive Summary: {company.get('executive_summary', 'N/A')}""")

        if "industry" in research:
            industry = research["industry"]
            stats = industry.get('key_statistics', [])[:3]
            competitors = industry.get('leading_competitors', [])[:3]
            use_cases = industry.get('proven_use_cases', [])[:3]

            stats_text = "\n".join([f"  - {s.get('stat', '')} (Source: {s.get('source', 'N/A')})" for s in stats]) if stats else "  - No statistics found"
            comp_text = "\n".join([f"  - {c.get('company', '')}: {c.get('initiative', '')}" for c in competitors]) if competitors else "  - No competitor data found"
            uc_text = "\n".join([f"  - {uc.get('use_case', '')}: {uc.get('result', '')} ({uc.get('company', 'unknown')})" for uc in use_cases]) if use_cases else "  - No proven use cases found"

            sections.append(f"""=== INDUSTRY INTELLIGENCE (REAL DATA) ===
- Industry AI Maturity: {industry.get('maturity_level', 'Unknown')}
- Adoption Rate: {industry.get('adoption_rate', 'Not found')}
- Competitive Urgency: {industry.get('competitive_urgency', 'Unknown')}

KEY STATISTICS:
{stats_text}

COMPETITOR AI INITIATIVES:
{comp_text}

PROVEN USE CASES:
{uc_text}

ROI BENCHMARKS:
- Typical ROI: {industry.get('typical_roi', 'Not found')}
- Time to Value: {industry.get('time_to_value', 'Not found')}
- Cost Range: {industry.get('cost_range', 'Not found')}

- Executive Summary: {industry.get('executive_summary', 'N/A')}""")

        if "whitepaper" in research:
            wp = research["whitepaper"]
            case_studies = wp.get('case_studies', [])[:3]
            impl = wp.get('implementation', {})
            vendors = wp.get('vendors', {})

            cs_text = []
            for cs in case_studies:
                cs_text.append(f"""  - {cs.get('company', 'Unknown')}: {cs.get('primary_result', 'Results unknown')}
    Challenge: {cs.get('challenge', 'N/A')}
    Solution: {cs.get('solution', 'N/A')}
    Source: {cs.get('source_url', 'N/A')}""")
            cs_formatted = "\n".join(cs_text) if cs_text else "  - No case studies found"

            sections.append(f"""=== CASE STUDIES & BEST PRACTICES (REAL DATA) ===
RELEVANT CASE STUDIES:
{cs_formatted}

IMPLEMENTATION INSIGHTS:
- Average Timeline: {impl.get('average_timeline', 'Not found')}
- Success Factors: {', '.join(impl.get('success_factors', [])[:3]) or 'None cited'}
- Common Failure Reasons: {', '.join(impl.get('failure_reasons', [])[:3]) or 'None cited'}

BUDGET BENCHMARKS:
- Small Implementation: {impl.get('budget_small', 'Not found')}
- Medium Implementation: {impl.get('budget_medium', 'Not found')}
- Enterprise Implementation: {impl.get('budget_enterprise', 'Not found')}

VENDOR LANDSCAPE:
- Leaders: {', '.join(vendors.get('leaders', [])[:3]) or 'Not identified'}
- Challengers: {', '.join(vendors.get('challengers', [])[:3]) or 'Not identified'}

- Research Confidence: {wp.get('confidence', 'N/A')}%""")

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
        """Parse priorities from AI response with PREMIUM data."""
        priorities = []

        for p in priorities_data[:3]:  # Max 3 priorities
            if not isinstance(p, dict):
                continue

            solution_data = p.get("solution", {})
            pricing_data = solution_data.get("pricing", {})

            # Create pricing object
            from contexts.compass.models import SolutionPricing
            pricing = SolutionPricing(
                model=pricing_data.get("model", ""),
                estimated_monthly=pricing_data.get("estimated_monthly", ""),
                implementation_cost=pricing_data.get("implementation_cost", ""),
            )

            solution = AISolution(
                name=solution_data.get("name", "AI Solution"),
                vendor=solution_data.get("vendor", ""),
                approach_type=solution_data.get("approach_type", "Automation"),
                description=solution_data.get("description", ""),
                why_this_fits=solution_data.get("why_this_fits", ""),
                specific_features=solution_data.get("specific_features", []),
                integrations=solution_data.get("integrations", []),
                tools=solution_data.get("tools", []),
                pricing=pricing,
                expected_impact=solution_data.get("expected_impact", "Efficiency improvement"),
                complexity=solution_data.get("complexity", "Medium"),
                time_to_value=solution_data.get("time_to_value", ""),
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
        """Parse anti-recommendations from AI response with enhanced data."""
        anti_recs = []

        for a in avoid_data[:3]:  # Max 3 anti-recommendations
            if not isinstance(a, dict):
                continue

            anti = AntiRecommendation(
                name=a.get("name", "Complex Solution"),
                vendor_examples=a.get("vendor_examples", []),
                why_tempting=a.get("why_tempting", "Promises quick results"),
                why_wrong_for_them=a.get("why_wrong_for_them", "Requires more preparation"),
                cost_of_mistake=a.get("cost_of_mistake", ""),
            )
            anti_recs.append(anti)

        return anti_recs

    def _parse_roadmap(self, roadmap_data: list) -> list[RoadmapPhase]:
        """Parse roadmap phases from AI response with enhanced data."""
        phases = []

        for r in roadmap_data[:3]:  # Max 3 months
            if not isinstance(r, dict):
                continue

            phase = RoadmapPhase(
                month=r.get("month", len(phases) + 1),
                focus=r.get("focus", f"Month {len(phases) + 1}"),
                actions=r.get("actions", []),
                specific_deliverables=r.get("specific_deliverables", []),
                tools_to_implement=r.get("tools_to_implement", []),
                budget=r.get("budget", ""),
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
