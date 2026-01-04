"""
Report Generator for AI Readiness Compass.

Generates premium 8-10 page HTML reports using Jinja2 templates
enriched with Claude-generated content.
"""

import structlog
from datetime import datetime
from typing import Protocol, runtime_checkable
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from contexts.compass.models import (
    CompassRequest,
    AIReadinessScore,
    BusinessPriority,
    AntiRecommendation,
    RoadmapPhase,
    CompassReport,
)

logger = structlog.get_logger()


@runtime_checkable
class AIProvider(Protocol):
    """Protocol for AI provider dependency."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 4096,
    ) -> str:
        ...


EXECUTIVE_SUMMARY_SYSTEM = """You are writing the executive summary for a premium AI Readiness Report.

Write a compelling 2-3 paragraph executive summary that:
1. Opens with their AI Readiness Score and what it means
2. Highlights the single most impactful opportunity
3. Ends with a clear call to action

Tone: Professional, confident, actionable
Length: 150-200 words
Format: Plain text paragraphs (no markdown)
"""


class CompassReportGenerator:
    """
    Generates premium AI Readiness Compass reports.

    Combines Jinja2 templates with Claude-enriched content
    for personalized, professional reports.
    """

    def __init__(
        self,
        ai_provider: AIProvider,
        template_dir: str = None,
    ):
        self._ai = ai_provider

        # Set up template directory
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"

        self._template_dir = Path(template_dir)
        self._env = Environment(
            loader=FileSystemLoader(str(self._template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    async def generate(
        self,
        request: CompassRequest,
        score: AIReadinessScore,
        research_insights: dict,
        priorities: list[BusinessPriority],
        avoid: list[AntiRecommendation],
        roadmap: list[RoadmapPhase],
        run_id: str,
    ) -> CompassReport:
        """
        Generate complete AI Readiness Compass report.

        Args:
            request: Original submission request
            score: Calculated AI Readiness Score
            research_insights: Aggregated research data
            priorities: Top 3 business priorities with solutions
            avoid: Anti-recommendations
            roadmap: 90-day implementation plan
            run_id: Unique run identifier

        Returns:
            CompassReport with rendered HTML content
        """
        logger.info(
            "report_generation_started",
            run_id=run_id,
            company_name=request.company_name,
        )

        # Generate AI-enriched executive summary
        executive_summary = await self._generate_executive_summary(
            request, score, priorities
        )

        # Render the full report HTML
        html_content = self._render_report(
            request=request,
            score=score,
            research=research_insights,
            priorities=priorities,
            avoid=avoid,
            roadmap=roadmap,
            executive_summary=executive_summary,
            run_id=run_id,
        )

        report = CompassReport(
            run_id=run_id,
            company_name=request.company_name,
            ai_readiness_score=score,
            priorities=priorities,
            roadmap=roadmap,
            avoid=avoid,
            research_insights=research_insights,
            html_content=html_content,
        )

        logger.info(
            "report_generation_completed",
            run_id=run_id,
            company_name=request.company_name,
            html_length=len(html_content),
        )

        return report

    async def _generate_executive_summary(
        self,
        request: CompassRequest,
        score: AIReadinessScore,
        priorities: list[BusinessPriority],
    ) -> str:
        """Generate personalized executive summary using AI."""
        top_priority = priorities[0] if priorities else None

        prompt = f"""Write an executive summary for this AI Readiness Report:

COMPANY: {request.company_name}
INDUSTRY: {request.industry}
AI READINESS SCORE: {score.overall_score:.0f}/100

TOP PRIORITY: {top_priority.problem_name if top_priority else 'Process Optimization'}
RECOMMENDED SOLUTION: {top_priority.solution.name if top_priority else 'AI Automation'}
EXPECTED IMPACT: {top_priority.solution.expected_impact if top_priority else 'Efficiency improvement'}

Their main challenge: {request.pain_point}

Write a compelling executive summary that makes them excited to act on these recommendations."""

        try:
            summary = await self._ai.generate(
                prompt=prompt,
                system_prompt=EXECUTIVE_SUMMARY_SYSTEM,
                max_tokens=500,
            )
            return summary.strip()
        except Exception as e:
            logger.warning(
                "executive_summary_generation_failed",
                error=str(e),
            )
            return self._get_default_executive_summary(request, score, priorities)

    def _get_default_executive_summary(
        self,
        request: CompassRequest,
        score: AIReadinessScore,
        priorities: list[BusinessPriority],
    ) -> str:
        """Fallback executive summary if AI generation fails."""
        level = self._get_readiness_level(score.overall_score)
        top = priorities[0] if priorities else None

        return f"""Your AI Readiness Score of {score.overall_score:.0f}/100 places {request.company_name} at the {level} level. This indicates {'strong foundations for AI adoption' if score.overall_score > 60 else 'clear opportunities to build AI capabilities'}.

Based on our comprehensive analysis of your company, industry, and specific challenges, we've identified {top.problem_name if top else 'key opportunities'} as your highest-impact priority. {'Our recommended solution, ' + top.solution.name + ', is projected to deliver ' + top.solution.expected_impact + '.' if top else 'Focused AI implementation can drive significant improvements.'}

The 90-day roadmap in this report provides a clear path forward. We recommend starting with Month 1's quick win to build momentum and demonstrate value before expanding your AI capabilities."""

    def _render_report(
        self,
        request: CompassRequest,
        score: AIReadinessScore,
        research: dict,
        priorities: list[BusinessPriority],
        avoid: list[AntiRecommendation],
        roadmap: list[RoadmapPhase],
        executive_summary: str,
        run_id: str,
    ) -> str:
        """Render the complete report HTML."""
        try:
            template = self._env.get_template("report_base.html.j2")
            # Extract citations from research for display
            all_citations = research.get("_citations", []) if isinstance(research, dict) else []

            return template.render(
                # Company info
                company_name=request.company_name,
                industry=request.industry,
                company_size=request.company_size,
                contact_name=request.contact_name,
                # Score
                score=score,
                readiness_level=self._get_readiness_level(score.overall_score),
                score_color=self._get_score_color(score.overall_score),
                # Content
                executive_summary=executive_summary,
                priorities=priorities,
                avoid=avoid,
                roadmap=roadmap,
                research=research,
                all_citations=all_citations,
                # Meta
                run_id=run_id,
                generated_date=datetime.now().strftime("%B %d, %Y"),
                year=datetime.now().year,
            )
        except Exception as e:
            logger.error(
                "template_render_failed",
                error=str(e),
            )
            # Return basic HTML if template fails
            return self._render_basic_html(
                request, score, priorities, avoid, roadmap, executive_summary, run_id
            )

    def _render_basic_html(
        self,
        request: CompassRequest,
        score: AIReadinessScore,
        priorities: list[BusinessPriority],
        avoid: list[AntiRecommendation],
        roadmap: list[RoadmapPhase],
        executive_summary: str,
        run_id: str,
    ) -> str:
        """Fallback basic HTML if template rendering fails."""
        priorities_html = ""
        for p in priorities:
            priorities_html += f"""
            <div class="priority">
                <h3>Priority {p.rank}: {p.problem_name}</h3>
                <p>{p.problem_description}</p>
                <h4>Recommended Solution: {p.solution.name}</h4>
                <p><strong>Approach:</strong> {p.solution.approach_type}</p>
                <p>{p.solution.description}</p>
                <p><strong>Why This Fits:</strong> {p.solution.why_this_fits}</p>
                <p><strong>Expected Impact:</strong> {p.solution.expected_impact}</p>
            </div>
            """

        avoid_html = ""
        for a in avoid:
            avoid_html += f"""
            <div class="avoid">
                <h4>Avoid: {a.name}</h4>
                <p><strong>Why It's Tempting:</strong> {a.why_tempting}</p>
                <p><strong>Why It's Wrong for You:</strong> {a.why_wrong_for_them}</p>
            </div>
            """

        roadmap_html = ""
        for r in roadmap:
            actions = "".join(f"<li>{a}</li>" for a in r.actions)
            roadmap_html += f"""
            <div class="phase">
                <h4>Month {r.month}: {r.focus}</h4>
                <ul>{actions}</ul>
                <p><strong>Decision Gate:</strong> {r.decision_gate}</p>
            </div>
            """

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>AI Readiness Compass - {request.company_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #1a1a2e; }}
        h2 {{ color: #16213e; border-bottom: 2px solid #00d4ff; padding-bottom: 10px; }}
        .score {{ font-size: 48px; font-weight: bold; color: #00d4ff; }}
        .priority, .avoid, .phase {{ margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>AI Readiness Compass</h1>
    <h2>{request.company_name}</h2>

    <h2>AI Readiness Score</h2>
    <div class="score">{score.overall_score:.0f}/100</div>
    <p>Readiness Level: {self._get_readiness_level(score.overall_score)}</p>

    <h2>Executive Summary</h2>
    <p>{executive_summary}</p>

    <h2>Top 3 Business Priorities</h2>
    {priorities_html}

    <h2>What to Avoid</h2>
    {avoid_html}

    <h2>90-Day Implementation Roadmap</h2>
    {roadmap_html}

    <footer>
        <p>Report ID: {run_id}</p>
        <p>Generated: {datetime.now().strftime("%B %d, %Y")}</p>
    </footer>
</body>
</html>"""

    def _get_readiness_level(self, score: float) -> str:
        """Convert score to readiness level string."""
        if score <= 30:
            return "Beginner"
        elif score <= 50:
            return "Developing"
        elif score <= 70:
            return "Established"
        elif score <= 85:
            return "Advanced"
        else:
            return "Leading"

    def _get_score_color(self, score: float) -> str:
        """Get color for score display."""
        if score <= 30:
            return "#ff4444"  # Red
        elif score <= 50:
            return "#ffaa00"  # Orange
        elif score <= 70:
            return "#00d4ff"  # Blue
        elif score <= 85:
            return "#00ff88"  # Green
        else:
            return "#7c3aed"  # Purple
