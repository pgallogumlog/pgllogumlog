"""
Unit tests for Self-Assessment Scorer.
TDD: Write tests first, then implement scorer.
"""

import pytest

from contexts.compass.models import SelfAssessment
from contexts.compass.scoring import SelfAssessmentScorer


class TestSelfAssessmentScorer:
    """Tests for SelfAssessmentScorer."""

    @pytest.fixture
    def scorer(self):
        """Create scorer instance."""
        return SelfAssessmentScorer()

    def test_perfect_score_returns_100(self, scorer):
        """All 5s should give 100%."""
        assessment = SelfAssessment(
            data_maturity=5,
            automation_experience=5,
            change_readiness=5,
        )
        score = scorer.score(assessment)
        assert score == 100.0

    def test_minimum_score_returns_20(self, scorer):
        """All 1s should give 20% (1/5 = 20%)."""
        assessment = SelfAssessment(
            data_maturity=1,
            automation_experience=1,
            change_readiness=1,
        )
        score = scorer.score(assessment)
        assert score == 20.0

    def test_middle_score_returns_60(self, scorer):
        """All 3s should give 60% (3/5 = 60%)."""
        assessment = SelfAssessment(
            data_maturity=3,
            automation_experience=3,
            change_readiness=3,
        )
        score = scorer.score(assessment)
        assert score == 60.0

    def test_weighted_average_calculation(self, scorer):
        """
        Test weighted calculation:
        - data_maturity: 40% weight
        - automation_experience: 35% weight
        - change_readiness: 25% weight

        Input: (5, 3, 2)
        data_maturity: 5/5 * 100 * 0.40 = 40
        automation_experience: 3/5 * 100 * 0.35 = 21
        change_readiness: 2/5 * 100 * 0.25 = 10
        Total: 71
        """
        assessment = SelfAssessment(
            data_maturity=5,
            automation_experience=3,
            change_readiness=2,
        )
        score = scorer.score(assessment)
        assert score == 71.0

    def test_another_weighted_calculation(self, scorer):
        """
        Input: (2, 4, 5)
        data_maturity: 2/5 * 100 * 0.40 = 16
        automation_experience: 4/5 * 100 * 0.35 = 28
        change_readiness: 5/5 * 100 * 0.25 = 25
        Total: 69
        """
        assessment = SelfAssessment(
            data_maturity=2,
            automation_experience=4,
            change_readiness=5,
        )
        score = scorer.score(assessment)
        assert score == 69.0

    def test_get_breakdown_returns_component_scores(self, scorer):
        """Should return individual component scores."""
        assessment = SelfAssessment(
            data_maturity=4,
            automation_experience=3,
            change_readiness=5,
        )
        breakdown = scorer.get_breakdown(assessment)

        assert "data_maturity" in breakdown
        assert "automation_experience" in breakdown
        assert "change_readiness" in breakdown

        # Each component as percentage (1-5 → 20-100)
        assert breakdown["data_maturity"] == 80.0  # 4/5 * 100
        assert breakdown["automation_experience"] == 60.0  # 3/5 * 100
        assert breakdown["change_readiness"] == 100.0  # 5/5 * 100

    def test_weights_are_correct(self, scorer):
        """Verify weights sum to 1.0."""
        assert scorer.WEIGHTS["data_maturity"] == 0.40
        assert scorer.WEIGHTS["automation_experience"] == 0.35
        assert scorer.WEIGHTS["change_readiness"] == 0.25
        assert sum(scorer.WEIGHTS.values()) == 1.0

    def test_score_is_bounded_0_to_100(self, scorer):
        """Score should always be between 0 and 100."""
        # Minimum possible
        min_assessment = SelfAssessment(1, 1, 1)
        min_score = scorer.score(min_assessment)
        assert 0 <= min_score <= 100

        # Maximum possible
        max_assessment = SelfAssessment(5, 5, 5)
        max_score = scorer.score(max_assessment)
        assert 0 <= max_score <= 100

    def test_get_readiness_level_beginner(self, scorer):
        """Score 0-30 should be 'Beginner'."""
        assessment = SelfAssessment(1, 1, 2)  # Low scores
        level = scorer.get_readiness_level(assessment)
        assert level == "Beginner"

    def test_get_readiness_level_developing(self, scorer):
        """Score 31-50 should be 'Developing'."""
        assessment = SelfAssessment(2, 2, 3)  # ~44
        level = scorer.get_readiness_level(assessment)
        assert level == "Developing"

    def test_get_readiness_level_established(self, scorer):
        """Score 51-70 should be 'Established'."""
        assessment = SelfAssessment(3, 3, 4)  # ~64
        level = scorer.get_readiness_level(assessment)
        assert level == "Established"

    def test_get_readiness_level_advanced(self, scorer):
        """Score 71-85 should be 'Advanced'."""
        assessment = SelfAssessment(4, 4, 4)  # 80
        level = scorer.get_readiness_level(assessment)
        assert level == "Advanced"

    def test_get_readiness_level_leading(self, scorer):
        """Score 86-100 should be 'Leading'."""
        assessment = SelfAssessment(5, 5, 4)  # ~95
        level = scorer.get_readiness_level(assessment)
        assert level == "Leading"
