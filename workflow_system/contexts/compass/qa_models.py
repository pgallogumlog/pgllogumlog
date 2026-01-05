"""
QA models for Compass AI Readiness Report validation.

Provides data models for post-generation QA validation across three dimensions:
1. Research QA (Call 1 validation)
2. Synthesis QA (Call 2 validation)
3. Client Satisfaction QA (Final report validation)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class ResearchQAResult:
    """QA results for Call 1 (Deep Research)."""

    hallucination_score: float  # 0-10: Are claims supported by sources?
    relevance_score: float  # 0-10: Does research address the input?
    quality_score: float  # 0-10: Is research comprehensive?
    feedback: str  # Brief explanation of scores
    issues: List[str] = field(default_factory=list)  # Specific problems found
    overall_score: float = 0.0  # Average of 3 scores
    passed: bool = False  # True if overall_score >= 7
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Calculate overall score and pass status."""
        self.overall_score = (
            self.hallucination_score + self.relevance_score + self.quality_score
        ) / 3
        self.passed = self.overall_score >= 7.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "hallucination_score": self.hallucination_score,
            "relevance_score": self.relevance_score,
            "quality_score": self.quality_score,
            "feedback": self.feedback,
            "issues": self.issues,
            "overall_score": self.overall_score,
            "passed": self.passed,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class SynthesisQAResult:
    """QA results for Call 2 (Strategic Synthesis)."""

    alignment_score: float  # 0-10: Are recommendations grounded in research?
    relevance_score: float  # 0-10: Do recommendations address user needs?
    quality_score: float  # 0-10: Are recommendations strategic and actionable?
    feedback: str  # Brief explanation
    strengths: List[str] = field(default_factory=list)  # What worked well
    improvements: List[str] = field(default_factory=list)  # Suggested improvements
    overall_score: float = 0.0  # Average of 3 scores
    passed: bool = False  # True if overall_score >= 7
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Calculate overall score and pass status."""
        self.overall_score = (
            self.alignment_score + self.relevance_score + self.quality_score
        ) / 3
        self.passed = self.overall_score >= 7.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "alignment_score": self.alignment_score,
            "relevance_score": self.relevance_score,
            "quality_score": self.quality_score,
            "feedback": self.feedback,
            "strengths": self.strengths,
            "improvements": self.improvements,
            "overall_score": self.overall_score,
            "passed": self.passed,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ClientSatisfactionQAResult:
    """QA results for Final Report."""

    fulfillment_score: float  # 0-10: Does report answer what client asked?
    pain_point_score: float  # 0-10: Does report address their pain point?
    quality_score: float  # 0-10: Is report professional and valuable?
    feedback: str  # Brief explanation
    client_likely_satisfied: bool = False  # Overall satisfaction prediction
    suggestions: List[str] = field(default_factory=list)  # Improvement suggestions
    overall_score: float = 0.0  # Average of 3 scores
    passed: bool = False  # True if overall_score >= 7
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Calculate overall score and pass status."""
        self.overall_score = (
            self.fulfillment_score + self.pain_point_score + self.quality_score
        ) / 3
        self.passed = self.overall_score >= 7.0
        self.client_likely_satisfied = self.overall_score >= 7.5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "fulfillment_score": self.fulfillment_score,
            "pain_point_score": self.pain_point_score,
            "quality_score": self.quality_score,
            "feedback": self.feedback,
            "client_likely_satisfied": self.client_likely_satisfied,
            "suggestions": self.suggestions,
            "overall_score": self.overall_score,
            "passed": self.passed,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CompassQAReport:
    """Aggregated QA report for entire Compass generation."""

    run_id: str
    company_name: str

    # Individual validator results
    research_qa: Optional[ResearchQAResult] = None
    synthesis_qa: Optional[SynthesisQAResult] = None
    client_satisfaction_qa: Optional[ClientSatisfactionQAResult] = None

    # Aggregated scores
    overall_score: float = 0.0  # Average of all validator overall scores
    passed: bool = False  # True if all validators passed

    # Metadata
    qa_duration_seconds: float = 0.0
    validator_failures: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def aggregate_scores(self) -> None:
        """
        Calculate overall score from validator results.

        Phase 1 MVP: Only client_satisfaction_qa is required
        Phase 2+: All three validators required
        """
        scores = []
        failed_validators = []

        # Track which validators actually ran
        ran_validators = []

        if self.research_qa:
            ran_validators.append("research")
            scores.append(self.research_qa.overall_score)
            if not self.research_qa.passed:
                failed_validators.append("research")

        if self.synthesis_qa:
            ran_validators.append("synthesis")
            scores.append(self.synthesis_qa.overall_score)
            if not self.synthesis_qa.passed:
                failed_validators.append("synthesis")

        if self.client_satisfaction_qa:
            ran_validators.append("client_satisfaction")
            scores.append(self.client_satisfaction_qa.overall_score)
            if not self.client_satisfaction_qa.passed:
                failed_validators.append("client_satisfaction")

        # Calculate overall score
        if scores:
            self.overall_score = sum(scores) / len(scores)
            # Pass if all validators that RAN passed (not all possible validators)
            self.passed = len(failed_validators) == 0
        else:
            # No validators ran at all
            self.overall_score = 0.0
            self.passed = False
            failed_validators.append("no_validators_ran")

        self.validator_failures = failed_validators

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "run_id": self.run_id,
            "company_name": self.company_name,
            "research_qa": self.research_qa.to_dict() if self.research_qa else None,
            "synthesis_qa": self.synthesis_qa.to_dict() if self.synthesis_qa else None,
            "client_satisfaction_qa": (
                self.client_satisfaction_qa.to_dict()
                if self.client_satisfaction_qa
                else None
            ),
            "overall_score": self.overall_score,
            "passed": self.passed,
            "qa_duration_seconds": self.qa_duration_seconds,
            "validator_failures": self.validator_failures,
            "timestamp": self.timestamp.isoformat(),
        }
