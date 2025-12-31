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
from typing import Any


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
class AISolution:
    """
    A specific AI solution recommendation for a business priority.

    Each priority gets ONE primary solution matched to readiness level.
    """
    name: str  # e.g., "RAG-Powered Support Bot"
    approach_type: str  # RAG, Agentic, n8n, Adapter, Open Source
    description: str
    why_this_fits: str  # Tied to AI Readiness score
    tools: list[str]  # e.g., ["Claude", "Pinecone", "Slack"]
    expected_impact: str  # e.g., "40% ticket reduction"
    complexity: str  # Low, Medium, High


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

    Premium differentiator: experts know what NOT to do.
    """
    name: str  # e.g., "Full Autonomous Agent System"
    why_tempting: str  # Why it seems attractive
    why_wrong_for_them: str  # Why it's wrong for their readiness level


@dataclass
class RoadmapPhase:
    """
    A phase in the 90-day implementation roadmap.

    Each month has a focus, actions, and decision gate.
    """
    month: int  # 1, 2, or 3
    focus: str  # e.g., "Quick Win", "Foundation", "Scale"
    actions: list[str]  # Specific actions for this month
    decision_gate: str  # Criteria to proceed to next phase


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
        }
