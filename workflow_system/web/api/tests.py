"""
Test Runner API endpoints - Compass Tests and HTML Results.
"""

from __future__ import annotations

from typing import List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from config import get_container
from contexts.testing.compass_test_cases import COMPASS_TEST_CASES, get_compass_test_cases
from contexts.testing.compass_orchestrator import CompassTestOrchestrator

logger = structlog.get_logger()
router = APIRouter()


# ===================
# HTML RESULTS MODELS AND ENDPOINTS
# ===================

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

    Supports Compass format: compass_{company}_{timestamp}.html
    Example: compass_Acme_Corp_20231227_145030.html

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

    # Check if this is a compass format file
    if parts[0].lower() == 'compass':
        # Compass format: compass_{company}_{YYYYMMDD_HHMMSS}.html
        tier = 'Compass'

        # Timestamp is last TWO parts joined: YYYYMMDD_HHMMSS
        if len(parts) >= 3:
            timestamp_str = f"{parts[-2]}_{parts[-1]}"
            # Company is everything between 'compass' and last two parts
            company_parts = parts[1:-2]
        else:
            timestamp_str = parts[-1] if len(parts) > 1 else ''
            company_parts = []

        company = ' '.join(company_parts) if company_parts else 'Unknown'

        # No run_id in compass format, use date portion as run_id
        run_id = parts[-2] if len(parts) >= 3 else 'unknown'

    else:
        # Legacy format or unknown: treat first part as tier
        tier = parts[0] if len(parts) > 0 else 'Unknown'
        run_id = parts[-1] if len(parts) > 0 else 'Unknown'

        # Company is everything between tier and last two parts
        company_parts = parts[1:-2] if len(parts) > 3 else []
        company = ' '.join(company_parts) if company_parts else 'Unknown'

        # Timestamp is second to last part
        timestamp_str = parts[-2] if len(parts) > 2 else ''

    # Parse timestamp
    try:
        # Parse format: YYYYMMDD_HHMMSS or YYYYMMDD
        if '_' in timestamp_str:
            dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        elif len(timestamp_str) >= 8:
            dt = datetime.strptime(timestamp_str[:8], '%Y%m%d')
        else:
            raise ValueError("Invalid timestamp format")
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


# ===================
# COMPASS TEST ENDPOINTS
# ===================

# Store for compass test results (in-memory for now)
_compass_test_results: dict = {}


class CompassTestRunRequest(BaseModel):
    """Request to run Compass tests."""

    count: int = Field(default=5, ge=1, le=15)
    category: Optional[str] = None  # e.g., "Low Readiness", "High Readiness"
    max_parallel: int = Field(default=3, ge=1, le=5)
    save_html: bool = Field(default=True)  # Save HTML reports to disk


class CompassTestCaseInfo(BaseModel):
    """Information about a Compass test case."""

    company_name: str
    industry: str
    company_size: str
    category: str
    data_maturity: int
    automation_experience: int
    change_readiness: int
    pain_point: str
    expected_score_range: Optional[tuple]


@router.get("/compass/cases")
async def list_compass_test_cases(
    count: int = 15,
    category: Optional[str] = None,
):
    """List available Compass test cases."""
    cases = get_compass_test_cases(count)

    if category:
        cases = [c for c in cases if c.category == category]

    categories = list(set(c.category for c in COMPASS_TEST_CASES))

    return {
        "total": len(cases),
        "categories": categories,
        "cases": [
            {
                "company_name": c.company_name,
                "industry": c.industry,
                "company_size": c.company_size,
                "category": c.category,
                "data_maturity": c.data_maturity,
                "automation_experience": c.automation_experience,
                "change_readiness": c.change_readiness,
                "pain_point": c.pain_point,
                "expected_score_range": c.expected_score_range,
            }
            for c in cases
        ],
    }


@router.post("/compass/run")
async def run_compass_tests(
    request: CompassTestRunRequest,
    background_tasks: BackgroundTasks,
):
    """
    Run Compass tests.

    Tests run in the background. Use /tests/compass/status/{run_id} to check progress.
    """
    import uuid

    container = get_container()
    run_id = f"compass-test-{uuid.uuid4().hex[:8]}"

    # Get AI provider
    ai_provider = container.ai_provider()

    # Get email client (optional)
    try:
        email_client = container.email_client()
    except Exception:
        email_client = None

    # Get sheets logger for QA logging (optional)
    try:
        sheets_logger = container.compass_sheets_logger()
    except Exception:
        sheets_logger = None

    # Store initial status
    _compass_test_results[run_id] = {
        "status": "running",
        "count": request.count,
        "category": request.category,
        "started_at": None,
        "result": None,
    }

    # Add background task
    background_tasks.add_task(
        _run_compass_tests_background,
        run_id=run_id,
        count=request.count,
        category=request.category,
        max_parallel=request.max_parallel,
        ai_provider=ai_provider,
        email_client=email_client,
        sheets_logger=sheets_logger,
        save_html=request.save_html,
    )

    return {
        "message": f"Compass test run initiated with {request.count} tests",
        "run_id": run_id,
        "count": request.count,
        "category": request.category,
        "status_url": f"/api/tests/compass/status/{run_id}",
    }


async def _run_compass_tests_background(
    run_id: str,
    count: int,
    category: Optional[str],
    max_parallel: int,
    ai_provider,
    email_client=None,
    sheets_logger=None,
    save_html: bool = True,
):
    """Run Compass tests in the background."""
    from datetime import datetime
    from pathlib import Path

    _compass_test_results[run_id]["started_at"] = datetime.now().isoformat()

    try:
        orchestrator = CompassTestOrchestrator(
            ai_provider=ai_provider,
            email_client=email_client,
            sheets_logger=sheets_logger,
            max_parallel=max_parallel,
        )

        result = await orchestrator.run_tests(
            count=count,
            category=category,
        )

        # Save HTML reports if requested
        html_save_errors = []
        try:
            logger.info(
                "compass_html_save_check",
                save_html=save_html,
                result_count=len(result.results) if result.results else 0,
            )
            if save_html and result.results:
                html_dir = Path("test_results")
                html_dir.mkdir(parents=True, exist_ok=True)
                logger.info("compass_html_dir_created", dir=str(html_dir.absolute()))

                for test_result in result.results:
                    logger.info(
                        "compass_html_check_result",
                        company=test_result.company_name,
                        success=test_result.success,
                        has_html=bool(test_result.report_html),
                        html_length=len(test_result.report_html) if test_result.report_html else 0,
                    )
                    if test_result.success and test_result.report_html:
                        # Create filename from company name and timestamp
                        company_slug = test_result.company_name.replace(" ", "_").replace("/", "-")[:50]
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"compass_{company_slug}_{timestamp}.html"
                        filepath = html_dir / filename

                        filepath.write_text(test_result.report_html, encoding="utf-8")
                        logger.info("compass_html_saved", filepath=str(filepath))
        except Exception as html_error:
            logger.error("compass_html_save_failed", error=str(html_error))
            html_save_errors.append(str(html_error))

        _compass_test_results[run_id]["status"] = "completed"
        _compass_test_results[run_id]["result"] = result.to_dict()
        if html_save_errors:
            _compass_test_results[run_id]["html_save_errors"] = html_save_errors

    except Exception as e:
        _compass_test_results[run_id]["status"] = "failed"
        _compass_test_results[run_id]["error"] = str(e)


@router.get("/compass/status/{run_id}")
async def get_compass_test_status(run_id: str):
    """Get status of a Compass test run."""
    if run_id not in _compass_test_results:
        raise HTTPException(
            status_code=404,
            detail=f"Test run not found: {run_id}",
        )

    return _compass_test_results[run_id]


@router.get("/compass/results")
async def list_compass_test_results():
    """List all Compass test run results."""
    return {
        "total": len(_compass_test_results),
        "runs": [
            {
                "run_id": run_id,
                "status": data["status"],
                "count": data.get("count"),
                "category": data.get("category"),
                "started_at": data.get("started_at"),
                "passed": data.get("result", {}).get("passed_tests") if data.get("result") else None,
                "failed": data.get("result", {}).get("failed_tests") if data.get("result") else None,
                "avg_score": data.get("result", {}).get("avg_score") if data.get("result") else None,
            }
            for run_id, data in _compass_test_results.items()
        ],
    }
