"""
AI Readiness Compass Context.

Premium $497 strategic report product that provides:
- AI Readiness Score (30% self-assessment + 70% AI research)
- Top 3 Business Priorities with solutions
- 90-Day Implementation Roadmap
- What to Avoid (anti-recommendations)
"""

from contexts.compass.models import (
    SelfAssessment,
    AIReadinessScore,
    CompassRequest,
    AISolution,
    BusinessPriority,
    AntiRecommendation,
    RoadmapPhase,
    CompassReport,
)

__all__ = [
    "SelfAssessment",
    "AIReadinessScore",
    "CompassRequest",
    "AISolution",
    "BusinessPriority",
    "AntiRecommendation",
    "RoadmapPhase",
    "CompassReport",
]
