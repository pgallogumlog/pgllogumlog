"""
Self-Assessment Scorer for AI Readiness Compass.

Calculates 30% of the overall AI Readiness Score based on user's
self-reported answers to 3 strategic questions.
"""

from contexts.compass.models import SelfAssessment


class SelfAssessmentScorer:
    """
    Calculate self-assessment portion (30%) of AI Readiness Score.

    Weights:
    - data_maturity: 40% (most critical for AI success)
    - automation_experience: 35% (indicates existing capability)
    - change_readiness: 25% (organizational factor)
    """

    WEIGHTS: dict[str, float] = {
        "data_maturity": 0.40,
        "automation_experience": 0.35,
        "change_readiness": 0.25,
    }

    READINESS_LEVELS: list[tuple[int, str]] = [
        (30, "Beginner"),
        (50, "Developing"),
        (70, "Established"),
        (85, "Advanced"),
        (100, "Leading"),
    ]

    def score(self, assessment: SelfAssessment) -> float:
        """
        Calculate weighted score from self-assessment.

        Args:
            assessment: User's self-assessment (1-5 for each dimension)

        Returns:
            Score from 20-100 (since minimum input is 1/5)
        """
        # Convert 1-5 scale to 0-100 percentage
        data_pct = (assessment.data_maturity / 5) * 100
        automation_pct = (assessment.automation_experience / 5) * 100
        change_pct = (assessment.change_readiness / 5) * 100

        # Apply weights
        weighted_score = (
            data_pct * self.WEIGHTS["data_maturity"]
            + automation_pct * self.WEIGHTS["automation_experience"]
            + change_pct * self.WEIGHTS["change_readiness"]
        )

        return weighted_score

    def get_breakdown(self, assessment: SelfAssessment) -> dict[str, float]:
        """
        Get individual component scores (before weighting).

        Args:
            assessment: User's self-assessment

        Returns:
            Dict with each component as 0-100 percentage
        """
        return {
            "data_maturity": (assessment.data_maturity / 5) * 100,
            "automation_experience": (assessment.automation_experience / 5) * 100,
            "change_readiness": (assessment.change_readiness / 5) * 100,
        }

    def get_readiness_level(self, assessment: SelfAssessment) -> str:
        """
        Get human-readable readiness level.

        Levels:
        - Beginner: 0-30
        - Developing: 31-50
        - Established: 51-70
        - Advanced: 71-85
        - Leading: 86-100

        Args:
            assessment: User's self-assessment

        Returns:
            Readiness level string
        """
        score = self.score(assessment)

        for threshold, level in self.READINESS_LEVELS:
            if score <= threshold:
                return level

        return "Leading"  # Default for 100
