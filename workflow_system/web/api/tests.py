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
    save_html: bool = False


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

    # Generate run_id for QA capture
    import uuid
    run_id = str(uuid.uuid4())[:8]

    # Get capturing AI provider for QA
    ai_provider = container.capturing_ai_provider(
        run_id=run_id,
        run_probabilistic=False,  # Deterministic only for speed
    )

    # Get sheets client and QA spreadsheet ID for logging
    sheets_client = None
    qa_spreadsheet_id = container.settings.google_sheets_qa_log_id
    if qa_spreadsheet_id:
        try:
            sheets_client = container.sheets_client()
        except Exception:
            pass  # Sheets logging is optional

    # Determine HTML output directory
    html_output_dir = "test_results" if request.save_html else None

    # Add background task
    background_tasks.add_task(
        _run_tests_background,
        config=config,
        ai_provider=ai_provider,
        sheets_client=sheets_client,
        qa_spreadsheet_id=qa_spreadsheet_id,
        html_output_dir=html_output_dir,
    )

    return TestRunResponse(
        message=f"Test run initiated with {total_tests} tests",
        total_tests=total_tests,
        tiers=tiers,
        environment=config.environment.value,
    )


async def _run_tests_background(
    config: TestConfig,
    ai_provider,
    sheets_client=None,
    qa_spreadsheet_id=None,
    html_output_dir=None,
):
    """Run tests in the background."""
    orchestrator = TestOrchestrator(
        ai_provider=ai_provider,
        sheets_client=sheets_client,
        qa_spreadsheet_id=qa_spreadsheet_id,
        html_output_dir=html_output_dir,
    )
    result = await orchestrator.run_tests(config)

    # Log test results to sheets
    if sheets_client and qa_spreadsheet_id:
        await orchestrator.log_results_to_sheets(result)

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


class HtmlResultMetadata(BaseModel):
    """Metadata for an HTML result file."""

    filename: str
    tier: str
    company: str
    timestamp: str
    run_id: str
    size_bytes: int


class HtmlResultsList(BaseModel):
    """List of HTML result files."""

    total: int
    results: List[HtmlResultMetadata]


class DeleteResponse(BaseModel):
    """Response from delete operation."""

    message: str
    deleted: str


class DeleteAllResponse(BaseModel):
    """Response from delete all operation."""

    message: str
    deleted_count: int
    deleted_files: List[str]


def _validate_filename(filename: str) -> str:
    """
    Validate filename for security.

    Args:
        filename: Filename to validate (FastAPI automatically URL-decodes this)

    Returns:
        Validated filename (basename only)

    Raises:
        HTTPException: If filename is invalid or contains path traversal
    """
    import re
    import os
    from urllib.parse import unquote

    # FastAPI should have already URL-decoded, but double-check
    decoded_filename = unquote(filename)

    # Check for path traversal attempts FIRST (before basename strips them)
    # Check both original and decoded versions
    for name in [filename, decoded_filename]:
        if '..' in name or '/' in name or '\\' in name or ':' in name:
            raise HTTPException(
                status_code=400,
                detail="Invalid filename: path traversal not allowed"
            )

    # Strip any path components
    basename = os.path.basename(decoded_filename)

    # Validate against safe pattern
    if not re.match(r'^[A-Za-z0-9_\-]+\.html$', basename):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename format"
        )

    return basename


def _get_results_dir() -> str:
    """Get absolute path to test_results directory."""
    import os
    return os.path.abspath("test_results")


def _parse_filename_metadata(filename: str, filepath: str) -> HtmlResultMetadata:
    """
    Parse metadata from HTML result filename.

    Filename format: {tier}_{company}_{timestamp}_{run_id}.html
    Example: Standard_Acme_Corp_20231227_145030_abc12345.html

    Args:
        filename: HTML filename
        filepath: Full path to file (for getting size)

    Returns:
        HtmlResultMetadata object
    """
    import os
    from datetime import datetime

    # Get file size
    stat = os.stat(filepath)
    size_bytes = stat.st_size

    # Parse filename: remove .html extension
    name_without_ext = filename[:-5] if filename.endswith('.html') else filename
    parts = name_without_ext.split('_')

    # Extract components
    tier = parts[0] if len(parts) > 0 else 'Unknown'
    run_id = parts[-1] if len(parts) > 0 else 'Unknown'

    # Company is everything between tier and last two parts (timestamp and run_id)
    company_parts = parts[1:-2] if len(parts) > 3 else []
    company = ' '.join(company_parts) if company_parts else 'Unknown'

    # Parse timestamp
    timestamp_str = parts[-2] if len(parts) > 2 else ''
    try:
        # Parse format: YYYYMMDD_HHMMSS
        dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        timestamp = dt.isoformat()
    except (ValueError, IndexError):
        timestamp = datetime.fromtimestamp(stat.st_mtime).isoformat()

    return HtmlResultMetadata(
        filename=filename,
        tier=tier,
        company=company,
        timestamp=timestamp,
        run_id=run_id,
        size_bytes=size_bytes,
    )


@router.get("/results", response_model=HtmlResultsList)
async def list_html_results():
    """
    List all saved HTML result files.

    Returns metadata for each file sorted by timestamp (newest first).
    """
    import os

    results_dir = _get_results_dir()

    # Return empty list if directory doesn't exist
    if not os.path.exists(results_dir):
        return HtmlResultsList(total=0, results=[])

    # List all HTML files
    results = []
    for filename in os.listdir(results_dir):
        if not filename.endswith('.html'):
            continue

        filepath = os.path.join(results_dir, filename)
        if not os.path.isfile(filepath):
            continue

        try:
            metadata = _parse_filename_metadata(filename, filepath)
            results.append(metadata)
        except Exception:
            # Skip files that can't be parsed
            continue

    # Sort by timestamp descending (newest first)
    results.sort(key=lambda x: x.timestamp, reverse=True)

    return HtmlResultsList(total=len(results), results=results)


@router.get("/results/{filename}")
async def get_html_result(filename: str):
    """
    Retrieve an HTML result file.

    Args:
        filename: Name of the HTML file

    Returns:
        HTML content with proper content-type header

    Raises:
        HTTPException: 400 for invalid filename, 404 if not found
    """
    import os
    from fastapi.responses import Response

    # Validate filename
    validated_filename = _validate_filename(filename)

    # Construct path
    results_dir = _get_results_dir()
    filepath = os.path.join(results_dir, validated_filename)

    # Verify path is within results directory (prevent path traversal)
    abs_filepath = os.path.abspath(filepath)
    if not abs_filepath.startswith(results_dir):
        raise HTTPException(
            status_code=400,
            detail="Invalid file path"
        )

    # Check if file exists
    if not os.path.exists(abs_filepath):
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    # Read and return file
    try:
        with open(abs_filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        return Response(
            content=content,
            media_type="text/html; charset=utf-8"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading file: {str(e)}"
        )


@router.delete("/results/{filename}", response_model=DeleteResponse)
async def delete_html_result(filename: str):
    """
    Delete an HTML result file.

    Args:
        filename: Name of the HTML file to delete

    Returns:
        Confirmation message

    Raises:
        HTTPException: 400 for invalid filename, 404 if not found
    """
    import os

    # Validate filename
    validated_filename = _validate_filename(filename)

    # Construct path
    results_dir = _get_results_dir()
    filepath = os.path.join(results_dir, validated_filename)

    # Verify path is within results directory
    abs_filepath = os.path.abspath(filepath)
    if not abs_filepath.startswith(results_dir):
        raise HTTPException(
            status_code=400,
            detail="Invalid file path"
        )

    # Check if file exists
    if not os.path.exists(abs_filepath):
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    # Delete file
    try:
        os.remove(abs_filepath)
        return DeleteResponse(
            message=f"File {validated_filename} deleted successfully",
            deleted=validated_filename
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file: {str(e)}"
        )


@router.delete("/results", response_model=DeleteAllResponse)
async def delete_all_html_results():
    """
    Delete all HTML result files.

    Returns:
        Count and list of deleted files
    """
    import os

    results_dir = _get_results_dir()

    # Return empty result if directory doesn't exist
    if not os.path.exists(results_dir):
        return DeleteAllResponse(
            message="No files to delete",
            deleted_count=0,
            deleted_files=[]
        )

    # Find all HTML files
    deleted_files = []
    for filename in os.listdir(results_dir):
        if not filename.endswith('.html'):
            continue

        filepath = os.path.join(results_dir, filename)
        if not os.path.isfile(filepath):
            continue

        try:
            os.remove(filepath)
            deleted_files.append(filename)
        except Exception:
            # Continue deleting other files even if one fails
            continue

    return DeleteAllResponse(
        message=f"Deleted {len(deleted_files)} files",
        deleted_count=len(deleted_files),
        deleted_files=deleted_files
    )
