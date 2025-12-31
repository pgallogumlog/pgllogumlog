"""
Unit tests for Compass domain models.
TDD: Write tests first, then implement models.
"""

import pytest
from dataclasses import asdict

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


class TestSelfAssessment:
    """Tests for SelfAssessment dataclass."""

    def test_creates_with_valid_scores(self):
        assessment = SelfAssessment(
            data_maturity=3,
            automation_experience=4,
            change_readiness=2,
        )
        assert assessment.data_maturity == 3
        assert assessment.automation_experience == 4
        assert assessment.change_readiness == 2

    def test_converts_to_dict(self):
        assessment = SelfAssessment(
            data_maturity=5,
            automation_experience=5,
            change_readiness=5,
        )
        result = asdict(assessment)
        assert result == {
            "data_maturity": 5,
            "automation_experience": 5,
            "change_readiness": 5,
        }


class TestAIReadinessScore:
    """Tests for AIReadinessScore dataclass."""

    def test_creates_with_scores(self):
        score = AIReadinessScore(
            self_assessment_score=80.0,
            research_score=60.0,
            overall_score=66.0,  # (80 * 0.30) + (60 * 0.70) = 24 + 42 = 66
            breakdown={"data": 80, "automation": 70, "change": 90},
        )
        assert score.self_assessment_score == 80.0
        assert score.research_score == 60.0
        assert score.overall_score == 66.0

    def test_breakdown_contains_components(self):
        score = AIReadinessScore(
            self_assessment_score=75.0,
            research_score=65.0,
            overall_score=68.0,
            breakdown={"data": 80, "automation": 70, "change": 75},
        )
        assert "data" in score.breakdown
        assert "automation" in score.breakdown
        assert "change" in score.breakdown


class TestCompassRequest:
    """Tests for CompassRequest dataclass."""

    def test_creates_with_all_fields(self):
        assessment = SelfAssessment(3, 4, 2)
        request = CompassRequest(
            company_name="Acme Corp",
            website="https://acme.com",
            industry="Technology",
            company_size="50-200",
            self_assessment=assessment,
            pain_point="Customer support overload",
            description="We're drowning in support tickets...",
            email="ceo@acme.com",
            contact_name="John Smith",
        )
        assert request.company_name == "Acme Corp"
        assert request.self_assessment.data_maturity == 3
        assert request.email == "ceo@acme.com"

    def test_website_can_be_empty(self):
        assessment = SelfAssessment(3, 4, 2)
        request = CompassRequest(
            company_name="No Website Co",
            website="",
            industry="Retail",
            company_size="10-50",
            self_assessment=assessment,
            pain_point="Manual processes",
            description="Everything is manual...",
            email="owner@noweb.com",
            contact_name="Jane Doe",
        )
        assert request.website == ""


class TestAISolution:
    """Tests for AISolution dataclass."""

    def test_creates_complete_solution(self):
        solution = AISolution(
            name="RAG-Powered Support Bot",
            approach_type="RAG",
            description="AI chatbot using company knowledge base",
            why_this_fits="Given your readiness score of 62, this approach...",
            tools=["Claude", "Pinecone", "Slack"],
            expected_impact="40% ticket reduction",
            complexity="Medium",
        )
        assert solution.name == "RAG-Powered Support Bot"
        assert solution.approach_type == "RAG"
        assert "Claude" in solution.tools
        assert solution.complexity == "Medium"


class TestBusinessPriority:
    """Tests for BusinessPriority dataclass."""

    def test_creates_priority_with_solution(self):
        solution = AISolution(
            name="Document Classifier",
            approach_type="Agentic",
            description="Auto-classify incoming documents",
            why_this_fits="Matches your data maturity level",
            tools=["Claude", "n8n"],
            expected_impact="60% time savings",
            complexity="Low",
        )
        priority = BusinessPriority(
            rank=1,
            problem_name="Document Processing Backlog",
            problem_description="Manual document sorting takes 20 hours/week",
            solution=solution,
        )
        assert priority.rank == 1
        assert priority.problem_name == "Document Processing Backlog"
        assert priority.solution.name == "Document Classifier"


class TestAntiRecommendation:
    """Tests for AntiRecommendation dataclass."""

    def test_creates_anti_recommendation(self):
        anti = AntiRecommendation(
            name="Full Autonomous Agent System",
            why_tempting="Promises complete automation of all processes",
            why_wrong_for_them="At readiness level 45, autonomous agents require data infrastructure you don't yet have",
        )
        assert anti.name == "Full Autonomous Agent System"
        assert "autonomous" in anti.why_wrong_for_them.lower()


class TestRoadmapPhase:
    """Tests for RoadmapPhase dataclass."""

    def test_creates_roadmap_phase(self):
        phase = RoadmapPhase(
            month=1,
            focus="Quick Win",
            actions=["Deploy support bot", "Train team on usage", "Monitor metrics"],
            decision_gate="Achieve 20% ticket deflection before proceeding",
        )
        assert phase.month == 1
        assert phase.focus == "Quick Win"
        assert len(phase.actions) == 3
        assert "deflection" in phase.decision_gate


class TestCompassReport:
    """Tests for CompassReport dataclass."""

    def test_creates_complete_report(self):
        score = AIReadinessScore(70.0, 60.0, 63.0, {})
        solution = AISolution("Bot", "RAG", "desc", "fits", ["Claude"], "40%", "Low")
        priority = BusinessPriority(1, "Support", "Too many tickets", solution)
        anti = AntiRecommendation("Complex", "Tempting", "Wrong")
        phase = RoadmapPhase(1, "Start", ["Do stuff"], "Check")

        report = CompassReport(
            run_id="compass-123",
            company_name="Test Corp",
            ai_readiness_score=score,
            priorities=[priority],
            roadmap=[phase],
            avoid=[anti],
            research_insights={"industry": "tech"},
            html_content="<html>...</html>",
        )
        assert report.run_id == "compass-123"
        assert len(report.priorities) == 1
        assert len(report.avoid) == 1
        assert len(report.roadmap) == 1
