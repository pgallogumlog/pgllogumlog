"""
QA Validators package.
Contains deterministic and probabilistic validators for AI call validation.
"""

from contexts.qa.validators.base import BaseValidator, ValidationResult, Validator
from contexts.qa.validators.deterministic import (
    DETERMINISTIC_VALIDATORS,
    JSONValidityValidator,
    ResponseEmptyValidator,
    TokenLimitWarning,
    TruncationDetector,
)
from contexts.qa.validators.probabilistic import (
    PROBABILISTIC_VALIDATORS,
    HallucinationDetector,
    PromptRelevanceValidator,
)

__all__ = [
    # Base
    "BaseValidator",
    "ValidationResult",
    "Validator",
    # Deterministic
    "DETERMINISTIC_VALIDATORS",
    "JSONValidityValidator",
    "TruncationDetector",
    "TokenLimitWarning",
    "ResponseEmptyValidator",
    # Probabilistic
    "PROBABILISTIC_VALIDATORS",
    "PromptRelevanceValidator",
    "HallucinationDetector",
]
