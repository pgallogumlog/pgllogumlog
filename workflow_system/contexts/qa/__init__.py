"""
QA Context - Call Capture and Validation.

This module handles AI call capture for validation and logging.

Public API:
    Call Capture:
    - AICallCapture: Captured AI call with inputs/outputs/metadata
    - AICallStore: Store for captured calls in a workflow run
    - CallScore: Score for a single AI call

    Validation:
    - ValidationResult: Result from a validation check
    - ValidationPipeline: Orchestrates validators
    - CallScorer: Scores AI calls from validation results

    Models:
    - Severity: Severity levels for QA findings
    - FailureType: Types of failures detected
"""

from contexts.qa.models import (
    CallScore,
    FailureType,
    Severity,
)
from contexts.qa.call_capture import AICallCapture, AICallStore
from contexts.qa.scoring import CallScorer, ValidationPipeline
from contexts.qa.validators.base import ValidationResult, Validator

__all__ = [
    # Models
    "Severity",
    "FailureType",
    # Call Capture
    "AICallCapture",
    "AICallStore",
    "CallScore",
    # Validation
    "ValidationResult",
    "Validator",
    "ValidationPipeline",
    "CallScorer",
]
