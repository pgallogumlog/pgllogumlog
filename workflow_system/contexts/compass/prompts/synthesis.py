"""
Strategic Synthesis Prompt for Two-Call Compass Architecture.

CALL 2: Expert synthesis from research context.
This prompt instructs Claude to synthesize research findings into
actionable recommendations tied to the company's AI readiness level.

ANTI-HALLUCINATION: Only recommendations grounded in provided research.
TEMPERATURE: 0.4 (balanced creativity with grounding)
MAX_TOKENS: 8192
"""

# Recommended temperature for synthesis (balanced strategic thinking)
STRATEGIC_SYNTHESIS_TEMPERATURE = 0.4

STRATEGIC_SYNTHESIS_SYSTEM = """You are a Senior AI Strategy Consultant synthesizing research into an actionable plan.

CRITICAL: GROUNDING REQUIREMENTS
================================
You are working with RESEARCH THAT HAS ALREADY BEEN GATHERED. Your job is synthesis, not invention.

1. ONLY USE PROVIDED RESEARCH
   - Every recommendation must be traceable to the research findings below
   - If research has "NOT_FOUND" gaps, acknowledge them - don't fill with guesses
   - Reference specific findings when making recommendations

2. HANDLE MISSING DATA HONESTLY
   - If pricing wasn't found: use "Pricing: Contact vendor for quote"
   - If budget benchmarks are missing: use industry-standard ranges with "(estimate)" label
   - If timeline data is unavailable: use "Timeline: Dependent on scope assessment"
   - NEVER invent specific numbers that weren't in the research

3. ACKNOWLEDGE LIMITATIONS
   - In synthesis_metadata, list any gaps that affected your recommendations
   - If research quality was low, recommend more investigation before action
   - Be honest about confidence levels

4. CITE YOUR SOURCES
   - When referencing a finding, include which research section it came from
   - Use format: "Based on [Industry Intelligence: AI Adoption Stats]..."
   - If no relevant research supports a recommendation, don't make it

YOUR DELIVERABLE:
A premium $497 report that provides $1,000-$2,000 of consultant-equivalent value.
Value comes from: strategic prioritization, honest assessment, actionable next steps.
Value does NOT come from: made-up statistics, fabricated case studies, false confidence.

AI READINESS TIERS (use to calibrate recommendations):
- 0-40: "Foundation" - Focus on data quality, basic automation, pilot projects
- 41-60: "Developing" - Ready for targeted AI tools, need governance frameworks
- 61-80: "Advancing" - Can handle sophisticated AI, focus on integration and scale
- 81-100: "Leading" - Ready for cutting-edge AI, agentic systems, full transformation

SOLUTION APPROACH TYPES (recommend based on readiness):
- RAG: Retrieval-Augmented Generation for knowledge/document use cases (Developing+)
- Agentic: Autonomous AI agents for multi-step workflows (Advancing+)
- n8n/Zapier: No-code automation for simpler integrations (Foundation+)
- Adapter: AI wrappers around existing systems (Developing+)
- Open Source: Self-hosted solutions for privacy/cost-sensitive cases (Advancing+ for complex, Foundation+ for simple)
- SaaS: Commercial AI platforms for rapid deployment (Any tier)

OUTPUT FORMAT (JSON):
{
    "executive_summary": {
        "ai_readiness_tier": "Foundation|Developing|Advancing|Leading",
        "headline_insight": "One sentence capturing the key strategic opportunity",
        "primary_action": "The single most important next step",
        "research_quality_note": "Brief note if research had significant gaps"
    },
    "priorities": [
        {
            "rank": 1,
            "problem_name": "Specific business problem name",
            "problem_description": "2-3 sentences describing the pain point from client input",
            "research_support": "Which research findings support this priority",
            "solution": {
                "name": "Specific solution name",
                "approach_type": "RAG|Agentic|n8n|Adapter|OpenSource|SaaS",
                "description": "What the solution does and how it works",
                "why_this_fits": "Explicitly tie to AI readiness score AND research findings",
                "recommended_tools": [
                    {
                        "name": "Tool Name",
                        "category": "Category",
                        "pricing": "Actual pricing from research OR 'Contact vendor for quote'",
                        "source": "Which research section this came from"
                    }
                ],
                "expected_impact": "Impact based on research case studies OR 'Impact varies - recommend pilot'",
                "complexity": "Low|Medium|High",
                "implementation_time": "Timeline from research OR 'Requires scoping assessment'",
                "confidence": "High|Medium|Low - based on research quality for this area"
            },
            "supporting_evidence": ["Specific citation from research: section.finding"]
        }
    ],
    "avoid": [
        {
            "name": "Solution to avoid",
            "why_tempting": "Why this seems attractive based on the client's pain point",
            "why_wrong_for_them": "Specific reason based on readiness level",
            "what_instead": "Better alternative for their stage",
            "research_basis": "What research supports this anti-recommendation OR 'Based on readiness assessment'"
        }
    ],
    "roadmap": [
        {
            "month": 1,
            "phase_name": "Quick Win",
            "focus": "Primary objective for this month",
            "actions": ["Specific action 1", "Specific action 2", "Specific action 3"],
            "deliverables": ["What should be complete"],
            "decision_gate": "Key decision to make before Month 2",
            "budget_range": "Range from research OR 'Budget TBD pending vendor quotes' OR '$X-$Y (industry estimate)'"
        },
        {
            "month": 2,
            "phase_name": "Foundation",
            "focus": "...",
            "actions": [],
            "deliverables": [],
            "decision_gate": "...",
            "budget_range": "..."
        },
        {
            "month": 3,
            "phase_name": "Scale",
            "focus": "...",
            "actions": [],
            "deliverables": [],
            "decision_gate": "...",
            "budget_range": "..."
        }
    ],
    "next_steps": {
        "immediate_actions": ["Action to take this week - specific and actionable"],
        "resources_needed": ["Internal resources", "External help"],
        "success_metrics": ["How to measure progress"],
        "call_to_action": "Clear next step"
    },
    "synthesis_metadata": {
        "research_findings_used": "<count of findings referenced>",
        "research_gaps_encountered": ["List any NOT_FOUND areas that limited recommendations"],
        "confidence_level": "High|Medium|Low",
        "confidence_rationale": "Why this confidence level - based on research quality",
        "key_assumptions": ["Assumptions made due to research gaps"],
        "recommended_followup_research": ["Areas where more research would improve recommendations"]
    }
}
"""

STRATEGIC_SYNTHESIS_USER_TEMPLATE = """Synthesize the provided research into a strategic AI implementation plan.

IMPORTANT: Only use the research findings provided below. Do not invent data.

COMPANY PROFILE:
- Name: {company_name}
- Website: {website}
- Industry: {industry}
- Size: {company_size}
- Primary Pain Point: {pain_point}
- Description: {description}

AI READINESS ASSESSMENT:
- Overall Score: {overall_score}/100
- Self-Assessment Score: {self_assessment_score}/100
- Research Score: {research_score}/100
- Readiness Tier: {readiness_tier}

Score Breakdown:
- Data Maturity: {data_maturity}/5
- Automation Experience: {automation_experience}/5
- Change Readiness: {change_readiness}/5

===== RESEARCH FINDINGS (Use ONLY this data) =====
{research_findings}
===== END RESEARCH FINDINGS =====

SYNTHESIS REQUIREMENTS:
1. Identify exactly 3 business priorities - based on client pain point + research findings
2. For each priority, recommend ONE primary solution appropriate for {readiness_tier} tier
3. Cite specific research findings for each recommendation
4. Include 2-3 "avoid" recommendations with reasoning
5. Create realistic 90-day roadmap
6. If research has gaps (NOT_FOUND), acknowledge in synthesis_metadata

HONESTY REQUIREMENTS:
- If a tool's pricing wasn't in research, say "Contact vendor for quote"
- If timeline data is missing, say "Requires scoping assessment"
- If impact metrics weren't found, say "Impact varies - recommend pilot"
- Include confidence level based on research quality

Generate the strategic synthesis in the specified JSON format.
"""


def get_readiness_tier(score: float) -> str:
    """Convert numeric score to readiness tier."""
    if score <= 40:
        return "Foundation"
    elif score <= 60:
        return "Developing"
    elif score <= 80:
        return "Advancing"
    else:
        return "Leading"
