"""
QA validation models for Compass two-call engine.

Contains dataclasses for validation results with to_sheets_row() methods
for Google Sheets logging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class CallQAResult:
    """
    QA result for a single API call (Call 1 or Call 2).

    Captures validation results for semantic relevance, specificity,
    and completeness checks.
    """

    # Identity
    call_id: str
    call_number: int  # 1 or 2
    call_type: str  # "Research" or "Synthesis"
    run_id: str = ""

    # Validation results
    passed: bool = False
    score: int = 0  # 1-10

    # Semantic checks
    is_relevant: bool = False  # Output mentions client context
    is_specific: bool = False  # Not generic boilerplate
    is_complete: bool = False  # All expected fields present

    # Client context (for logging)
    company_name: str = ""
    industry: str = ""
    pain_point: str = ""

    # Token/timing info
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: float = 0.0

    # Issues and fixes
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # Previews for debugging
    prompt_preview: str = ""
    response_preview: str = ""

    # AI validation (optional)
    ai_relevance_score: Optional[float] = None

    timestamp: datetime = field(default_factory=datetime.now)

    def to_sheets_row(self) -> list[Any]:
        """
        Convert to row for 'Compass AI Call Log' sheet.

        Columns:
        Timestamp, Run ID, Call Number, Call Type, Company, Industry,
        Pain Point, Input Tokens, Output Tokens, Duration (ms), QA Score,
        QA Passed, Is Relevant, Is Specific, Is Complete, Issues,
        Recommendations, Prompt Preview, Response Preview
        """
        return [
            self.timestamp.isoformat(),
            self.run_id,
            self.call_number,
            self.call_type,
            self.company_name,
            self.industry,
            self.pain_point[:100] if self.pain_point else "",
            self.input_tokens,
            self.output_tokens,
            round(self.duration_ms, 1),
            self.score,
            "PASS" if self.passed else "FAIL",
            "TRUE" if self.is_relevant else "FALSE",
            "TRUE" if self.is_specific else "FALSE",
            "TRUE" if self.is_complete else "FALSE",
            "; ".join(self.issues[:3]) if self.issues else "",
            "; ".join(self.recommendations[:2]) if self.recommendations else "",
            self.prompt_preview[:300] if self.prompt_preview else "",
            self.response_preview[:300] if self.response_preview else "",
        ]

    @staticmethod
    def get_headers() -> list[str]:
        """Get column headers for Compass AI Call Log sheet."""
        return [
            "Timestamp",
            "Run ID",
            "Call Number",
            "Call Type",
            "Company",
            "Industry",
            "Pain Point",
            "Input Tokens",
            "Output Tokens",
            "Duration (ms)",
            "QA Score",
            "QA Passed",
            "Is Relevant",
            "Is Specific",
            "Is Complete",
            "Issues",
            "Recommendations",
            "Prompt Preview",
            "Response Preview",
        ]


@dataclass
class CrossCallQAResult:
    """
    QA result for cross-call validation.

    Validates that Call 2 (Synthesis) actually uses the research
    from Call 1, detecting when AI ignores provided context.
    """

    # Validation results
    passed: bool = False
    score: int = 0  # 1-10

    # Cross-call checks
    call_2_references_call_1: bool = False
    research_used_count: int = 0
    research_total_count: int = 0
    orphaned_findings_count: int = 0

    # Issues and fixes
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    @property
    def research_used_percent(self) -> float:
        """Percentage of research findings used in synthesis."""
        if self.research_total_count == 0:
            return 0.0
        return (self.research_used_count / self.research_total_count) * 100


@dataclass
class CompassQASummary:
    """
    Complete QA summary for a Compass run.

    Aggregates all validation results for logging to Google Sheets.
    """

    # Identity
    run_id: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Client info
    company_name: str = ""
    industry: str = ""
    pain_point: str = ""

    # Scores
    ai_readiness_score: float = 0.0

    # Per-call QA
    call_1_qa: Optional[CallQAResult] = None
    call_2_qa: Optional[CallQAResult] = None
    cross_call_qa: Optional[CrossCallQAResult] = None

    # Aggregates
    overall_qa_passed: bool = False
    total_tokens: int = 0
    duration_seconds: float = 0.0

    # Delivery status
    email_sent: bool = False
    payment_captured: bool = False

    # Top issues
    top_issues: list[str] = field(default_factory=list)

    def to_sheets_row(self) -> list[Any]:
        """
        Convert to row for 'Compass QA Summary' sheet.

        Columns:
        Timestamp, Run ID, Company, Industry, Pain Point, AI Readiness Score,
        Call 1 QA Score, Call 1 Passed, Call 2 QA Score, Call 2 Passed,
        Cross-Call Score, Cross-Call Passed, Research Used %, Overall QA Passed,
        Total Tokens, Duration (s), Email Sent, Payment Captured, Top Issues
        """
        return [
            self.timestamp.isoformat(),
            self.run_id,
            self.company_name,
            self.industry,
            self.pain_point[:100] if self.pain_point else "",
            round(self.ai_readiness_score, 1),
            self.call_1_qa.score if self.call_1_qa else "",
            "PASS" if self.call_1_qa and self.call_1_qa.passed else "FAIL",
            self.call_2_qa.score if self.call_2_qa else "",
            "PASS" if self.call_2_qa and self.call_2_qa.passed else "FAIL",
            self.cross_call_qa.score if self.cross_call_qa else "",
            "PASS" if self.cross_call_qa and self.cross_call_qa.passed else "FAIL",
            f"{self.cross_call_qa.research_used_percent:.0f}%" if self.cross_call_qa else "",
            "PASS" if self.overall_qa_passed else "FAIL",
            self.total_tokens,
            round(self.duration_seconds, 1),
            "TRUE" if self.email_sent else "FALSE",
            "TRUE" if self.payment_captured else "FALSE",
            "; ".join(self.top_issues[:3]) if self.top_issues else "",
        ]

    @staticmethod
    def get_headers() -> list[str]:
        """Get column headers for Compass QA Summary sheet."""
        return [
            "Timestamp",
            "Run ID",
            "Company",
            "Industry",
            "Pain Point",
            "AI Readiness Score",
            "Call 1 QA Score",
            "Call 1 Passed",
            "Call 2 QA Score",
            "Call 2 Passed",
            "Cross-Call Score",
            "Cross-Call Passed",
            "Research Used %",
            "Overall QA Passed",
            "Total Tokens",
            "Duration (s)",
            "Email Sent",
            "Payment Captured",
            "Top Issues",
        ]
