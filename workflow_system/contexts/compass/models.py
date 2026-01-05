"""
Domain models for AI Readiness Compass.

Premium $497 strategic report with:
- AI Readiness Score (hybrid: 30% self-assessment + 70% AI research)
- Top 3 Business Priorities with focused solutions
- 90-Day Implementation Roadmap
- Anti-recommendations (what to avoid)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class SelfAssessment:
    """
    User's self-assessment for 30% of AI Readiness Score.

    Each field is rated 1-5:
    - 1: Not started / Very low
    - 2: Early stage / Low
    - 3: Developing / Medium
    - 4: Established / High
    - 5: Advanced / Very high
    """
    data_maturity: int  # How structured and accessible is business data?
    automation_experience: int  # Current level of automation adoption
    change_readiness: int  # Organization's ability to adopt new technology


@dataclass
class AIReadinessScore:
    """
    Hybrid AI Readiness Score.

    Formula: overall = (self_assessment * 0.30) + (research * 0.70)
    """
    self_assessment_score: float  # 0-100, from user's self-assessment
    research_score: float  # 0-100, from AI website/industry analysis
    overall_score: float  # 0-100, weighted combination
    breakdown: dict[str, float]  # Component-level breakdown


@dataclass
class CompassRequest:
    """
    Complete submission for AI Readiness Compass report.

    Combines business context + self-assessment for personalized analysis.
    """
    company_name: str
    website: str
    industry: str
    company_size: str
    self_assessment: SelfAssessment
    pain_point: str
    description: str
    email: str
    contact_name: str


@dataclass
class SolutionPricing:
    """Pricing information for a solution."""
    model: str = ""  # per_user, per_usage, flat_rate
    estimated_monthly: str = ""  # e.g., "$500-$1,500/month"
    implementation_cost: str = ""  # e.g., "$5,000 one-time"


@dataclass
class AISolution:
    """
    A PREMIUM specific AI solution recommendation for a business priority.

    UPGRADED: Now includes SPECIFIC VENDOR names, PRICING, and INTEGRATIONS.
    Each priority gets ONE primary solution matched to readiness level.
    """
    name: str  # e.g., "Intercom Fin AI Bot" (SPECIFIC PRODUCT NAME)
    vendor: str = ""  # e.g., "Intercom" (SPECIFIC VENDOR)
    approach_type: str = ""  # RAG, Agentic, Automation, Integration, Platform
    description: str = ""
    why_this_fits: str = ""  # Tied to AI Readiness score + research data
    specific_features: list[str] = field(default_factory=list)  # Features addressing their pain
    integrations: list[str] = field(default_factory=list)  # Systems they can integrate with
    tools: list[str] = field(default_factory=list)  # Legacy field for backwards compat
    pricing: SolutionPricing = field(default_factory=SolutionPricing)
    expected_impact: str = ""  # e.g., "40% ticket reduction in 60 days"
    complexity: str = ""  # Low, Medium, High
    time_to_value: str = ""  # e.g., "4-6 weeks"


@dataclass
class BusinessPriority:
    """
    A business priority with ONE recommended AI solution.

    Report includes top 3 priorities, each with a focused solution.
    """
    rank: int  # 1, 2, or 3
    problem_name: str
    problem_description: str
    solution: AISolution  # Single primary recommendation


@dataclass
class AntiRecommendation:
    """
    A 'tempting but wrong' solution to avoid.

    UPGRADED: Now includes vendor examples and cost of mistake.
    Premium differentiator: experts know what NOT to do.
    """
    name: str  # e.g., "Custom LLM Fine-tuning" (SPECIFIC)
    vendor_examples: list[str] = field(default_factory=list)  # Vendors that offer this
    why_tempting: str = ""  # Why it seems attractive
    why_wrong_for_them: str = ""  # Why it's wrong for their readiness level
    cost_of_mistake: str = ""  # What they'd waste in time/money


@dataclass
class RoadmapPhase:
    """
    A phase in the 90-day implementation roadmap.

    UPGRADED: Now includes specific deliverables, tools, and budget.
    Each month has a focus, actions, and decision gate.
    """
    month: int  # 1, 2, or 3
    focus: str = ""  # e.g., "Quick Win - Deploy Support Bot"
    actions: list[str] = field(default_factory=list)  # Legacy field
    specific_deliverables: list[str] = field(default_factory=list)  # Specific outputs
    tools_to_implement: list[str] = field(default_factory=list)  # Products to deploy
    budget: str = ""  # e.g., "$2,000-$3,000"
    decision_gate: str = ""  # Specific metric to hit before proceeding


@dataclass
class CompassReport:
    """
    Complete AI Readiness Compass report.

    Deliverable structure (8-10 pages):
    1. Executive Summary (score + top action)
    2. Top 3 Business Priorities (each with 1 solution)
    3. 90-Day Implementation Roadmap
    4. What to Avoid (2-3 anti-recommendations)
    5. Next Steps
    """
    run_id: str
    company_name: str
    ai_readiness_score: AIReadinessScore
    priorities: list[BusinessPriority]  # Top 3, each with 1 solution
    roadmap: list[RoadmapPhase]  # 3-month plan
    avoid: list[AntiRecommendation]  # 2-3 anti-recommendations
    research_insights: dict[str, Any]  # Raw research data
    html_content: str  # Rendered report HTML
    timestamp: datetime = field(default_factory=datetime.now)

    qa_report: Optional["CompassQAReport"] = None  # QA validation results

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/serialization."""
        return {
            "run_id": self.run_id,
            "company_name": self.company_name,
            "timestamp": self.timestamp.isoformat(),
            "ai_readiness_score": {
                "self_assessment": self.ai_readiness_score.self_assessment_score,
                "research": self.ai_readiness_score.research_score,
                "overall": self.ai_readiness_score.overall_score,
            },
            "priority_count": len(self.priorities),
            "avoid_count": len(self.avoid),
            "qa_report": self.qa_report.to_dict() if self.qa_report else None,
        }
