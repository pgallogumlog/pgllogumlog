"""
Workflow Context - Self-Consistency Engine.

This module handles the core AI workflow proposal generation using
self-consistency voting across multiple temperature variations.

Public API:
    - WorkflowEngine: Main orchestrator for processing inquiries
    - WorkflowResult: Result dataclass with proposal and metadata
"""

from contexts.workflow.engine import WorkflowEngine
from contexts.workflow.models import WorkflowResult, ConsensusResult, WorkflowProposal

__all__ = [
    "WorkflowEngine",
    "WorkflowResult",
    "ConsensusResult",
    "WorkflowProposal",
]
