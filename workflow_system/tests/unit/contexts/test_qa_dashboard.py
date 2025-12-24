"""Unit tests for QA Dashboard aggregation logic."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock


class TestQADashboardAggregator:
    """Tests for QADashboardAggregator data transformations."""

    @pytest.fixture
    def sample_workflow_data(self):
        """Mock workflow summary data from Sheets."""
        # Generate sample data spanning 30 days
        base_date = datetime.now() - timedelta(days=30)
        data = []

        for i in range(10):
            date = base_date + timedelta(days=i * 3)
            # Create varied scores and pass/fail status
            score = 7.0 + (i % 3)  # Scores: 7.0, 8.0, 9.0, 7.0, ...
            passed = "PASS" if score >= 7.0 else "FAIL"

            data.append({
                "Timestamp": date.isoformat() + "Z",
                "Run ID": f"run-{i:03d}",
                "Client": "Test Client",
                "Overall Score": str(score),
                "Passed": passed,
                "Total Calls": str(5 + i),  # Varies from 5 to 14
            })

        return data

    def test_should_calculate_total_runs(self, sample_workflow_data):
        """Count total workflow runs in dataset."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics(sample_workflow_data)
        assert metrics.total_runs == 10

    def test_should_calculate_pass_rate(self, sample_workflow_data):
        """Calculate percentage of runs with PASS status."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics(sample_workflow_data)

        # All 10 samples have score >= 7.0, so all should pass
        assert metrics.pass_rate == 1.0

    def test_should_calculate_average_score(self, sample_workflow_data):
        """Calculate mean score from Overall Score column."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics(sample_workflow_data)

        # Scores cycle: 7.0, 8.0, 9.0, 7.0, 8.0, 9.0, 7.0, 8.0, 9.0, 7.0
        # Average = (7+8+9+7+8+9+7+8+9+7) / 10 = 79/10 = 7.9
        assert abs(metrics.avg_score - 7.9) < 0.01

    def test_should_calculate_total_calls(self, sample_workflow_data):
        """Sum total calls from all runs."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics(sample_workflow_data)

        # Total Calls: 5+6+7+8+9+10+11+12+13+14 = 95
        assert metrics.total_calls == 95

    def test_should_calculate_avg_calls_per_run(self, sample_workflow_data):
        """Calculate average calls per workflow run."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics(sample_workflow_data)

        # 95 total calls / 10 runs = 9.5
        assert abs(metrics.avg_calls_per_run - 9.5) < 0.01

    def test_should_handle_empty_dataset_gracefully(self):
        """Return zero metrics when no data available."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics([])

        assert metrics.total_runs == 0
        assert metrics.pass_rate == 0.0
        assert metrics.avg_score == 0.0
        assert metrics.total_calls == 0
        assert metrics.avg_calls_per_run == 0.0
        assert metrics.top_failures == []

    def test_should_filter_by_date_range_7d(self, sample_workflow_data):
        """Filter to last 7 days when date_range='7d'."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        aggregator = QADashboardAggregator()

        # Modify sample data to have some recent runs
        recent_data = []
        for i in range(3):
            date = datetime.now() - timedelta(days=i)
            recent_data.append({
                "Timestamp": date.isoformat() + "Z",
                "Run ID": f"recent-{i}",
                "Client": "Test Client",
                "Overall Score": "8.0",
                "Passed": "PASS",
                "Total Calls": "5",
            })

        # Add older data (should be filtered out)
        old_date = datetime.now() - timedelta(days=10)
        recent_data.append({
            "Timestamp": old_date.isoformat() + "Z",
            "Run ID": "old-run",
            "Client": "Test Client",
            "Overall Score": "7.0",
            "Passed": "PASS",
            "Total Calls": "5",
        })

        metrics = aggregator.get_overview_metrics(recent_data, date_range='7d')

        # Should only include the 3 recent runs, not the old one
        assert metrics.total_runs == 3

    def test_should_filter_by_date_range_30d(self, sample_workflow_data):
        """Filter to last 30 days when date_range='30d'."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics(sample_workflow_data, date_range='30d')

        # Most or all sample data should be within 30 days (edge case tolerance)
        assert 9 <= metrics.total_runs <= 10

    def test_should_return_all_data_when_date_range_is_none(self, sample_workflow_data):
        """Return all data when date_range is None."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics(sample_workflow_data, date_range=None)

        assert metrics.total_runs == 10

    def test_should_aggregate_daily_scores_for_trends(self, sample_workflow_data):
        """Group by date and calculate avg score per day."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        aggregator = QADashboardAggregator()
        trends = aggregator.get_score_trends(sample_workflow_data, days=7)

        # Should return data for last 7 days
        assert len(trends.dates) == 7
        assert len(trends.values) == 7
        assert len(trends.counts) == 7

        # Each value should be a float (score or 0 for days with no data)
        for value in trends.values:
            assert isinstance(value, float)
            assert 0.0 <= value <= 10.0

    def test_should_handle_empty_dataset_for_trends(self):
        """Return empty trend data when no data available."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        aggregator = QADashboardAggregator()
        trends = aggregator.get_score_trends([], days=7)

        assert trends.dates == []
        assert trends.values == []
        assert trends.counts == []

    def test_should_fill_missing_dates_in_trends(self):
        """Fill dates with no runs with zero values."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        # Create data with gaps
        data = [
            {
                "Timestamp": (datetime.now() - timedelta(days=2)).isoformat() + "Z",
                "Run ID": "run-1",
                "Client": "Test Client",
                "Overall Score": "8.0",
                "Passed": "PASS",
                "Total Calls": "5",
            }
        ]

        aggregator = QADashboardAggregator()
        trends = aggregator.get_score_trends(data, days=7)

        # Should return 7 dates, but most will have count=0
        assert len(trends.dates) == 7
        assert len(trends.counts) == 7

        # Count of runs with no data should be 0
        zero_count = sum(1 for c in trends.counts if c == 0)
        assert zero_count == 6  # 6 days with no data


class TestQADashboardEdgeCases:
    """Edge cases and error handling tests."""

    def test_should_handle_malformed_sheets_data(self):
        """Gracefully handle missing columns or invalid data types."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        malformed_data = [
            {"Timestamp": "invalid-date", "Overall Score": "not-a-number"},
            {"Run ID": "missing-timestamp"},
            {"Timestamp": datetime.now().isoformat() + "Z"},  # Missing score
        ]
        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics(malformed_data)

        # Should not crash, return defaults
        assert metrics.total_runs >= 0
        assert 0.0 <= metrics.pass_rate <= 1.0
        assert metrics.avg_score >= 0.0

    def test_should_handle_division_by_zero(self):
        """Handle cases where total_runs is 0."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics([])

        assert metrics.pass_rate == 0.0
        assert metrics.avg_calls_per_run == 0.0
        assert metrics.avg_score == 0.0

    def test_should_handle_missing_score_field(self):
        """Handle data rows without Overall Score field."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        data = [
            {
                "Timestamp": (datetime.now() - timedelta(days=1)).isoformat() + "Z",
                "Run ID": "run-1",
                "Passed": "PASS",
                "Total Calls": "5",
                # Missing Overall Score
            }
        ]

        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics(data)

        # Should handle gracefully
        assert metrics.total_runs == 1
        assert metrics.avg_score >= 0.0

    def test_should_handle_missing_calls_field(self):
        """Handle data rows without Total Calls field."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        data = [
            {
                "Timestamp": (datetime.now() - timedelta(days=1)).isoformat() + "Z",
                "Run ID": "run-1",
                "Overall Score": "8.0",
                "Passed": "PASS",
                # Missing Total Calls
            }
        ]

        aggregator = QADashboardAggregator()
        metrics = aggregator.get_overview_metrics(data)

        # Should handle gracefully
        assert metrics.total_runs == 1
        assert metrics.total_calls == 0

    def test_should_handle_non_numeric_score(self):
        """Handle non-numeric values in Overall Score field."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        data = [
            {
                "Timestamp": (datetime.now() - timedelta(days=1)).isoformat() + "Z",
                "Run ID": "run-1",
                "Overall Score": "not-a-number",
                "Passed": "PASS",
                "Total Calls": "5",
            }
        ]

        aggregator = QADashboardAggregator()
        # Should not crash
        try:
            metrics = aggregator.get_overview_metrics(data)
            assert metrics.total_runs >= 0
        except ValueError:
            # Acceptable to raise ValueError for invalid data
            pass

    def test_should_handle_invalid_date_strings(self):
        """Handle invalid date strings in Timestamp field."""
        from contexts.qa_dashboard.aggregator import QADashboardAggregator

        data = [
            {
                "Timestamp": "not-a-date",
                "Run ID": "run-1",
                "Overall Score": "8.0",
                "Passed": "PASS",
                "Total Calls": "5",
            }
        ]

        aggregator = QADashboardAggregator()
        # Should not crash, may skip invalid entries
        try:
            metrics = aggregator.get_overview_metrics(data, date_range="7d")
            assert metrics.total_runs >= 0
        except (ValueError, AttributeError):
            # Acceptable to raise error for invalid dates
            pass


class TestQADashboardDataFetcher:
    """Tests for fetching data from Google Sheets."""

    @pytest.fixture
    def mock_sheets_adapter(self):
        """Mock SheetsAdapter for testing."""
        mock = Mock()
        mock.read_sheet = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_should_fetch_workflow_summary_from_sheets(self, mock_sheets_adapter):
        """Fetch data from 'Workflow QA Summary' sheet."""
        from contexts.qa_dashboard.data_fetcher import QADashboardDataFetcher

        # Arrange
        mock_sheets_adapter.read_sheet.return_value = [{"Run ID": "test-run"}]
        fetcher = QADashboardDataFetcher(
            sheets_adapter=mock_sheets_adapter, spreadsheet_id="test-sheet-id"
        )

        # Act
        data = await fetcher.fetch_workflow_summary()

        # Assert
        assert len(data) == 1
        assert data[0]["Run ID"] == "test-run"
        mock_sheets_adapter.read_sheet.assert_called_once_with(
            spreadsheet_id="test-sheet-id", sheet_name="Workflow QA Summary"
        )

    @pytest.mark.asyncio
    async def test_should_cache_data_for_5_minutes(self, mock_sheets_adapter):
        """Don't refetch if called within 5-minute cache window."""
        from contexts.qa_dashboard.data_fetcher import QADashboardDataFetcher

        # Arrange
        mock_sheets_adapter.read_sheet.return_value = [{"Run ID": "test-run"}]
        fetcher = QADashboardDataFetcher(
            sheets_adapter=mock_sheets_adapter,
            spreadsheet_id="test-sheet-id",
            cache_ttl_seconds=300,
        )

        # Act: Fetch twice within cache window
        data1 = await fetcher.fetch_workflow_summary()
        data2 = await fetcher.fetch_workflow_summary()

        # Assert: Only called once (second call uses cache)
        assert mock_sheets_adapter.read_sheet.call_count == 1
        assert data1 == data2

    @pytest.mark.asyncio
    async def test_should_handle_sheets_api_errors_gracefully(self, mock_sheets_adapter):
        """Return empty list if Sheets API fails, log error."""
        from contexts.qa_dashboard.data_fetcher import QADashboardDataFetcher

        # Arrange
        mock_sheets_adapter.read_sheet.side_effect = Exception("API Error")
        fetcher = QADashboardDataFetcher(
            sheets_adapter=mock_sheets_adapter, spreadsheet_id="test-sheet-id"
        )

        # Act
        data = await fetcher.fetch_workflow_summary()

        # Assert
        assert data == []
        # Verify API was called
        mock_sheets_adapter.read_sheet.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_return_cached_data_on_subsequent_calls(
        self, mock_sheets_adapter
    ):
        """Cached data is returned without making additional API calls."""
        from contexts.qa_dashboard.data_fetcher import QADashboardDataFetcher

        # Arrange
        mock_sheets_adapter.read_sheet.return_value = [
            {"Run ID": "run-1"},
            {"Run ID": "run-2"},
        ]
        fetcher = QADashboardDataFetcher(
            sheets_adapter=mock_sheets_adapter,
            spreadsheet_id="test-sheet-id",
            cache_ttl_seconds=300,
        )

        # Act: Multiple fetches
        data1 = await fetcher.fetch_workflow_summary()
        data2 = await fetcher.fetch_workflow_summary()
        data3 = await fetcher.fetch_workflow_summary()

        # Assert: API called only once
        assert mock_sheets_adapter.read_sheet.call_count == 1
        assert len(data1) == 2
        assert data1 == data2 == data3
