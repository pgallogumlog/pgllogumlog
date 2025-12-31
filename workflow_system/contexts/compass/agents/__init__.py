"""
Research Agents for AI Readiness Compass.

Three parallel agents that contribute 70% of the AI Readiness Score:
- CompanyResearchAgent: Website/tech stack analysis
- IndustryResearchAgent: AI adoption patterns in industry
- WhitePaperResearchAgent: Case studies and best practices
"""

from contexts.compass.agents.company_agent import CompanyResearchAgent
from contexts.compass.agents.industry_agent import IndustryResearchAgent
from contexts.compass.agents.whitepaper_agent import WhitePaperResearchAgent
from contexts.compass.agents.orchestrator import ResearchOrchestrator

__all__ = [
    "CompanyResearchAgent",
    "IndustryResearchAgent",
    "WhitePaperResearchAgent",
    "ResearchOrchestrator",
]
