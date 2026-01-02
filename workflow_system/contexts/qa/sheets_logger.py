"""
Google Sheets logger for QA results.

Logs AI call captures and workflow QA summaries to Google Sheets
for tracking, analysis, and auditing.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

import structlog

from contexts.qa.models import WorkflowQAResult
from contexts.qa.scoring import WorkflowScorer

if TYPE_CHECKING:
    from contexts.qa.call_capture import AICallCapture, AICallStore
    from contexts.qa.models import QAResult
    from config.dependency_injection import SheetsClient

logger = structlog.get_logger()


class QASheetsLogger:
    """
    Log QA results to Google Sheets.

    By default writes to "QA Logs" sheet with:
    - Per-call details with validation results
    - Per-workflow aggregated scores and summaries
    """

    def __init__(
        self,
        sheets_client: SheetsClient,
        spreadsheet_id: str,
        call_log_sheet: str = "AI Call Log",
        summary_sheet: str = "QA Logs",
    ):
        """
        Initialize the QA sheets logger.

        Args:
            sheets_client: Google Sheets client
            spreadsheet_id: ID of the spreadsheet to log to
            call_log_sheet: Name of sheet for per-call logs
            summary_sheet: Name of sheet for workflow summaries
        """
        self._sheets = sheets_client
        self._spreadsheet_id = spreadsheet_id
        self._call_sheet = call_log_sheet
        self._summary_sheet = summary_sheet

    async def log_call(self, capture: AICallCapture) -> bool:
        """
        Log a single AI call to the call log sheet.

        Args:
            capture: The captured AI call to log

        Returns:
            True if logging succeeded
        """
        try:
            row = capture.to_sheets_row()

            success = await self._sheets.append_row(
                spreadsheet_id=self._spreadsheet_id,
                sheet_name=self._call_sheet,
                values=row,
            )

            if success:
                logger.debug(
                    "qa_call_logged",
                    call_id=capture.call_id,
                    score=capture.call_score.overall_score if capture.call_score else None,
                )

            return success

        except Exception as e:
            logger.error(
                "qa_call_log_failed",
                call_id=capture.call_id,
                error=str(e),
            )
            return False

    async def log_all_calls(self, calls: list[AICallCapture]) -> int:
        """
        Log all captured calls to the call log sheet.

        Args:
            calls: List of captured AI calls

        Returns:
            Number of calls successfully logged
        """
        success_count = 0
        for call in calls:
            if await self.log_call(call):
                success_count += 1

        logger.info(
            "qa_calls_batch_logged",
            total=len(calls),
            success=success_count,
        )

        return success_count

    async def log_workflow_summary(
        self,
        call_store: AICallStore,
        client_name: str,
        run_id: str,
        semantic_result: Optional[QAResult] = None,
        top_issues: Optional[list[str]] = None,
    ) -> bool:
        """
        Log workflow-level QA summary to the summary sheet.

        When semantic_result is provided, uses 7-column semantic format
        (the most important metric). Otherwise falls back to call-level format.

        Args:
            call_store: Store containing all captured AI calls
            client_name: Name of the client
            run_id: Run ID for this workflow execution
            semantic_result: Optional semantic QA result from QAAuditor
            top_issues: Optional list of top issues found

        Returns:
            True if logging succeeded
        """
        try:
            # If we have a semantic result, use it as primary (7-column format)
            if semantic_result:
                semantic_result.run_id = run_id
                semantic_result.client_name = client_name
                row = semantic_result.to_sheets_row()

                success = await self._sheets.append_row(
                    spreadsheet_id=self._spreadsheet_id,
                    sheet_name=self._summary_sheet,
                    values=row,
                )

                if success:
                    logger.info(
                        "qa_workflow_summary_logged",
                        run_id=call_store.run_id,
                        score=semantic_result.score,
                        passed=semantic_result.passed,
                        total_calls=len(call_store.calls),
                    )

                return success

            # Fall back to call-level scoring if no semantic result
            scorer = WorkflowScorer()
            result = scorer.score(call_store, semantic_result)
            result.run_id = run_id
            result.client_name = client_name

            # Build row
            row = result.to_sheets_row()

            # Add top issues to the last column
            if top_issues:
                row[-1] = "; ".join(top_issues[:3])
            else:
                # Extract issues from failed calls
                issues = self._extract_top_issues(call_store)
                row[-1] = "; ".join(issues[:3])

            success = await self._sheets.append_row(
                spreadsheet_id=self._spreadsheet_id,
                sheet_name=self._summary_sheet,
                values=row,
            )

            if success:
                logger.info(
                    "qa_workflow_summary_logged",
                    run_id=result.run_id,
                    score=result.overall_score,
                    passed=result.passed,
                    total_calls=result.total_calls,
                )

            return success

        except Exception as e:
            logger.error(
                "qa_workflow_summary_log_failed",
                run_id=call_store.run_id,
                error=str(e),
            )
            return False

    async def log_complete_workflow(
        self,
        call_store: AICallStore,
        client_name: str,
        run_id: str,
        semantic_result: Optional[QAResult] = None,
    ) -> tuple[int, bool]:
        """
        Log complete workflow QA data to both sheets.

        Logs:
        1. Per-call details to "AI Call Log" sheet (each AI call with validation results)
        2. Workflow summary to "QA Logs" sheet (overall semantic audit)

        Args:
            call_store: Store containing all captured AI calls
            client_name: Name of the client
            run_id: Run ID for this workflow execution
            semantic_result: Optional semantic QA result

        Returns:
            Tuple of (calls_logged, summary_logged)
        """
        # Log all individual calls to AI Call Log sheet
        calls_logged = await self.log_all_calls(call_store.calls)

        # Log workflow summary to QA Logs sheet
        summary_logged = await self.log_workflow_summary(
            call_store=call_store,
            client_name=client_name,
            run_id=run_id,
            semantic_result=semantic_result,
        )

        return calls_logged, summary_logged

    def _extract_top_issues(self, call_store: AICallStore) -> list[str]:
        """Extract top issues from failed calls."""
        issues: list[str] = []

        for call in call_store.calls:
            for result in call.validation_results:
                if not result.passed:
                    issue = f"{result.check_name}: {result.message}"
                    if issue not in issues:
                        issues.append(issue)

        return issues

    @staticmethod
    def get_call_log_headers() -> list[str]:
        """Get column headers for the AI Call Log sheet."""
        return [
            "Timestamp",
            "Run ID",
            "Call ID",
            "Sequence",
            "Method",
            "Caller Context",
            "Model",
            "Temperature",
            "Max Tokens",
            "Input Tokens",
            "Output Tokens",
            "Stop Reason",
            "Duration (ms)",
            "Call Score",
            "Passed",
            "Worst Severity",
            "Failed Checks",
            "Recommended Fixes",
            "Prompt Preview",
            "Response Preview",
        ]

    @staticmethod
    def get_summary_headers() -> list[str]:
        """Get column headers for the Workflow QA Summary sheet."""
        return [
            "Timestamp",
            "Run ID",
            "Client",
            "Total Calls",
            "Calls Passed",
            "Calls Failed",
            "Overall Score",
            "Passed",
            "Worst Call ID",
            "Worst Severity",
            "Semantic Score",
            "Duration (s)",
            "Top Issues",
        ]


async def ensure_sheets_headers(
    sheets_client: SheetsClient,
    spreadsheet_id: str,
    call_log_sheet: str = "AI Call Log",
    summary_sheet: str = "Workflow QA Summary",
) -> None:
    """
    Ensure sheets have headers (creates them if sheets are empty).

    This is a utility function to set up new spreadsheets.
    Call once during initial setup.

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
                values=QASheetsLogger.get_call_log_headers(),
            )
            logger.info("qa_call_log_headers_created", sheet=call_log_sheet)
    except Exception as e:
        logger.warning("qa_call_log_sheet_check_failed", error=str(e))

    # Check summary sheet
    try:
        rows = await sheets_client.read_sheet(spreadsheet_id, summary_sheet)
        if not rows:
            await sheets_client.append_row(
                spreadsheet_id=spreadsheet_id,
                sheet_name=summary_sheet,
                values=QASheetsLogger.get_summary_headers(),
            )
            logger.info("qa_summary_headers_created", sheet=summary_sheet)
    except Exception as e:
        logger.warning("qa_summary_sheet_check_failed", error=str(e))
