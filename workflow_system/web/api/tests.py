"""
Test Runner API endpoints.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from config import get_container
from contexts.testing import TestConfig, TestOrchestrator
from contexts.testing.models import Environment, Tier
from contexts.testing.test_cases import TEST_CASES, get_test_cases

router = APIRouter()


class TestRunRequest(BaseModel):
    """Request to run tests."""

    environment: str = "Production"
    tier: str = "Standard"
    count: int = Field(default=10, ge=1, le=50)
    parallel: bool = True
    max_parallel: int = Field(default=5, ge=1, le=10)


class TestRunResponse(BaseModel):
    """Response from test run initiation."""

    message: str
    total_tests: int
    tiers: List[str]
    environment: str


class TestCaseInfo(BaseModel):
    """Information about a test case."""

    company: str
    category: str
    prompt_preview: str


@router.get("/cases")
async def list_test_cases(
    count: int = 50,
    category: Optional[str] = None,
):
    """List available test cases."""
    cases = get_test_cases(count)

    if category:
        cases = [c for c in cases if c.category == category]

    return {
        "total": len(cases),
        "categories": list(set(c.category for c in TEST_CASES)),
        "cases": [
            TestCaseInfo(
                company=c.company,
                category=c.category,
                prompt_preview=c.prompt[:100] + "...",
            )
            for c in cases
        ],
    }


@router.post("/run", response_model=TestRunResponse)
async def run_tests(
    request: TestRunRequest,
    background_tasks: BackgroundTasks,
):
    """
    Initiate a test run.

    Tests run in the background. Use /tests/status to check progress.
    """
    container = get_container()

    # Parse tier
    try:
        tier = Tier(request.tier)
    except ValueError:
        tier = Tier.STANDARD

    # Parse environment
    try:
        environment = Environment(request.environment)
    except ValueError:
        environment = Environment.PRODUCTION

    # Create config
    config = TestConfig(
        environment=environment,
        tier=tier,
        count=request.count,
        parallel=request.parallel,
        max_parallel=request.max_parallel,
    )

    # Calculate total tests
    tiers = config.tiers_to_run
    total_tests = request.count * len(tiers)

    # Add background task
    background_tasks.add_task(
        _run_tests_background,
        config=config,
        ai_provider=container.ai_provider(),
    )

    return TestRunResponse(
        message=f"Test run initiated with {total_tests} tests",
        total_tests=total_tests,
        tiers=tiers,
        environment=config.environment.value,
    )


async def _run_tests_background(config: TestConfig, ai_provider):
    """Run tests in the background."""
    orchestrator = TestOrchestrator(ai_provider=ai_provider)
    result = await orchestrator.run_tests(config)
    # Results are logged to console/sheets
    return result


@router.get("/tiers")
async def list_tiers():
    """List available tiers."""
    return {
        "tiers": [
            {"value": t.value, "name": t.name}
            for t in Tier
        ]
    }


@router.get("/environments")
async def list_environments():
    """List available environments."""
    return {
        "environments": [
            {"value": e.value, "name": e.name}
            for e in Environment
        ]
    }
