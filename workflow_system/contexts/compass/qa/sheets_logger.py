"""
Compass QA Sheets Logger - Logs QA validation results to Google Sheets.

Phase 1 MVP: Basic logging with core columns
Phase 2: Full schema with all validator details
"""

import structlog
import json
from typing import Protocol, runtime_checkable

from contexts.compass.qa_models import CompassQAReport

logger = structlog.get_logger()


@runtime_checkable
class SheetsClient(Protocol):
    """Protocol for Google Sheets client dependency."""

    async def append_row(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        values: list,
    ) -> bool:
        ...


class CompassQASheetsLogger:
    """
    Logs Compass QA validation results to Google Sheets.

    Phase 1 MVP: Logs to "Compass QA Results" sheet with basic columns
    Phase 2: Full schema with all validator details
    """

    # Sheet names
    QA_RESULTS_SHEET = "Compass QA Results"

    def __init__(self, sheets_client: SheetsClient, spreadsheet_id: str):
        """
        Initialize Compass QA sheets logger.

        Args:
            sheets_client: Google Sheets client
            spreadsheet_id: Spreadsheet ID for logging
        """
        self._sheets = sheets_client
        self._spreadsheet_id = spreadsheet_id

    @staticmethod
    def get_qa_results_headers() -> list:
        """
        Get headers for QA Results sheet.

        Phase 1 MVP: Core columns only
        """
        return [
            "run_id",
            "timestamp",
            "company_name",
            "overall_qa_score",
            "passed",
            "client_fulfillment_score",
            "client_pain_point_score",
            "client_quality_score",
            "client_overall_score",
            "client_passed",
            "client_likely_satisfied",
            "client_feedback",
            "client_suggestions_json",
            "validator_failures_json",
            "qa_duration_seconds",
        ]

    async def log_qa_report(self, qa_report: CompassQAReport) -> tuple[bool, str]:
        """
        Log QA report to Google Sheets.

        Args:
            qa_report: Compass QA report to log

        Returns:
            Tuple of (success, message)
        """
        logger.info(
            "compass_qa_sheets_log_started",
            run_id=qa_report.run_id,
            company=qa_report.company_name,
        )

        try:
            # Build row data
            row_data = self._build_qa_results_row(qa_report)

            # Append to sheet
            success = await self._sheets.append_row(
                spreadsheet_id=self._spreadsheet_id,
                sheet_name=self.QA_RESULTS_SHEET,
                values=row_data,
            )

            if success:
                logger.info(
                    "compass_qa_sheets_log_success",
                    run_id=qa_report.run_id,
                    company=qa_report.company_name,
                    overall_score=qa_report.overall_score,
                )
                return True, "QA results logged successfully"
            else:
                logger.warning(
                    "compass_qa_sheets_log_failed",
                    run_id=qa_report.run_id,
                    reason="append_row_returned_false",
                )
                return False, "Failed to append row to sheet"

        except Exception as e:
            logger.error(
                "compass_qa_sheets_log_error",
                run_id=qa_report.run_id,
                error=str(e),
            )
            return False, f"Error logging to sheets: {str(e)}"

    def _build_qa_results_row(self, qa_report: CompassQAReport) -> list:
        """
        Build row data for QA Results sheet.

        Args:
            qa_report: QA report

        Returns:
            List of column values
        """
        # Client satisfaction data (Phase 1 MVP)
        client_qa = qa_report.client_satisfaction_qa
        if client_qa:
            client_fulfillment = client_qa.fulfillment_score
            client_pain_point = client_qa.pain_point_score
            client_quality = client_qa.quality_score
            client_overall = client_qa.overall_score
            client_passed = client_qa.passed
            client_likely_satisfied = client_qa.client_likely_satisfied
            client_feedback = client_qa.feedback
            client_suggestions = json.dumps(client_qa.suggestions)
        else:
            client_fulfillment = 0.0
            client_pain_point = 0.0
            client_quality = 0.0
            client_overall = 0.0
            client_passed = False
            client_likely_satisfied = False
            client_feedback = "Validator did not run"
            client_suggestions = "[]"

        return [
            qa_report.run_id,
            qa_report.timestamp.isoformat(),
            qa_report.company_name,
            round(qa_report.overall_score, 2),
            qa_report.passed,
            round(client_fulfillment, 2),
            round(client_pain_point, 2),
            round(client_quality, 2),
            round(client_overall, 2),
            client_passed,
            client_likely_satisfied,
            client_feedback,
            client_suggestions,
            json.dumps(qa_report.validator_failures),
            round(qa_report.qa_duration_seconds, 2),
        ]

    async def ensure_headers_exist(self) -> bool:
        """
        Ensure QA Results sheet has headers.

        Returns:
            True if headers exist or were created
        """
        try:
            headers = self.get_qa_results_headers()
            success = await self._sheets.append_row(
                spreadsheet_id=self._spreadsheet_id,
                sheet_name=self.QA_RESULTS_SHEET,
                values=headers,
            )

            if success:
                logger.info(
                    "compass_qa_headers_ensured",
                    sheet=self.QA_RESULTS_SHEET,
                )
            return success

        except Exception as e:
            logger.warning(
                "compass_qa_headers_ensure_failed",
                error=str(e),
            )
            return False
