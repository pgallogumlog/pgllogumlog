"""
Compass Test Cases - DEPRECATED

DEPRECATED: Test case data has been moved to JSON.
Use CompassTestLoader from compass_test_loader.py instead.

This module now only provides the CompassTestCase dataclass.
The hardcoded test case list has been removed in favor of:
- data/compass_test_suite.json (29 real companies)

Migration:
    # Old (deprecated):
    from contexts.testing.compass_test_cases import get_compass_test_cases
    cases = get_compass_test_cases(10)

    # New:
    from contexts.testing.compass_test_loader import CompassTestLoader
    loader = CompassTestLoader()
    cases = loader.load_all()[:10]
"""

import warnings
from dataclasses import dataclass
from typing import Optional


@dataclass
class CompassTestCase:
    """Test case for AI Readiness Compass.

    This dataclass is still used by CompassTestLoader and other modules.
    """

    # Company Info
    company_name: str
    website: str
    industry: str
    company_size: str

    # Self-Assessment (1-5 scale)
    data_maturity: int
    automation_experience: int
    change_readiness: int

    # Challenge
    pain_point: str
    description: str

    # Contact
    email: str = "test@example.com"
    contact_name: str = "Test User"

    # Metadata
    category: str = "General"
    expected_score_range: Optional[tuple[int, int]] = None  # (min, max) expected score


# DEPRECATED: Empty list - use CompassTestLoader instead
COMPASS_TEST_CASES: list[CompassTestCase] = []


def get_compass_test_cases(count: int = 15) -> list[CompassTestCase]:
    """
    DEPRECATED: Use CompassTestLoader.load_all() instead.

    This function now returns an empty list.
    """
    warnings.warn(
        "get_compass_test_cases() is deprecated. "
        "Use CompassTestLoader().load_all() from compass_test_loader.py instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return []


def get_compass_test_cases_by_category(category: str) -> list[CompassTestCase]:
    """
    DEPRECATED: Use CompassTestLoader.filter_by_readiness() instead.

    This function now returns an empty list.
    """
    warnings.warn(
        "get_compass_test_cases_by_category() is deprecated. "
        "Use CompassTestLoader().filter_by_readiness() from compass_test_loader.py instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return []
