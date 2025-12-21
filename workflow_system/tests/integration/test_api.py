"""
Integration tests for the FastAPI application.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from web.app import app


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Tests for health check endpoints."""

    async def test_health_check(self):
        """Test basic health check."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_detailed_health_check(self):
        """Test detailed health check."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "version" in data


@pytest.mark.asyncio
class TestTestsEndpoints:
    """Tests for test runner endpoints."""

    async def test_list_test_cases(self):
        """Test listing test cases."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tests/cases?count=5")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert "cases" in data
        assert "categories" in data

    async def test_list_tiers(self):
        """Test listing available tiers."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tests/tiers")

        assert response.status_code == 200
        data = response.json()
        assert "tiers" in data
        assert len(data["tiers"]) == 4  # Budget, Standard, Premium, All

    async def test_list_environments(self):
        """Test listing available environments."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tests/environments")

        assert response.status_code == 200
        data = response.json()
        assert "environments" in data
        assert len(data["environments"]) == 2  # Production, Staging
