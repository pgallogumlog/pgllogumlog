"""
Compass Test Suite Loader.

Loads and filters test cases from compass_test_suite.json.
Provides methods for selecting tests by industry, readiness level,
random sampling, and stratified sampling.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Optional

from contexts.testing.compass_test_cases import CompassTestCase


class CompassTestLoader:
    """
    Loads Compass test cases from JSON file.

    Supports filtering by industry, readiness level, and various
    sampling strategies for test execution.
    """

    def __init__(self, suite_file: str = "data/compass_test_suite.json"):
        """
        Initialize loader with test suite file.

        Args:
            suite_file: Path to JSON test suite file
        """
        self.suite_file = Path(suite_file)
        self._suite_data: Optional[dict[str, Any]] = None
        self._test_cases: Optional[list[CompassTestCase]] = None

    def _load_suite(self) -> dict[str, Any]:
        """Load test suite from JSON file."""
        if self._suite_data is None:
            with open(self.suite_file, "r", encoding="utf-8") as f:
                self._suite_data = json.load(f)
        return self._suite_data

    def _parse_test_cases(self) -> list[CompassTestCase]:
        """Parse JSON test cases into CompassTestCase objects."""
        if self._test_cases is None:
            suite = self._load_suite()
            self._test_cases = []

            for case_data in suite["test_cases"]:
                # Convert expected_score_range from list to tuple
                expected_range = case_data.get("expected_score_range")
                if expected_range and isinstance(expected_range, list):
                    expected_range = tuple(expected_range)

                test_case = CompassTestCase(
                    company_name=case_data["company_name"],
                    website=case_data["website"],
                    industry=case_data["industry"],
                    company_size=case_data["company_size"],
                    data_maturity=case_data["data_maturity"],
                    automation_experience=case_data["automation_experience"],
                    change_readiness=case_data["change_readiness"],
                    pain_point=case_data["pain_point"],
                    description=case_data["description"],
                    email=case_data.get("email", "test@example.com"),
                    contact_name=case_data.get("contact_name", "Test User"),
                    category=case_data.get("category", "General"),
                    expected_score_range=expected_range,
                )

                # Store test_id as metadata for validation
                if not hasattr(test_case, "_test_id"):
                    object.__setattr__(test_case, "_test_id", case_data.get("id", ""))

                self._test_cases.append(test_case)

        return self._test_cases

    def load_all(self) -> list[CompassTestCase]:
        """
        Load all test cases from suite.

        Returns:
            List of all CompassTestCase objects
        """
        return self._parse_test_cases()

    def filter_by_industry(self, industry: str) -> list[CompassTestCase]:
        """
        Get all test cases for a specific industry.

        Args:
            industry: Industry name (e.g., "Technology", "Healthcare")

        Returns:
            List of CompassTestCase objects for that industry
        """
        all_cases = self.load_all()
        return [case for case in all_cases if case.industry == industry]

    def filter_by_readiness(self, readiness_level: str) -> list[CompassTestCase]:
        """
        Get all test cases for a specific readiness level.

        Args:
            readiness_level: Readiness level (e.g., "High", "Medium", "Low")

        Returns:
            List of CompassTestCase objects for that readiness level
        """
        all_cases = self.load_all()
        # Match against category field which contains readiness level
        return [
            case
            for case in all_cases
            if readiness_level.lower() in case.category.lower()
        ]

    def get_random_sample(
        self, count: int, seed: Optional[int] = None
    ) -> list[CompassTestCase]:
        """
        Get random N test cases from suite.

        Args:
            count: Number of test cases to return
            seed: Optional random seed for reproducibility

        Returns:
            List of randomly selected CompassTestCase objects
        """
        all_cases = self.load_all()

        if seed is not None:
            random.seed(seed)

        sample_size = min(count, len(all_cases))
        return random.sample(all_cases, sample_size)

    def get_stratified_sample(self, count: int) -> list[CompassTestCase]:
        """
        Get stratified sample balanced across readiness levels.

        Ensures balanced representation of Low, Medium, and High
        readiness companies in the sample.

        Args:
            count: Number of test cases to return

        Returns:
            List of CompassTestCase objects balanced across readiness levels
        """
        all_cases = self.load_all()

        # Group by readiness level
        low_cases = self.filter_by_readiness("Low")
        medium_cases = self.filter_by_readiness("Medium")
        high_cases = self.filter_by_readiness("High")

        # Calculate samples per level
        per_level = count // 3
        remainder = count % 3

        # Sample from each level
        sample = []

        if low_cases:
            low_count = min(per_level + (1 if remainder > 0 else 0), len(low_cases))
            sample.extend(random.sample(low_cases, low_count))

        if medium_cases:
            medium_count = min(
                per_level + (1 if remainder > 1 else 0), len(medium_cases)
            )
            sample.extend(random.sample(medium_cases, medium_count))

        if high_cases:
            high_count = min(per_level, len(high_cases))
            sample.extend(random.sample(high_cases, high_count))

        return sample

    def list_industries(self) -> list[str]:
        """
        Get list of all unique industries in test suite.

        Returns:
            Sorted list of industry names
        """
        all_cases = self.load_all()
        industries = list(set(case.industry for case in all_cases))
        return sorted(industries)

    def get_metadata(self) -> dict[str, Any]:
        """
        Get metadata about test suite.

        Returns:
            Dictionary with total_cases, by_industry, by_readiness counts
        """
        suite = self._load_suite()
        return suite.get("metadata", {})

    def validate_test_case(
        self,
        test_id: str,
        actual_score: int,
        tolerance: int = 0,
    ) -> dict[str, Any]:
        """
        Validate actual score against expected range for test case.

        Args:
            test_id: Test case ID
            actual_score: Actual AI readiness score from Compass
            tolerance: Optional tolerance margin (e.g., 5 points)

        Returns:
            Validation result with passed status and details
        """
        all_cases = self.load_all()

        # Find test case by ID
        test_case = None
        for case in all_cases:
            if hasattr(case, "_test_id") and getattr(case, "_test_id") == test_id:
                test_case = case
                break

        if not test_case:
            return {
                "passed": False,
                "error": f"Test case not found: {test_id}",
                "test_id": test_id,
            }

        if not test_case.expected_score_range:
            return {
                "passed": True,
                "warning": "No expected range defined",
                "test_id": test_id,
                "actual_score": actual_score,
            }

        min_score, max_score = test_case.expected_score_range

        # Check if within expected range
        within_range = min_score <= actual_score <= max_score

        # Check if within tolerance
        within_tolerance = False
        if tolerance > 0:
            within_tolerance = (
                min_score - tolerance <= actual_score <= max_score + tolerance
            )

        passed = within_range or within_tolerance

        return {
            "passed": passed,
            "test_id": test_id,
            "actual_score": actual_score,
            "expected_range": [min_score, max_score],
            "within_range": within_range,
            "within_tolerance": within_tolerance if tolerance > 0 else None,
            "company_name": test_case.company_name,
            "industry": test_case.industry,
        }
