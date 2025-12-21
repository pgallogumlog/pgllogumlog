"""
QA Context - Quality Auditor and Call Capture.

This module handles automated quality assessment of workflow outputs
and AI call capture for validation and logging.

Public API:
    Core QA:
    - QAAuditor: Main auditor for analyzing workflow outputs
    - QAResult: Result from quality analysis
    - Severity: Severity levels for QA findings
    - FailureType: Types of failures detected

    Call Capture:
    - AICallCapture: Captured AI call with inputs/outputs/metadata
    - AICallStore: Store for captured calls in a workflow run
    - CallScore: Score for a single AI call
    - WorkflowQAResult: Aggregate QA result for entire workflow

    Validation:
    - ValidationResult: Result from a validation check
    - ValidationPipeline: Orchestrates validators
    - CallScorer: Scores AI calls from validation results
    - WorkflowScorer: Aggregate scores for workflows

    Logging:
    - QASheetsLogger: Logs QA results to Google Sheets
"""

from contexts.qa.auditor import QAAuditor
from contexts.qa.models import (
    CallScore,
    FailureType,
    QAConfig,
    QAResult,
    Severity,
    WorkflowQAResult,
)
from contexts.qa.call_capture import AICallCapture, AICallStore
from contexts.qa.scoring import CallScorer, ValidationPipeline, WorkflowScorer
from contexts.qa.sheets_logger import QASheetsLogger
from contexts.qa.validators.base import ValidationResult, Validator

__all__ = [
    # Core QA
    "QAAuditor",
    "QAResult",
    "QAConfig",
    "Severity",
    "FailureType",
    # Call Capture
    "AICallCapture",
    "AICallStore",
    "CallScore",
    "WorkflowQAResult",
    # Validation
    "ValidationResult",
    "Validator",
    "ValidationPipeline",
    "CallScorer",
    "WorkflowScorer",
    # Logging
    "QASheetsLogger",
]
