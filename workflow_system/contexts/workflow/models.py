"""
Data models for the Workflow Context.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class WorkflowRecommendation:
    """A single workflow recommendation."""

    name: str
    objective: str
    tools: list[str]
    description: str = ""
    metrics: list[str] = field(default_factory=list)
    feasibility: str = ""


@dataclass
class Phase:
    """A phase in the implementation roadmap."""

    phase_number: int
    phase_name: str
    workflows: list[WorkflowRecommendation]


@dataclass
class ConsensusResult:
    """Result of self-consistency voting."""

    final_answer: str
    total_responses: int
    votes_for_winner: int
    confidence_percent: int
    consensus_strength: str  # "Strong", "Moderate", "Weak"
    had_consensus: bool
    all_workflows: list[WorkflowRecommendation]
    fallback_mode: bool = False  # True if ranked fallback was used
    confidence_warning: str = ""  # Warning message when using fallback
    selection_method: str = "consensus"  # "consensus" or "ranked_fallback"


@dataclass
class WorkflowProposal:
    """Generated workflow proposal."""

    phases: list[Phase]
    recommendation: str
    html_body: str
    subject: str


@dataclass
class WorkflowResult:
    """Complete result from workflow processing."""

    run_id: str
    client_name: str
    business_name: str
    original_question: str
    normalized_prompt: str
    research_pack: dict[str, Any]
    consensus: ConsensusResult
    proposal: WorkflowProposal
    timestamp: datetime = field(default_factory=datetime.now)
    tier: str = "Standard"

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/serialization."""
        return {
            "run_id": self.run_id,
            "client_name": self.client_name,
            "business_name": self.business_name,
            "timestamp": self.timestamp.isoformat(),
            "tier": self.tier,
            "consensus": {
                "final_answer": self.consensus.final_answer,
                "confidence_percent": self.consensus.confidence_percent,
                "consensus_strength": self.consensus.consensus_strength,
                "had_consensus": self.consensus.had_consensus,
            },
            "workflow_count": len(self.consensus.all_workflows),
            "phase_count": len(self.proposal.phases),
        }


@dataclass
class EmailInquiry:
    """Incoming email inquiry."""

    message_id: str
    from_email: str
    from_name: str
    subject: str
    body: str

    @property
    def reply_to(self) -> str:
        """Format reply-to address."""
        if self.from_name:
            return f'"{self.from_name}" <{self.from_email}>'
        return self.from_email
