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
class TestCompassHtmlSaving:
    """Tests for Compass HTML report saving and display."""

    async def test_compass_filename_parsing(self):
        """Test that compass filename format is parsed correctly."""
        import os
        from datetime import datetime
        from web.api.tests import _parse_filename_metadata

        # Create test_results directory and compass file
        test_results_dir = "test_results"
        os.makedirs(test_results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"compass_Acme_Manufacturing_{timestamp}.html"
        filepath = os.path.join(test_results_dir, filename)

        html_content = "<html><body><h1>AI Readiness Compass Report</h1></body></html>"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        try:
            # Parse the compass filename
            metadata = _parse_filename_metadata(filename, filepath)

            # Assert: Verify compass-specific metadata
            assert metadata.filename == filename
            assert metadata.tier == "Compass", f"Expected tier='Compass', got '{metadata.tier}'"
            assert "Acme Manufacturing" in metadata.company, f"Expected company to contain 'Acme Manufacturing', got '{metadata.company}'"
            assert metadata.timestamp, "Expected valid timestamp"
            assert metadata.size_bytes > 0, "Expected file size > 0"

        finally:
            # Cleanup
            import shutil
            if os.path.exists(test_results_dir):
                shutil.rmtree(test_results_dir)

    async def test_compass_html_saving_has_logger(self):
        """Test that compass background task can run without NameError on logger."""
        # Try importing the function - this will fail if logger is not defined
        try:
            from web.api.tests import _run_compass_tests_background
            # If we can import it, logger should be accessible in the module
            import web.api.tests as tests_module
            assert hasattr(tests_module, 'logger'), "logger not defined in tests.py module"
        except NameError as e:
            pytest.fail(f"NameError when importing: {e}")

    async def test_compass_html_files_are_saved(self):
        """Test that compass tests actually save HTML files to disk."""
        import os
        import shutil
        from unittest.mock import AsyncMock, patch
        from web.api.tests import _run_compass_tests_background
        from contexts.testing.compass_orchestrator import CompassTestSuiteResult, CompassTestResult
        from contexts.testing.compass_test_cases import CompassTestCase

        # Clean up test_results directory
        test_results_dir = "test_results"
        if os.path.exists(test_results_dir):
            shutil.rmtree(test_results_dir)

        # Create mock AI provider and orchestrator
        mock_ai = AsyncMock()

        # Create a test case
        test_case = CompassTestCase(
            company_name="Test Corp",
            website="https://test.com",
            industry="Technology",
            company_size="50-200",
            category="High Readiness",
            data_maturity=8,
            automation_experience=7,
            change_readiness=9,
            pain_point="Need to scale operations",
            description="Growing tech company",
            email="test@test.com",
            contact_name="Test User",
            expected_score_range=(70, 85),
        )

        # Create a successful test result with HTML content
        test_result = CompassTestResult(
            test_case=test_case,
            run_id="test-run-123",
            success=True,
            ai_readiness_score=75.0,
            qa_passed=True,
            report_html="<html><body><h1>Test Compass Report</h1><p>AI Readiness: 75/100</p></body></html>",
        )

        # Create mock suite result
        from datetime import datetime
        mock_result = CompassTestSuiteResult(
            started_at=datetime.now(),
            completed_at=datetime.now(),
            results=[test_result],
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            avg_score=75.0,
            avg_duration=30.0,
        )

        # Mock the orchestrator to return our result
        with patch('web.api.tests.CompassTestOrchestrator') as MockOrchestrator:
            mock_orch_instance = MockOrchestrator.return_value
            mock_orch_instance.run_tests = AsyncMock(return_value=mock_result)

            # Initialize the results dictionary (normally done by run_compass_tests endpoint)
            from web.api.tests import _compass_test_results
            run_id = "test-123"
            _compass_test_results[run_id] = {
                "status": "running",
                "count": 1,
                "category": None,
                "started_at": None,
                "result": None,
            }

            # Run the background task
            await _run_compass_tests_background(
                run_id=run_id,
                test_cases=[test_case],
                max_parallel=1,
                ai_provider=mock_ai,
                email_client=None,
                save_html=True,
            )

        # Assert: Verify HTML file was saved
        try:
            html_files = [f for f in os.listdir(test_results_dir) if f.startswith('compass_') and f.endswith('.html')]
            assert len(html_files) == 1, f"Expected 1 compass HTML file, found {len(html_files)}"

            # Verify content
            html_path = os.path.join(test_results_dir, html_files[0])
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "Test Compass Report" in content, "Expected HTML content to be saved"
            assert "AI Readiness: 75/100" in content, "Expected report content in saved file"

        finally:
            # Cleanup
            if os.path.exists(test_results_dir):
                shutil.rmtree(test_results_dir)

    async def test_list_html_results_includes_compass_files(self):
        """Test that listing results includes compass HTML files."""
        import os
        from datetime import datetime

        # Create test_results directory with compass file
        test_results_dir = "test_results"
        os.makedirs(test_results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create compass format file
        compass_file = f"compass_Acme_Corp_{timestamp}.html"
        compass_path = os.path.join(test_results_dir, compass_file)
        with open(compass_path, "w", encoding="utf-8") as f:
            f.write("<html><body>Compass</body></html>")

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/tests/results")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] >= 1, f"Expected at least 1 file, got {data['total']}"

            # Find compass result
            compass_results = [r for r in data["results"] if r["tier"] == "Compass"]
            assert len(compass_results) >= 1, "Expected at least 1 compass result"

            compass_result = compass_results[0]
            assert "Acme Corp" in compass_result["company"], f"Expected 'Acme Corp' in company name, got '{compass_result['company']}'"

        finally:
            # Cleanup
            import shutil
            if os.path.exists(test_results_dir):
                shutil.rmtree(test_results_dir)
