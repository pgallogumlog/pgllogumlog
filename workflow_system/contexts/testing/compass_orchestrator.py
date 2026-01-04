"""
Compass Test Orchestrator - Runs AI Readiness Compass tests in parallel.

Uses the TwoCallCompassEngine for improved quality:
- Call 1: Deep Research (temp 0.2) - factual, grounded research
- Call 2: Strategic Synthesis (temp 0.4) - recommendations from research

Handles parallel execution of Compass tests and result aggregation.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

import structlog

from config.dependency_injection import AIProvider, EmailClient
from contexts.compass.models import CompassRequest, SelfAssessment
from contexts.compass.two_call_engine import TwoCallCompassEngine, TwoCallResult
from contexts.compass.sheets_logger import CompassQASheetsLogger
from contexts.testing.compass_test_cases import CompassTestCase, get_compass_test_cases

logger = structlog.get_logger()


@dataclass
class CompassTestResult:
    """Result of a single Compass test."""

    test_case: CompassTestCase
    run_id: str
    success: bool
    ai_readiness_score: Optional[float] = None
    self_assessment_score: Optional[float] = None
    research_score: Optional[float] = None
    qa_passed: bool = False
    qa_score: Optional[int] = None
    email_sent: bool = False
    error: Optional[str] = None
    duration_seconds: float = 0.0
    priority_count: int = 0
    anti_recommendation_count: int = 0
    report_html: Optional[str] = None  # HTML content for saving

    @property
    def company_name(self) -> str:
        """Get company name from test case."""
        return self.test_case.company_name


@dataclass
class CompassTestSuiteResult:
    """Results from a full Compass test suite run."""

    started_at: datetime
    completed_at: Optional[datetime] = None
    results: List[CompassTestResult] = field(default_factory=list)
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    avg_score: float = 0.0
    avg_duration: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "pass_rate": f"{(self.passed_tests / self.total_tests * 100):.1f}%" if self.total_tests > 0 else "0%",
            "avg_score": round(self.avg_score, 1),
            "avg_duration_seconds": round(self.avg_duration, 1),
            "results": [
                {
                    "company_name": r.test_case.company_name,
                    "category": r.test_case.category,
                    "run_id": r.run_id,
                    "success": r.success,
                    "ai_readiness_score": round(r.ai_readiness_score, 1) if r.ai_readiness_score else None,
                    "self_assessment_score": round(r.self_assessment_score, 1) if r.self_assessment_score else None,
                    "research_score": round(r.research_score, 1) if r.research_score else None,
                    "qa_passed": r.qa_passed,
                    "qa_score": r.qa_score,
                    "email_sent": r.email_sent,
                    "error": r.error,
                    "duration_seconds": round(r.duration_seconds, 1),
                    "priority_count": r.priority_count,
                    "expected_score_range": r.test_case.expected_score_range,
                    "score_in_range": (
                        r.test_case.expected_score_range[0] <= r.ai_readiness_score <= r.test_case.expected_score_range[1]
                        if r.ai_readiness_score and r.test_case.expected_score_range
                        else None
                    ),
                }
                for r in self.results
            ],
        }


class CompassTestOrchestrator:
    """
    Orchestrator for running Compass tests in parallel.

    Supports:
    - Parallel test execution with configurable concurrency
    - Varied readiness profiles testing
    - Result aggregation and analysis
    """

    def __init__(
        self,
        ai_provider: AIProvider,
        email_client: Optional[EmailClient] = None,
        sheets_logger: Optional[CompassQASheetsLogger] = None,
        max_parallel: int = 3,
    ):
        """
        Initialize the Compass test orchestrator.

        Args:
            ai_provider: AI provider for Compass engine
            email_client: Optional email client for sending reports
            sheets_logger: Optional sheets logger for QA logging
            max_parallel: Maximum parallel test executions
        """
        self._ai = ai_provider
        self._email_client = email_client
        self._sheets_logger = sheets_logger
        self._max_parallel = max_parallel

    async def run_tests(
        self,
        count: int = 5,
        category: Optional[str] = None,
    ) -> CompassTestSuiteResult:
        """
        Run Compass test suite.

        Args:
            count: Number of tests to run (1-15)
            category: Optional category filter (e.g., "Low Readiness", "High Readiness")

        Returns:
            CompassTestSuiteResult with all results
        """
        start_time = datetime.now()

        # Get test cases
        if category:
            from contexts.testing.compass_test_cases import get_compass_test_cases_by_category
            test_cases = get_compass_test_cases_by_category(category)[:count]
        else:
            test_cases = get_compass_test_cases(count)

        logger.info(
            "compass_test_suite_started",
            count=len(test_cases),
            category=category,
            max_parallel=self._max_parallel,
        )

        # Run tests with concurrency limit
        semaphore = asyncio.Semaphore(self._max_parallel)
        tasks = [
            self._run_single_test(test_case, semaphore)
            for test_case in test_cases
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        test_results: List[CompassTestResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test_results.append(CompassTestResult(
                    test_case=test_cases[i],
                    run_id="error",
                    success=False,
                    error=str(result),
                ))
            else:
                test_results.append(result)

        # Calculate statistics
        passed = [r for r in test_results if r.success]
        scores = [r.ai_readiness_score for r in passed if r.ai_readiness_score is not None]
        durations = [r.duration_seconds for r in test_results if r.duration_seconds > 0]

        suite_result = CompassTestSuiteResult(
            started_at=start_time,
            completed_at=datetime.now(),
            results=test_results,
            total_tests=len(test_results),
            passed_tests=len(passed),
            failed_tests=len(test_results) - len(passed),
            avg_score=sum(scores) / len(scores) if scores else 0.0,
            avg_duration=sum(durations) / len(durations) if durations else 0.0,
        )

        logger.info(
            "compass_test_suite_completed",
            total=suite_result.total_tests,
            passed=suite_result.passed_tests,
            failed=suite_result.failed_tests,
            avg_score=round(suite_result.avg_score, 1),
            avg_duration=round(suite_result.avg_duration, 1),
        )

        return suite_result

    async def _run_single_test(
        self,
        test_case: CompassTestCase,
        semaphore: asyncio.Semaphore,
    ) -> CompassTestResult:
        """Run a single Compass test."""
        async with semaphore:
            start_time = datetime.now()

            logger.info(
                "compass_test_started",
                company=test_case.company_name,
                category=test_case.category,
            )

            try:
                # Create Compass request from test case
                request = CompassRequest(
                    company_name=test_case.company_name,
                    website=test_case.website,
                    industry=test_case.industry,
                    company_size=test_case.company_size,
                    self_assessment=SelfAssessment(
                        data_maturity=test_case.data_maturity,
                        automation_experience=test_case.automation_experience,
                        change_readiness=test_case.change_readiness,
                    ),
                    pain_point=test_case.pain_point,
                    description=test_case.description,
                    email=test_case.email,
                    contact_name=test_case.contact_name,
                )

                # Create two-call engine and process
                engine = TwoCallCompassEngine(
                    ai_provider=self._ai,
                    email_client=self._email_client,
                    sheets_logger=self._sheets_logger,
                    enable_web_search=True,
                )

                result: TwoCallResult = await engine.process(request)

                duration = (datetime.now() - start_time).total_seconds()

                if result.report:
                    test_result = CompassTestResult(
                        test_case=test_case,
                        run_id=result.report.run_id,
                        success=True,
                        ai_readiness_score=result.report.ai_readiness_score.overall_score,
                        self_assessment_score=result.report.ai_readiness_score.self_assessment_score,
                        research_score=result.report.ai_readiness_score.research_score,
                        qa_passed=result.qa_passed,
                        qa_score=result.qa_score,
                        email_sent=result.email_sent,
                        duration_seconds=duration,
                        priority_count=len(result.report.priorities),
                        anti_recommendation_count=len(result.report.avoid),
                        report_html=result.report.html_content,  # Capture HTML for saving
                    )
                else:
                    test_result = CompassTestResult(
                        test_case=test_case,
                        run_id="failed",
                        success=False,
                        error=result.error or "No report generated",
                        duration_seconds=duration,
                    )

                logger.info(
                    "compass_test_completed",
                    company=test_case.company_name,
                    success=test_result.success,
                    score=test_result.ai_readiness_score,
                    duration=round(duration, 1),
                )

                return test_result

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(
                    "compass_test_failed",
                    company=test_case.company_name,
                    error=str(e),
                )
                return CompassTestResult(
                    test_case=test_case,
                    run_id="error",
                    success=False,
                    error=str(e),
                    duration_seconds=duration,
                )
