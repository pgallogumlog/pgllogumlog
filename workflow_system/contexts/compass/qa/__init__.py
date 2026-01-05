"""
Compass QA module - Post-generation quality validation.

Provides AI-powered validators for Compass reports:
- Research Validator (Call 1 QA)
- Synthesis Validator (Call 2 QA)
- Client Satisfaction Validator (Final Report QA)
"""

from contexts.compass.qa.orchestrator import CompassQAOrchestrator
from contexts.compass.qa_models import (
    CompassQAReport,
    ResearchQAResult,
    SynthesisQAResult,
    ClientSatisfactionQAResult,
)

__all__ = [
    "CompassQAOrchestrator",
    "CompassQAReport",
    "ResearchQAResult",
    "SynthesisQAResult",
    "ClientSatisfactionQAResult",
]
