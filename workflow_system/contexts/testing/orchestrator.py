"""
Test Orchestrator - Main orchestrator for running test suites.

Handles parallel execution, tier comparison, and result aggregation.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Optional

import structlog

from config.dependency_injection import AIProvider, SheetsClient
from contexts.qa import QAAuditor
from contexts.qa.sheets_logger import QASheetsLogger
from contexts.testing.models import (
    TestCase,
    TestConfig,
    TestResult,
    TestSuiteResult,
)
from contexts.testing.test_cases import get_test_cases
from contexts.workflow import WorkflowEngine
from contexts.workflow.models import EmailInquiry
from shared.delivery import deliver_workflow_via_email

logger = structlog.get_logger()


class TestOrchestrator:
    """
    Main orchestrator for running test suites.

    Supports:
    - Single tier or all-tier comparison testing
    - Parallel test execution with configurable concurrency
    - Result logging to Google Sheets
    """

    def __init__(
        self,
        ai_provider: AIProvider,
        sheets_client: Optional[SheetsClient] = None,
        qa_spreadsheet_id: Optional[str] = None,
        email_client=None,
        send_emails: bool = True,
        html_output_dir: Optional[str] = None,
    ):
        """
        Initialize the test orchestrator.

        Args:
            ai_provider: AI provider for workflow engine
            sheets_client: Optional sheets client for logging
            qa_spreadsheet_id: Optional spreadsheet ID for QA logs
            email_client: Optional email client for sending proposals
            send_emails: Whether to send proposal emails after processing
            html_output_dir: Optional directory to save HTML proposals (e.g., "test_results")
        """
        self._ai = ai_provider
        self._sheets = sheets_client
        self._qa_spreadsheet_id = qa_spreadsheet_id
        self._email_client = email_client
        self._send_emails = send_emails
        self._html_output_dir = html_output_dir

    async def run_tests(self, config: TestConfig) -> TestSuiteResult:
        """
        Run a full test suite based on configuration.

        Args:
            config: Test configuration

        Returns:
            TestSuiteResult with all results and statistics
        """
        start_time = datetime.now()
        logger.info(
            "test_suite_started",
            environment=config.environment.value,
            tiers=config.tiers_to_run,
            count=config.count,
        )

        # Get test cases
        test_cases = get_test_cases(config.count)
        tiers = config.tiers_to_run

        # Build test matrix: (test_case, tier) pairs
        test_matrix: list[tuple[TestCase, str]] = []
        for test_case in test_cases:
            for tier in tiers:
                test_matrix.append((test_case, tier))

        logger.info(
            "test_matrix_built",
            total_executions=len(test_matrix),
            test_cases=len(test_cases),
            tiers=len(tiers),
        )

        # Run tests (parallel or sequential)
        if config.parallel:
            results = await self._run_parallel(
                test_matrix=test_matrix,
                environment=config.environment.value,
                max_parallel=config.max_parallel,
            )
        else:
            results = await self._run_sequential(
                test_matrix=test_matrix,
                environment=config.environment.value,
            )

        end_time = datetime.now()

        suite_result = TestSuiteResult(
            config=config,
            results=results,
            start_time=start_time,
            end_time=end_time,
        )

        logger.info(
            "test_suite_complete",
            total=suite_result.total_tests,
            passed=suite_result.passed,
            failed=suite_result.failed,
            pass_rate=f"{suite_result.pass_rate:.1f}%",
            duration_seconds=suite_result.duration_seconds,
        )

        return suite_result

    async def _run_parallel(
        self,
        test_matrix: list[tuple[TestCase, str]],
        environment: str,
        max_parallel: int = 5,
    ) -> list[TestResult]:
        """Run tests in parallel with concurrency limit."""
        semaphore = asyncio.Semaphore(max_parallel)
        results: list[TestResult] = []

        async def run_with_semaphore(test_case: TestCase, tier: str) -> TestResult:
            async with semaphore:
                return await self._run_single_test(test_case, tier, environment)

        tasks = [
            run_with_semaphore(test_case, tier)
            for test_case, tier in test_matrix
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test_case, tier = test_matrix[i]
                final_results.append(TestResult(
                    test_case=test_case,
                    tier=tier,
                    environment=environment,
                    success=False,
                    run_id="error",
                    error_message=str(result),
                ))
            else:
                final_results.append(result)

        return final_results

    async def _run_sequential(
        self,
        test_matrix: list[tuple[TestCase, str]],
        environment: str,
    ) -> list[TestResult]:
        """Run tests sequentially."""
        results = []
        for test_case, tier in test_matrix:
            result = await self._run_single_test(test_case, tier, environment)
            results.append(result)
        return results

    async def _run_single_test(
        self,
        test_case: TestCase,
        tier: str,
        environment: str,
    ) -> TestResult:
        """Run a single test case with QA audit."""
        start_time = time.time()

        logger.debug(
            "test_case_started",
            company=test_case.company,
            tier=tier,
        )

        try:
            # Create QA sheets logger if sheets client is available
            qa_logger = None
            if self._sheets and self._qa_spreadsheet_id:
                qa_logger = QASheetsLogger(
                    sheets_client=self._sheets,
                    spreadsheet_id=self._qa_spreadsheet_id,
                )

            # Create workflow engine for this test
            engine = WorkflowEngine(
                ai_provider=self._ai,
                min_consensus_votes=3,
                qa_sheets_logger=qa_logger,
            )

            # Create mock email inquiry from test case
            inquiry = EmailInquiry(
                message_id=f"test-{test_case.test_id}-{tier}",
                from_email="pgallogumlog@gmail.com",
                from_name="Test Runner",
                subject=f"Test: {test_case.company}",
                body=test_case.prompt,
            )

            # Run the workflow (returns tuple of workflow_result, qa_result)
            workflow_result, qa_result_from_engine = await engine.process_inquiry(
                inquiry=inquiry,
                tier=tier,
            )

            # Get semantic audit from engine if available (primary metric)
            qa_score = None
            qa_passed = None
            qa_severity = None
            qa_failure_reason = None

            if qa_result_from_engine and qa_result_from_engine.semantic_result:
                # Use semantic result as primary metric (most important)
                semantic = qa_result_from_engine.semantic_result
                qa_score = semantic.score
                qa_passed = semantic.passed
                qa_severity = semantic.severity.value
                if not semantic.passed:
                    qa_failure_reason = semantic.root_cause
            elif qa_result_from_engine:
                # Fall back to call-level score if no semantic result
                qa_score = qa_result_from_engine.overall_score
                qa_passed = qa_result_from_engine.passed
                qa_severity = qa_result_from_engine.worst_severity.value
            elif self._sheets and self._qa_spreadsheet_id:
                # Fall back to separate QA audit
                qa_auditor = QAAuditor(
                    ai_provider=self._ai,
                    sheets_client=self._sheets,
                    qa_spreadsheet_id=self._qa_spreadsheet_id,
                )
                qa_result = await qa_auditor.audit(workflow_result)
                qa_score = qa_result.score
                qa_passed = qa_result.passed
                qa_severity = qa_result.severity.value
                if not qa_result.passed:
                    qa_failure_reason = qa_result.root_cause

                # Log QA result to sheets
                await qa_auditor.log_to_sheets(qa_result)

            if qa_score is not None:
                logger.info(
                    "qa_audit_complete",
                    run_id=workflow_result.run_id,
                    score=qa_score,
                    passed=qa_passed,
                    severity=qa_severity,
                )

            duration = time.time() - start_time

            # Success is based on semantic audit if available, else workflow completion
            test_success = qa_passed if qa_passed is not None else True

            result = TestResult(
                test_case=test_case,
                tier=tier,
                environment=environment,
                success=test_success,
                run_id=workflow_result.run_id,
                workflow_count=len(workflow_result.consensus.all_workflows),
                phase_count=len(workflow_result.proposal.phases),
                consensus_strength=workflow_result.consensus.consensus_strength,
                confidence_percent=workflow_result.consensus.confidence_percent,
                duration_seconds=duration,
                qa_score=qa_score,
                qa_passed=qa_passed,
                qa_failure_reason=qa_failure_reason,
            )

            logger.info(
                "test_case_complete",
                company=test_case.company,
                tier=tier,
                success=test_success,
                consensus=workflow_result.consensus.consensus_strength,
                qa_score=qa_score,
                duration=f"{duration:.1f}s",
            )

            # Save HTML proposal if configured
            if self._html_output_dir:
                await self._save_html_proposal(workflow_result, test_case, tier)

            # Send proposal email if configured
            if self._send_emails and self._email_client:
                await deliver_workflow_via_email(
                    result=workflow_result,
                    inquiry=inquiry,
                    email_client=self._email_client,
                    recipient="pgallogumlog@gmail.com",
                )

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "test_case_failed",
                company=test_case.company,
                tier=tier,
                error=str(e),
            )

            return TestResult(
                test_case=test_case,
                tier=tier,
                environment=environment,
                success=False,
                run_id="error",
                error_message=str(e),
                duration_seconds=duration,
            )

    async def log_results_to_sheets(
        self,
        suite_result: TestSuiteResult,
        sheet_name: str = "Test Results",
    ) -> bool:
        """
        Log test results to Google Sheets.

        Args:
            suite_result: Test suite results
            sheet_name: Sheet tab name

        Returns:
            True if successful
        """
        if not self._sheets or not self._qa_spreadsheet_id:
            logger.warning("sheets_logging_not_configured")
            return False

        try:
            for result in suite_result.results:
                # Format duration as "Xm Ys"
                mins = int(result.duration_seconds // 60)
                secs = int(result.duration_seconds % 60)
                duration_formatted = f"{mins}m {secs}s"

                # Build notes column with semantic audit result (primary metric)
                if result.error_message:
                    notes = result.error_message
                elif result.qa_score is not None:
                    qa_status = "PASS" if result.qa_passed else "FAIL"
                    if result.qa_failure_reason:
                        # Show failure reason for failed audits
                        notes = f"Semantic QA: {qa_status} ({result.qa_score}/10) - {result.qa_failure_reason}"
                    else:
                        notes = f"Semantic QA: {qa_status} ({result.qa_score}/10)"
                else:
                    notes = ""

                row = [
                    result.timestamp.isoformat(),
                    result.test_case.company,
                    result.tier,
                    result.environment,
                    "PASS" if result.success else "FAIL",
                    result.run_id,
                    result.consensus_strength,
                    result.confidence_percent,
                    result.workflow_count,
                    result.phase_count,
                    duration_formatted,
                    notes,
                ]

                await self._sheets.append_row(
                    spreadsheet_id=self._qa_spreadsheet_id,
                    sheet_name=sheet_name,
                    values=row,
                )

            logger.info(
                "results_logged_to_sheets",
                count=len(suite_result.results),
            )
            return True

        except Exception as e:
            logger.error("sheets_logging_failed", error=str(e))
            return False

    async def _save_html_proposal(
        self,
        workflow_result: WorkflowResult,
        test_case: TestCase,
        tier: str,
    ) -> bool:
        """
        Save HTML proposal to file.

        Args:
            workflow_result: Workflow result with proposal
            test_case: Test case that generated this result
            tier: Tier name (Budget/Standard/Premium)

        Returns:
            True if saved successfully
        """
        import os
        from datetime import datetime

        try:
            # Create output directory if it doesn't exist
            os.makedirs(self._html_output_dir, exist_ok=True)

            # Create filename: {tier}_{company}_{timestamp}_{run_id}.html
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            company_slug = test_case.company.replace(" ", "_").replace("/", "-")
            filename = f"{tier}_{company_slug}_{timestamp}_{workflow_result.run_id[:8]}.html"
            filepath = os.path.join(self._html_output_dir, filename)

            # Write HTML to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(workflow_result.proposal.html_body)

            logger.info(
                "html_proposal_saved",
                filepath=filepath,
                run_id=workflow_result.run_id,
                tier=tier,
                company=test_case.company,
            )

            print(f"\n✅ HTML saved: {filepath}")
            return True

        except Exception as e:
            logger.error(
                "html_save_failed",
                error=str(e),
                run_id=workflow_result.run_id,
            )
            return False
