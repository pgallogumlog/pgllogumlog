"""
Google Sheets logger for Compass QA results.

Logs validation results to two sheets:
- "Compass AI Call Log": Per-call validation details
- "Compass QA Summary": Per-run summaries
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import structlog

from contexts.compass.validators.models import (
    CallQAResult,
    CompassQASummary,
)

if TYPE_CHECKING:
    from config.dependency_injection import SheetsClient

logger = structlog.get_logger()


class CompassQASheetsLogger:
    """
    Log Compass QA results to Google Sheets.

    Writes to two tabs:
    - "Compass AI Call Log": Per-call validation details (2 rows per run)
    - "Compass QA Summary": Per-run summaries (1 row per run)
    """

    CALL_LOG_SHEET = "Compass AI Call Log"
    SUMMARY_SHEET = "Compass QA Summary"

    def __init__(
        self,
        sheets_client: SheetsClient,
        spreadsheet_id: str,
        call_log_sheet: Optional[str] = None,
        summary_sheet: Optional[str] = None,
    ):
        """
        Initialize the Compass QA sheets logger.

        Args:
            sheets_client: Google Sheets client
            spreadsheet_id: ID of the spreadsheet to log to
            call_log_sheet: Optional custom name for call log sheet
            summary_sheet: Optional custom name for summary sheet
        """
        self._sheets = sheets_client
        self._spreadsheet_id = spreadsheet_id
        self._call_log_sheet = call_log_sheet or self.CALL_LOG_SHEET
        self._summary_sheet = summary_sheet or self.SUMMARY_SHEET

    async def log_call_qa(self, result: CallQAResult) -> bool:
        """
        Log a single call's QA result to the call log sheet.

        Args:
            result: Call QA result to log

        Returns:
            True if logging succeeded
        """
        try:
            row = result.to_sheets_row()

            success = await self._sheets.append_row(
                spreadsheet_id=self._spreadsheet_id,
                sheet_name=self._call_log_sheet,
                values=row,
            )

            if success:
                logger.debug(
                    "compass_call_qa_logged",
                    run_id=result.run_id,
                    call_number=result.call_number,
                    call_type=result.call_type,
                    score=result.score,
                    passed=result.passed,
                )

            return success

        except Exception as e:
            logger.error(
                "compass_call_qa_log_failed",
                run_id=result.run_id,
                call_number=result.call_number,
                error=str(e),
            )
            return False

    async def log_summary(self, summary: CompassQASummary) -> bool:
        """
        Log compass run QA summary to the summary sheet.

        Args:
            summary: Compass QA summary to log

        Returns:
            True if logging succeeded
        """
        try:
            row = summary.to_sheets_row()

            success = await self._sheets.append_row(
                spreadsheet_id=self._spreadsheet_id,
                sheet_name=self._summary_sheet,
                values=row,
            )

            if success:
                logger.info(
                    "compass_qa_summary_logged",
                    run_id=summary.run_id,
                    company=summary.company_name,
                    overall_passed=summary.overall_qa_passed,
                    ai_readiness_score=summary.ai_readiness_score,
                )

            return success

        except Exception as e:
            logger.error(
                "compass_qa_summary_log_failed",
                run_id=summary.run_id,
                error=str(e),
            )
            return False

    async def log_complete_run(
        self,
        summary: CompassQASummary,
    ) -> tuple[int, bool]:
        """
        Log complete Compass run QA data to both sheets.

        Logs:
        1. Call 1 QA result to "Compass AI Call Log"
        2. Call 2 QA result to "Compass AI Call Log"
        3. Run summary to "Compass QA Summary"

        Args:
            summary: Complete QA summary with call results

        Returns:
            Tuple of (calls_logged_count, summary_logged)
        """
        calls_logged = 0

        # Log Call 1 QA
        if summary.call_1_qa:
            if await self.log_call_qa(summary.call_1_qa):
                calls_logged += 1

        # Log Call 2 QA
        if summary.call_2_qa:
            if await self.log_call_qa(summary.call_2_qa):
                calls_logged += 1

        # Log summary
        summary_logged = await self.log_summary(summary)

        logger.info(
            "compass_qa_complete_logged",
            run_id=summary.run_id,
            company=summary.company_name,
            calls_logged=calls_logged,
            summary_logged=summary_logged,
        )

        return calls_logged, summary_logged

    @staticmethod
    def get_call_log_headers() -> list[str]:
        """Get column headers for Compass AI Call Log sheet."""
        return CallQAResult.get_headers()

    @staticmethod
    def get_summary_headers() -> list[str]:
        """Get column headers for Compass QA Summary sheet."""
        return CompassQASummary.get_headers()


async def ensure_compass_sheets_headers(
    sheets_client: SheetsClient,
    spreadsheet_id: str,
    call_log_sheet: str = "Compass AI Call Log",
    summary_sheet: str = "Compass QA Summary",
) -> None:
    """
    Ensure Compass QA sheets have headers.

    Creates headers if sheets are empty. Call once during setup.

    Args:
        sheets_client: Google Sheets client
        spreadsheet_id: ID of the spreadsheet
        call_log_sheet: Name of call log sheet
        summary_sheet: Name of summary sheet
    """
    # Check call log sheet
    try:
        rows = await sheets_client.read_sheet(spreadsheet_id, call_log_sheet)
        if not rows:
            await sheets_client.append_row(
                spreadsheet_id=spreadsheet_id,
                sheet_name=call_log_sheet,
                values=CompassQASheetsLogger.get_call_log_headers(),
            )
            logger.info("compass_call_log_headers_created", sheet=call_log_sheet)
    except Exception as e:
        logger.warning("compass_call_log_sheet_check_failed", error=str(e))

    # Check summary sheet
    try:
        rows = await sheets_client.read_sheet(spreadsheet_id, summary_sheet)
        if not rows:
            await sheets_client.append_row(
                spreadsheet_id=spreadsheet_id,
                sheet_name=summary_sheet,
                values=CompassQASheetsLogger.get_summary_headers(),
            )
            logger.info("compass_summary_headers_created", sheet=summary_sheet)
    except Exception as e:
        logger.warning("compass_summary_sheet_check_failed", error=str(e))
