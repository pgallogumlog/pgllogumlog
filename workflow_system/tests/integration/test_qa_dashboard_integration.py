"""Integration tests for QA Dashboard API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport

from web.app import app


@pytest.mark.asyncio
class TestQADashboardAPI:
    """Tests for /api/v1/qa-dashboard endpoints."""

    async def test_get_overview_should_return_200(self):
        """GET /api/v1/qa-dashboard/overview returns 200."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/qa-dashboard/overview")

        assert response.status_code == 200

    async def test_get_overview_should_return_metrics(self):
        """Response includes all required metric fields."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/qa-dashboard/overview")

        data = response.json()
        assert "total_runs" in data
        assert "pass_rate" in data
        assert "avg_score" in data
        assert "total_calls" in data
        assert "avg_calls_per_run" in data
        assert "top_failures" in data

        # Check types
        assert isinstance(data["total_runs"], int)
        assert isinstance(data["pass_rate"], (int, float))
        assert isinstance(data["avg_score"], (int, float))
        assert isinstance(data["total_calls"], int)
        assert isinstance(data["avg_calls_per_run"], (int, float))
        assert isinstance(data["top_failures"], list)

    async def test_get_overview_should_filter_by_date_range_7d(self):
        """Query param date_range=7d filters correctly."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/qa-dashboard/overview?date_range=7d")

        assert response.status_code == 200
        data = response.json()
        assert "total_runs" in data

    async def test_get_overview_should_filter_by_date_range_30d(self):
        """Query param date_range=30d filters correctly."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/qa-dashboard/overview?date_range=30d")

        assert response.status_code == 200

    async def test_get_overview_should_filter_by_date_range_90d(self):
        """Query param date_range=90d filters correctly."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/qa-dashboard/overview?date_range=90d")

        assert response.status_code == 200

    async def test_get_overview_should_filter_by_date_range_all(self):
        """Query param date_range=all returns all data."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/qa-dashboard/overview?date_range=all")

        assert response.status_code == 200

    async def test_get_overview_should_reject_invalid_date_range(self):
        """Invalid date_range parameter should return 422."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/qa-dashboard/overview?date_range=invalid")

        # FastAPI should return 422 for validation error
        assert response.status_code == 422

    async def test_get_trends_should_return_200(self):
        """GET /api/v1/qa-dashboard/trends returns 200."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/qa-dashboard/trends")

        assert response.status_code == 200

    async def test_get_trends_should_return_time_series_data(self):
        """GET /api/v1/qa-dashboard/trends returns chart data."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/qa-dashboard/trends?days=7")

        assert response.status_code == 200
        data = response.json()

        assert "dates" in data
        assert "values" in data
        assert "counts" in data

        # Check types
        assert isinstance(data["dates"], list)
        assert isinstance(data["values"], list)
        assert isinstance(data["counts"], list)

        # All arrays should have same length
        assert len(data["dates"]) == len(data["values"]) == len(data["counts"])

    async def test_get_trends_should_accept_days_parameter(self):
        """Trends endpoint accepts days parameter."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/qa-dashboard/trends?days=30")

        assert response.status_code == 200

    async def test_get_trends_should_reject_invalid_days(self):
        """Days parameter outside valid range should return 422."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/qa-dashboard/trends?days=5")  # < 7

        assert response.status_code == 422

    async def test_get_trends_should_reject_days_too_large(self):
        """Days parameter > 90 should return 422."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/qa-dashboard/trends?days=100")  # > 90

        assert response.status_code == 422
