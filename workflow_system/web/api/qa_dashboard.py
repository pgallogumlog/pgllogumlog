"""QA Dashboard API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
import structlog

from contexts.qa_dashboard.aggregator import QADashboardAggregator
from contexts.qa_dashboard.data_fetcher import QADashboardDataFetcher
from config.dependency_injection import get_container

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/qa-dashboard", tags=["QA Dashboard"])


# Response Models
class OverviewResponse(BaseModel):
    """Overview metrics response."""

    total_runs: int
    pass_rate: float
    avg_score: float
    total_calls: int
    avg_calls_per_run: float
    top_failures: List[dict]


class TrendsResponse(BaseModel):
    """Trends data response."""

    dates: List[str]
    values: List[float]
    counts: List[int]


# Endpoints
@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    date_range: Optional[str] = Query("30d", regex="^(7d|30d|90d|all)$")
):
    """Get overview metrics for QA dashboard."""
    try:
        container = get_container()
        sheets_adapter = container.sheets_client()
        settings = container.settings

        data_fetcher = QADashboardDataFetcher(
            sheets_adapter=sheets_adapter,
            spreadsheet_id=settings.google_sheets_qa_log_id,
        )

        workflow_data = await data_fetcher.fetch_workflow_summary()

        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics(
            workflow_data, date_range=date_range if date_range != "all" else None
        )

        return OverviewResponse(
            total_runs=metrics.total_runs,
            pass_rate=metrics.pass_rate,
            avg_score=metrics.avg_score,
            total_calls=metrics.total_calls,
            avg_calls_per_run=metrics.avg_calls_per_run,
            top_failures=metrics.top_failures,
        )

    except Exception as e:
        logger.error("qa_dashboard.overview.error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch overview metrics")


@router.get("/trends", response_model=TrendsResponse)
async def get_trends(days: int = Query(30, ge=7, le=90)):
    """Get score trends for chart visualization."""
    try:
        container = get_container()
        sheets_adapter = container.sheets_client()
        settings = container.settings

        data_fetcher = QADashboardDataFetcher(
            sheets_adapter=sheets_adapter,
            spreadsheet_id=settings.google_sheets_qa_log_id,
        )

        workflow_data = await data_fetcher.fetch_workflow_summary()

        aggregator = QADashboardAggregator()
        trends = aggregator.get_score_trends(workflow_data, days=days)

        return TrendsResponse(dates=trends.dates, values=trends.values, counts=trends.counts)

    except Exception as e:
        logger.error("qa_dashboard.trends.error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch trend data")
