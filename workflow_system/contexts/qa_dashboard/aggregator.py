"""QA Dashboard data aggregation logic."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import statistics


@dataclass
class OverviewMetrics:
    """Aggregated overview metrics for dashboard."""

    total_runs: int
    pass_rate: float
    avg_score: float
    total_calls: int
    avg_calls_per_run: float
    top_failures: List[Dict[str, Any]]


@dataclass
class TrendData:
    """Time-series data for trend charts."""

    dates: List[str]  # ISO format dates
    values: List[float]  # Scores or counts
    counts: List[int]  # Number of runs per date


class QADashboardAggregator:
    """Aggregates raw QA data from Google Sheets into dashboard metrics."""

    def get_overview_metrics(
        self,
        workflow_data: List[Dict[str, Any]],
        date_range: Optional[str] = None,
    ) -> OverviewMetrics:
        """
        Calculate overview metrics from workflow summary data.

        Args:
            workflow_data: List of dicts from "Workflow QA Summary" sheet
            date_range: Filter to "7d", "30d", "90d", or None (all time)

        Returns:
            OverviewMetrics with aggregated statistics
        """
        if not workflow_data:
            return OverviewMetrics(
                total_runs=0,
                pass_rate=0.0,
                avg_score=0.0,
                total_calls=0,
                avg_calls_per_run=0.0,
                top_failures=[],
            )

        # Filter by date range
        filtered_data = self._filter_by_date_range(workflow_data, date_range)

        if not filtered_data:
            return OverviewMetrics(
                total_runs=0,
                pass_rate=0.0,
                avg_score=0.0,
                total_calls=0,
                avg_calls_per_run=0.0,
                top_failures=[],
            )

        # Calculate metrics
        total_runs = len(filtered_data)
        passed_runs = sum(1 for row in filtered_data if row.get("Passed") == "PASS")
        pass_rate = passed_runs / total_runs if total_runs > 0 else 0.0

        # Parse scores with error handling
        scores = []
        for row in filtered_data:
            try:
                score = float(row.get("Overall Score", 0))
                scores.append(score)
            except (ValueError, TypeError):
                # Skip invalid scores
                continue

        avg_score = statistics.mean(scores) if scores else 0.0

        # Parse total calls with error handling
        total_calls = 0
        for row in filtered_data:
            try:
                calls = int(row.get("Total Calls", 0))
                total_calls += calls
            except (ValueError, TypeError):
                # Skip invalid values
                continue

        avg_calls_per_run = total_calls / total_runs if total_runs > 0 else 0.0

        # Extract top failures (placeholder for now)
        top_failures = []  # Will implement in refactor phase

        return OverviewMetrics(
            total_runs=total_runs,
            pass_rate=pass_rate,
            avg_score=avg_score,
            total_calls=total_calls,
            avg_calls_per_run=avg_calls_per_run,
            top_failures=top_failures,
        )

    def get_score_trends(
        self,
        workflow_data: List[Dict[str, Any]],
        days: int = 30,
    ) -> TrendData:
        """
        Generate daily score trends for charting.

        Args:
            workflow_data: List of dicts from "Workflow QA Summary" sheet
            days: Number of days to include in trends

        Returns:
            TrendData with dates, scores, and counts per day
        """
        if not workflow_data:
            return TrendData(dates=[], values=[], counts=[])

        # Group by date
        daily_data: Dict[str, List[float]] = {}
        for row in workflow_data:
            timestamp_str = row.get("Timestamp", "")
            if not timestamp_str:
                continue

            try:
                date = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")).date()
                date_str = date.isoformat()

                score = float(row.get("Overall Score", 0))
                if date_str not in daily_data:
                    daily_data[date_str] = []
                daily_data[date_str].append(score)
            except (ValueError, AttributeError):
                # Skip invalid dates
                continue

        # Generate date range (last N days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)

        dates = []
        values = []
        counts = []

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            dates.append(date_str)

            day_scores = daily_data.get(date_str, [])
            avg_score = statistics.mean(day_scores) if day_scores else 0.0
            values.append(round(avg_score, 2))
            counts.append(len(day_scores))

            current_date += timedelta(days=1)

        return TrendData(dates=dates, values=values, counts=counts)

    def _filter_by_date_range(
        self,
        data: List[Dict[str, Any]],
        date_range: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Filter data to specified date range."""
        if not date_range:
            return data

        # Parse date range
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(date_range, 30)

        # Make cutoff_date timezone-aware (UTC) to match parsed timestamps
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        filtered = []
        for row in data:
            timestamp_str = row.get("Timestamp", "")
            if not timestamp_str:
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if timestamp >= cutoff_date:
                    filtered.append(row)
            except (ValueError, AttributeError):
                # Skip invalid timestamps
                continue

        return filtered
