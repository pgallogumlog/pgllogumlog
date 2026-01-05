"""
Unit tests for Compass QA Phase 1 MVP.

Tests:
- QA data models
- Client Satisfaction Validator
- QA Orchestrator
- Sheets Logger
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from contexts.compass.models import CompassRequest, SelfAssessment
from contexts.compass.qa_models import (
    ClientSatisfactionQAResult,
    CompassQAReport,
)
from contexts.compass.qa.validators.client_satisfaction_validator import (
    ClientSatisfactionValidator,
    HTMLTextExtractor,
)
from contexts.compass.qa.orchestrator import CompassQAOrchestrator
from contexts.compass.qa.sheets_logger import CompassQASheetsLogger


class TestQAModels:
    """Test QA data models."""

    def test_client_satisfaction_result_calculates_overall_score(self):
        """Test that overall score is calculated correctly."""
        result = ClientSatisfactionQAResult(
            fulfillment_score=8.0,
            pain_point_score=9.0,
            quality_score=7.0,
            feedback="Good report",
        )

        # Should calculate average
        assert result.overall_score == 8.0  # (8+9+7)/3
        assert result.passed is True  # >= 7.0
        assert result.client_likely_satisfied is True  # >= 7.5

    def test_client_satisfaction_result_fails_below_threshold(self):
        """Test that scores below 7.0 fail."""
        result = ClientSatisfactionQAResult(
            fulfillment_score=6.0,
            pain_point_score=6.0,
            quality_score=7.0,
            feedback="Needs improvement",
        )

        assert result.overall_score == pytest.approx(6.33, rel=0.1)
        assert result.passed is False  # < 7.0
        assert result.client_likely_satisfied is False  # < 7.5

    def test_compass_qa_report_aggregation(self):
        """Test QA report aggregates validator results correctly."""
        qa_report = CompassQAReport(
            run_id="test-123",
            company_name="Acme Corp",
        )

        # Add client satisfaction result
        qa_report.client_satisfaction_qa = ClientSatisfactionQAResult(
            fulfillment_score=8.0,
            pain_point_score=9.0,
            quality_score=7.0,
            feedback="Good",
        )

        # Aggregate
        qa_report.aggregate_scores()

        assert qa_report.overall_score == 8.0  # Only 1 validator
        assert qa_report.passed is True
        assert qa_report.validator_failures == []

    def test_compass_qa_report_handles_missing_validators(self):
        """Test QA report handles missing validator results."""
        qa_report = CompassQAReport(
            run_id="test-123",
            company_name="Acme Corp",
        )

        # No validators run
        qa_report.aggregate_scores()

        assert qa_report.overall_score == 0.0
        assert qa_report.passed is False
        assert "no_validators_ran" in qa_report.validator_failures


class TestHTMLTextExtractor:
    """Test HTML text extraction."""

    def test_extracts_text_from_html(self):
        """Test basic HTML text extraction."""
        html = """
        <html>
            <head><title>Report</title></head>
            <body>
                <h1>AI Readiness Report</h1>
                <p>This is the content.</p>
                <script>alert('ignore this');</script>
            </body>
        </html>
        """

        extractor = HTMLTextExtractor()
        extractor.feed(html)
        text = extractor.get_text()

        assert "AI Readiness Report" in text
        assert "This is the content" in text
        assert "ignore this" not in text  # Script content excluded

    def test_handles_empty_html(self):
        """Test extraction from empty HTML."""
        extractor = HTMLTextExtractor()
        extractor.feed("")
        text = extractor.get_text()

        assert text == ""


class TestClientSatisfactionValidator:
    """Test Client Satisfaction Validator."""

    @pytest.mark.asyncio
    async def test_validates_report_successfully(self):
        """Test successful report validation."""
        # Mock AI provider
        mock_ai = AsyncMock()
        mock_ai.generate_json = AsyncMock(
            return_value={
                "fulfillment_score": 8.5,
                "pain_point_score": 9.0,
                "quality_score": 8.0,
                "feedback": "Excellent report addressing all client needs",
                "client_likely_satisfied": True,
                "suggestions": ["Add more specific metrics"],
            }
        )

        # Create validator
        validator = ClientSatisfactionValidator(mock_ai)

        # Create test request
        request = CompassRequest(
            company_name="Test Corp",
            website="https://test.com",
            industry="Technology",
            company_size="50-200",
            self_assessment=SelfAssessment(
                data_maturity=3,
                automation_experience=4,
                change_readiness=3,
            ),
            pain_point="Need to automate customer support",
            description="Growing tech company",
            email="test@test.com",
            contact_name="John Doe",
        )

        html_report = "<html><body><h1>AI Readiness Report</h1></body></html>"

        # Validate
        result = await validator.validate(request, html_report)

        # Assertions
        assert result.overall_score == 8.5  # (8.5+9+8)/3
        assert result.passed is True
        assert result.client_likely_satisfied is True
        assert "Excellent report" in result.feedback
        assert len(result.suggestions) == 1

    @pytest.mark.asyncio
    async def test_handles_validation_failure(self):
        """Test validator handles AI failures gracefully."""
        # Mock AI provider that raises exception
        mock_ai = AsyncMock()
        mock_ai.generate_json = AsyncMock(
            side_effect=Exception("AI service unavailable")
        )

        validator = ClientSatisfactionValidator(mock_ai)

        request = CompassRequest(
            company_name="Test Corp",
            website="https://test.com",
            industry="Technology",
            company_size="50-200",
            self_assessment=SelfAssessment(
                data_maturity=3,
                automation_experience=4,
                change_readiness=3,
            ),
            pain_point="Test",
            description="Test",
            email="test@test.com",
            contact_name="Test",
        )

        html_report = "<html><body>Report</body></html>"

        # Should return failed result, not raise exception
        result = await validator.validate(request, html_report)

        assert result.overall_score == 0.0
        assert result.passed is False
        assert "Validation failed" in result.feedback


class TestCompassQAOrchestrator:
    """Test QA Orchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_runs_validation(self):
        """Test orchestrator coordinates validation."""
        # Mock AI provider
        mock_ai = AsyncMock()
        mock_ai.generate_json = AsyncMock(
            return_value={
                "fulfillment_score": 8.0,
                "pain_point_score": 8.5,
                "quality_score": 7.5,
                "feedback": "Good report",
                "client_likely_satisfied": True,
                "suggestions": [],
            }
        )

        # Create orchestrator
        orchestrator = CompassQAOrchestrator(mock_ai)

        # Create test request
        request = CompassRequest(
            company_name="Test Corp",
            website="https://test.com",
            industry="Technology",
            company_size="50-200",
            self_assessment=SelfAssessment(
                data_maturity=3,
                automation_experience=4,
                change_readiness=3,
            ),
            pain_point="Test pain point",
            description="Test description",
            email="test@test.com",
            contact_name="Test User",
        )

        html_report = "<html><body><h1>Report</h1></body></html>"

        # Run QA review
        qa_report = await orchestrator.review(
            run_id="test-123",
            request=request,
            final_report_html=html_report,
        )

        # Assertions
        assert qa_report.run_id == "test-123"
        assert qa_report.company_name == "Test Corp"
        assert qa_report.client_satisfaction_qa is not None
        assert qa_report.overall_score == 8.0
        assert qa_report.passed is True
        assert qa_report.qa_duration_seconds >= 0


class TestCompassQASheetsLogger:
    """Test Compass QA Sheets Logger."""

    @pytest.mark.asyncio
    async def test_logs_qa_report_to_sheets(self):
        """Test logging QA report to Google Sheets."""
        # Mock sheets client
        mock_sheets = AsyncMock()
        mock_sheets.append_row = AsyncMock(return_value=True)

        # Create logger
        logger = CompassQASheetsLogger(
            sheets_client=mock_sheets,
            spreadsheet_id="test-spreadsheet-123",
        )

        # Create test QA report
        qa_report = CompassQAReport(
            run_id="test-456",
            company_name="Acme Corp",
        )
        qa_report.client_satisfaction_qa = ClientSatisfactionQAResult(
            fulfillment_score=8.0,
            pain_point_score=9.0,
            quality_score=7.5,
            feedback="Great report",
            suggestions=["Add ROI calculator"],
        )
        qa_report.aggregate_scores()

        # Log to sheets
        success, message = await logger.log_qa_report(qa_report)

        # Assertions
        assert success is True
        assert "successfully" in message
        mock_sheets.append_row.assert_called_once()

        # Check the row data
        call_args = mock_sheets.append_row.call_args
        assert call_args.kwargs["spreadsheet_id"] == "test-spreadsheet-123"
        assert call_args.kwargs["sheet_name"] == "Compass QA Results"

        row_data = call_args.kwargs["values"]
        assert row_data[0] == "test-456"  # run_id
        assert row_data[2] == "Acme Corp"  # company_name
        assert row_data[3] == 8.17  # overall_qa_score (rounded)

    def test_get_qa_results_headers(self):
        """Test QA results sheet headers."""
        headers = CompassQASheetsLogger.get_qa_results_headers()

        assert "run_id" in headers
        assert "company_name" in headers
        assert "overall_qa_score" in headers
        assert "client_fulfillment_score" in headers
        assert "passed" in headers
