"""Prompts for two-call Compass architecture."""

from contexts.compass.prompts.deep_research import (
    DEEP_RESEARCH_SYSTEM,
    DEEP_RESEARCH_USER_TEMPLATE,
    DEEP_RESEARCH_TEMPERATURE,
)
from contexts.compass.prompts.synthesis import (
    STRATEGIC_SYNTHESIS_SYSTEM,
    STRATEGIC_SYNTHESIS_USER_TEMPLATE,
    STRATEGIC_SYNTHESIS_TEMPERATURE,
    get_readiness_tier,
)

__all__ = [
    # Deep Research (Call 1)
    "DEEP_RESEARCH_SYSTEM",
    "DEEP_RESEARCH_USER_TEMPLATE",
    "DEEP_RESEARCH_TEMPERATURE",
    # Strategic Synthesis (Call 2)
    "STRATEGIC_SYNTHESIS_SYSTEM",
    "STRATEGIC_SYNTHESIS_USER_TEMPLATE",
    "STRATEGIC_SYNTHESIS_TEMPERATURE",
    # Utilities
    "get_readiness_tier",
]
