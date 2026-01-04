"""
Unit tests for CompassTestLoader.
"""

import json
import pytest
from pathlib import Path
from contexts.testing.compass_test_loader import CompassTestLoader
from contexts.testing.compass_test_cases import CompassTestCase


@pytest.fixture
def sample_test_suite_file(tmp_path):
    """Create a sample test suite JSON file."""
    test_suite = {
        "version": "1.0.0",
        "generated_at": "2026-01-04T10:00:00Z",
        "test_cases": [
            {
                "id": "tech-high-001",
                "company_name": "DataFlow Solutions",
                "website": "https://dataflow.example.com",
                "industry": "Technology",
                "company_size": "51-200",
                "readiness_level": "High",
                "data_maturity": 5,
                "automation_experience": 4,
                "change_readiness": 5,
                "pain_point": "Customer Support",
                "description": "Tech company with modern stack",
                "email": "test@dataflow.example.com",
                "contact_name": "Alex Chen",
                "category": "High Readiness",
                "expected_score_range": [70, 90],
                "tags": ["saas", "high-readiness"]
            },
            {
                "id": "healthcare-low-001",
                "company_name": "Family Medical",
                "website": "https://familymedical.example.com",
                "industry": "Healthcare",
                "company_size": "1-50",
                "readiness_level": "Low",
                "data_maturity": 2,
                "automation_experience": 1,
                "change_readiness": 1,
                "pain_point": "Email Overload",
                "description": "Small medical practice",
                "email": "test@familymedical.example.com",
                "contact_name": "Dr. Smith",
                "category": "Low Readiness",
                "expected_score_range": [15, 35],
                "tags": ["healthcare", "low-readiness"]
            },
            {
                "id": "tech-medium-001",
                "company_name": "Regional Software",
                "website": "https://regionalsoftware.example.com",
                "industry": "Technology",
                "company_size": "201-500",
                "readiness_level": "Medium",
                "data_maturity": 3,
                "automation_experience": 3,
                "change_readiness": 3,
                "pain_point": "Report Generation",
                "description": "Mid-size software company",
                "email": "test@regionalsoftware.example.com",
                "contact_name": "Jordan Lee",
                "category": "Medium Readiness",
                "expected_score_range": [45, 65],
                "tags": ["software", "medium-readiness"]
            }
        ],
        "metadata": {
            "total_cases": 3,
            "by_industry": {"Technology": 2, "Healthcare": 1},
            "by_readiness": {"High": 1, "Medium": 1, "Low": 1}
        }
    }

    suite_file = tmp_path / "test_suite.json"
    suite_file.write_text(json.dumps(test_suite, indent=2))
    return suite_file


class TestCompassTestLoader:
    """Tests for CompassTestLoader."""

    def test_load_all_returns_all_test_cases(self, sample_test_suite_file):
        """Test loading all test cases from JSON."""
        loader = CompassTestLoader(str(sample_test_suite_file))

        cases = loader.load_all()

        assert len(cases) == 3
        assert isinstance(cases[0], CompassTestCase)
        assert cases[0].company_name == "DataFlow Solutions"
        assert cases[0].industry == "Technology"

    def test_filter_by_industry_returns_correct_cases(self, sample_test_suite_file):
        """Test filtering by industry."""
        loader = CompassTestLoader(str(sample_test_suite_file))

        tech_cases = loader.filter_by_industry("Technology")

        assert len(tech_cases) == 2
        assert all(c.industry == "Technology" for c in tech_cases)
        assert tech_cases[0].company_name == "DataFlow Solutions"
        assert tech_cases[1].company_name == "Regional Software"

    def test_filter_by_readiness_returns_correct_cases(self, sample_test_suite_file):
        """Test filtering by readiness level."""
        loader = CompassTestLoader(str(sample_test_suite_file))

        high_cases = loader.filter_by_readiness("High")

        assert len(high_cases) == 1
        assert high_cases[0].company_name == "DataFlow Solutions"
        assert high_cases[0].category == "High Readiness"

    def test_get_random_sample_returns_correct_count(self, sample_test_suite_file):
        """Test getting random sample."""
        loader = CompassTestLoader(str(sample_test_suite_file))

        sample = loader.get_random_sample(count=2, seed=42)

        assert len(sample) == 2
        assert isinstance(sample[0], CompassTestCase)

        # Verify reproducibility with same seed
        sample2 = loader.get_random_sample(count=2, seed=42)
        assert sample[0].company_name == sample2[0].company_name

    def test_get_stratified_sample_balances_readiness(self, sample_test_suite_file):
        """Test stratified sampling balances readiness levels."""
        loader = CompassTestLoader(str(sample_test_suite_file))

        sample = loader.get_stratified_sample(count=3)

        assert len(sample) == 3
        readiness_levels = [c.category for c in sample]
        # Should have one of each readiness level
        assert "High Readiness" in readiness_levels
        assert "Medium Readiness" in readiness_levels
        assert "Low Readiness" in readiness_levels

    def test_list_industries_returns_unique_industries(self, sample_test_suite_file):
        """Test listing all available industries."""
        loader = CompassTestLoader(str(sample_test_suite_file))

        industries = loader.list_industries()

        assert len(industries) == 2
        assert "Technology" in industries
        assert "Healthcare" in industries

    def test_get_metadata_returns_correct_info(self, sample_test_suite_file):
        """Test getting metadata about test suite."""
        loader = CompassTestLoader(str(sample_test_suite_file))

        metadata = loader.get_metadata()

        assert metadata["total_cases"] == 3
        assert metadata["by_industry"]["Technology"] == 2
        assert metadata["by_readiness"]["High"] == 1

    def test_validate_test_case_within_range_passes(self, sample_test_suite_file):
        """Test validation passes when score within expected range."""
        loader = CompassTestLoader(str(sample_test_suite_file))

        result = loader.validate_test_case("tech-high-001", actual_score=75)

        assert result["passed"] is True
        assert result["test_id"] == "tech-high-001"
        assert result["actual_score"] == 75
        assert result["expected_range"] == [70, 90]

    def test_validate_test_case_outside_range_fails(self, sample_test_suite_file):
        """Test validation fails when score outside expected range."""
        loader = CompassTestLoader(str(sample_test_suite_file))

        result = loader.validate_test_case("tech-high-001", actual_score=50)

        assert result["passed"] is False
        assert result["actual_score"] == 50
        assert result["expected_range"] == [70, 90]

    def test_validate_test_case_with_tolerance_margin(self, sample_test_suite_file):
        """Test validation with tolerance margin."""
        loader = CompassTestLoader(str(sample_test_suite_file))

        # Score 68 is outside [70, 90] but within 5-point tolerance
        result = loader.validate_test_case("tech-high-001", actual_score=68, tolerance=5)

        assert result["passed"] is True
        assert result["within_tolerance"] is True
