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


@pytest.mark.asyncio
class TestSemanticRelevanceFallback:
    """Integration tests for semantic relevance in fallback scoring."""

    async def test_semantic_relevance_in_fallback_scoring(self):
        """
        Test that semantic relevance flows correctly through the full stack.

        This integration test validates:
        1. WorkflowEngine receives user inquiry
        2. Self-consistency voting fails (no consensus)
        3. Fallback scoring activates with normalized_prompt
        4. score_workflow() receives normalized_prompt parameter
        5. _calculate_semantic_relevance() computes relevance score
        6. fallback_score metric is set in ConsensusResult
        7. Workflow matching user's question scores higher

        Bug context: This test was added to catch parameter naming bugs where
        original_prompt vs normalized_prompt caused semantic relevance to fail.
        """
        from contexts.workflow.engine import WorkflowEngine
        from contexts.workflow.models import EmailInquiry
        from tests.conftest import MockAIProvider

        # Setup: Create inquiry about a specific topic (email automation)
        inquiry = EmailInquiry(
            message_id="test-123",
            from_email="test@example.com",
            from_name="Test Client",
            subject="Need workflow automation help",
            body="I need help with email automation and inbox management. We get hundreds of emails daily and need to automatically categorize and route them to the right teams.",
        )

        # Setup: Configure MockAIProvider
        mock_provider = MockAIProvider()

        # Mock table template for consistent responses
        table_template = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | {name} | {objective} | {problems} | {how} | {tools} | {metrics} | {feasibility} |

The answer is {name}"""

        # Set up all responses in order of calls
        # 5 self-consistency responses + 1 normalized prompt = 6 text responses total
        mock_provider.set_responses([
            # Response 1 (temp=0.4): Email workflow - HIGH feasibility, HIGH semantic relevance
            table_template.format(
                name="Email Triage Automation",
                objective="Email automation for inbox management - categorize and route incoming emails automatically",
                problems="High volume email inbox overload, manual email sorting and routing",
                how="Simple NLP classification with Gmail API for email categorization",
                tools="n8n, OpenAI, Gmail API",
                metrics="Email routing accuracy, Inbox management time saved",
                feasibility="High",
            ),
            # Response 2 (temp=0.6): Support Chatbot - Medium feasibility, LOW semantic relevance
            table_template.format(
                name="Customer Support Chatbot",
                objective="Automate customer support responses",
                problems="High support ticket volume",
                how="Complex custom AI chatbot with knowledge base",
                tools="n8n, Claude API, Zendesk",
                metrics="Response time, Ticket deflection",
                feasibility="Medium",
            ),
            # Response 3 (temp=0.8): Invoice workflow - Medium feasibility, LOW semantic relevance
            table_template.format(
                name="Invoice Processing System",
                objective="Automate invoice data extraction",
                problems="Manual invoice entry",
                how="Complex OCR and data extraction with multiple integrations",
                tools="Make, QuickBooks, OCR API",
                metrics="Processing time, Error rate",
                feasibility="Medium",
            ),
            # Response 4 (temp=1.0): Report workflow - Medium feasibility, LOW semantic relevance
            table_template.format(
                name="Report Generation Tool",
                objective="Automate report creation",
                problems="Manual reporting",
                how="Complex template generation with custom logic",
                tools="Make, Google Sheets",
                metrics="Time saved",
                feasibility="Medium",
            ),
            # Response 5 (temp=1.2): CRM workflow - Medium feasibility, LOW semantic relevance
            table_template.format(
                name="CRM Data Sync",
                objective="Synchronize customer data",
                problems="Manual CRM updates",
                how="Complex API integration with data validation",
                tools="Zapier, Salesforce API",
                metrics="Data accuracy",
                feasibility="Medium",
            ),
            # Normalized prompt (from input rewriter)
            "I need assistance with email automation and inbox management for routing emails",
        ])

        # Set up JSON responses (research pack and grouper)
        mock_provider.set_json_responses([
            # Research pack
            {
                "industry": "Technology",
                "business_size": "Enterprise",
                "current_tools": ["Manual email sorting"],
                "pain_points": ["Email overload", "Slow routing"],
            },
            # Grouper response
            {
                "phases": [{
                    "phaseNumber": 1,
                    "phaseName": "Quick Wins",
                    "workflows": [{
                        "name": "Email Triage Automation",
                        "objective": "Categorize emails",
                        "tools": ["Gmail API"],
                        "description": "Email automation",
                    }]
                }],
                "recommendation": "Start with email automation",
            },
        ])

        # Execute: Run workflow engine
        # Use 5 temperatures to ensure we have enough responses to avoid retries interfering
        engine = WorkflowEngine(
            ai_provider=mock_provider,
            temperatures=[0.4, 0.6, 0.8, 1.0, 1.2],  # 5 responses
            min_consensus_votes=5,  # Require 5 votes (will fail - only 1 vote each)
        )

        result, qa_result = await engine.process_inquiry(inquiry, tier="Standard")

        # Assert: Verify fallback scoring was activated
        assert result.consensus.had_consensus is False, (
            "Expected no consensus (5 different workflows with 1 vote each)"
        )

        # Assert: Verify semantic relevance influenced the final answer
        # Email-related workflow should win because it has high semantic relevance
        # to the user's email question (checking for email/triage keywords)
        final_answer_lower = result.consensus.final_answer.lower()
        assert "email" in final_answer_lower and "triage" in final_answer_lower, (
            f"Expected an email triage workflow to win via semantic relevance, "
            f"but got '{result.consensus.final_answer}'. "
            f"Semantic relevance should boost email-related workflow above generic workflows."
        )

        # Assert: Verify fallback_score metrics were set
        assert result.consensus.confidence_percent > 0, (
            "Expected fallback_score to set confidence_percent > 0"
        )

        assert "Fallback" in result.consensus.consensus_strength, (
            f"Expected consensus_strength to indicate 'Fallback' scoring, "
            f"but got '{result.consensus.consensus_strength}'"
        )

        # Assert: Verify workflows are populated
        assert len(result.consensus.all_workflows) >= 5, (
            "Expected at least 5 workflows from fallback scoring"
        )

        # Assert: Verify the first workflow matches the semantic query
        first_workflow = result.consensus.all_workflows[0]
        first_name_lower = first_workflow.name.lower()
        assert "email" in first_name_lower and "triage" in first_name_lower, (
            f"Expected email triage workflow to be ranked first, got '{first_workflow.name}'"
        )


@pytest.mark.asyncio
class TestHtmlResultsEndpoints:
    """Tests for HTML results management endpoints."""

    async def test_run_tests_with_save_html_enabled(self):
        """Test running tests with save_html parameter."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/tests/run",
                json={
                    "environment": "Production",
                    "tier": "Standard",
                    "count": 1,
                    "parallel": False,
                    "save_html": True,
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["message"]
        assert data["total_tests"] >= 1

    async def test_list_html_results_empty(self):
        """Test listing HTML results when directory is empty."""
        import os
        import shutil

        # Clean up test_results directory
        test_results_dir = "test_results"
        if os.path.exists(test_results_dir):
            shutil.rmtree(test_results_dir)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tests/results")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["results"] == []

    async def test_list_html_results_with_files(self):
        """Test listing HTML results with existing files."""
        import os
        from datetime import datetime

        # Create test_results directory and sample files
        test_results_dir = "test_results"
        os.makedirs(test_results_dir, exist_ok=True)

        # Create sample HTML files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_files = [
            f"Standard_Test_Company_{timestamp}_abc12345.html",
            f"Premium_Another_Corp_{timestamp}_def67890.html",
        ]

        for filename in test_files:
            filepath = os.path.join(test_results_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("<html><body>Test workflow</body></html>")

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/tests/results")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert len(data["results"]) == 2

            # Verify metadata structure
            result = data["results"][0]
            assert "filename" in result
            assert "tier" in result
            assert "company" in result
            assert "timestamp" in result
            assert "run_id" in result
            assert "size_bytes" in result

        finally:
            # Cleanup
            import shutil
            if os.path.exists(test_results_dir):
                shutil.rmtree(test_results_dir)

    async def test_get_html_file_success(self):
        """Test retrieving an HTML file."""
        import os
        from datetime import datetime

        # Create test file
        test_results_dir = "test_results"
        os.makedirs(test_results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Standard_Test_Company_{timestamp}_abc12345.html"
        filepath = os.path.join(test_results_dir, filename)

        html_content = "<html><body><h1>Test Workflow Proposal</h1></body></html>"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/tests/results/{filename}")

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/html; charset=utf-8"
            assert html_content in response.text

        finally:
            # Cleanup
            import shutil
            if os.path.exists(test_results_dir):
                shutil.rmtree(test_results_dir)

    async def test_get_html_file_not_found(self):
        """Test retrieving a non-existent HTML file."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tests/results/nonexistent.html")

        assert response.status_code == 404

    async def test_get_html_file_path_traversal_attack(self):
        """Test that path traversal attacks are blocked."""
        from urllib.parse import quote
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Try various path traversal attacks with .html extension
            # These need to be URL-encoded to pass FastAPI routing
            malicious_filenames = [
                quote("../../../config.html", safe=''),
                quote("..\\..\\windows\\system32\\config.html", safe=''),
                quote("test/../config.html", safe=''),
            ]

            for malicious_name in malicious_filenames:
                response = await client.get(f"/api/tests/results/{malicious_name}")
                # Accept 400 (validation error) or 404 (routing blocked) - both indicate blocked access
                assert response.status_code in [400, 404], f"Path traversal not blocked for: {malicious_name}, got {response.status_code}"

    async def test_delete_html_file_success(self):
        """Test deleting an HTML file."""
        import os
        from datetime import datetime

        # Create test file
        test_results_dir = "test_results"
        os.makedirs(test_results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Standard_Test_Company_{timestamp}_abc12345.html"
        filepath = os.path.join(test_results_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("<html><body>Test</body></html>")

        assert os.path.exists(filepath)

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete(f"/api/tests/results/{filename}")

            assert response.status_code == 200
            data = response.json()
            assert data["deleted"] == filename
            assert "deleted successfully" in data["message"].lower()

            # Verify file is actually deleted
            assert not os.path.exists(filepath)

        finally:
            # Cleanup
            import shutil
            if os.path.exists(test_results_dir):
                shutil.rmtree(test_results_dir)

    async def test_delete_html_file_not_found(self):
        """Test deleting a non-existent file."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/api/tests/results/nonexistent.html")

        assert response.status_code == 404

    async def test_delete_html_file_path_traversal_attack(self):
        """Test that path traversal is blocked in delete operation."""
        from urllib.parse import quote
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            malicious_name = quote("../../../config.html", safe='')
            response = await client.delete(f"/api/tests/results/{malicious_name}")

        # Accept 400 (validation error) or 404 (routing blocked) - both indicate blocked access
        assert response.status_code in [400, 404]

    async def test_delete_all_html_files_success(self):
        """Test deleting all HTML files."""
        import os
        from datetime import datetime

        # Create test files
        test_results_dir = "test_results"
        os.makedirs(test_results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_files = [
            f"Standard_Company_A_{timestamp}_abc12345.html",
            f"Premium_Company_B_{timestamp}_def67890.html",
            f"Budget_Company_C_{timestamp}_ghi11111.html",
        ]

        for filename in test_files:
            filepath = os.path.join(test_results_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("<html><body>Test</body></html>")

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete("/api/tests/results")

            assert response.status_code == 200
            data = response.json()
            assert data["deleted_count"] == 3
            assert len(data["deleted_files"]) == 3

            # Verify all files are deleted
            for filename in test_files:
                filepath = os.path.join(test_results_dir, filename)
                assert not os.path.exists(filepath)

        finally:
            # Cleanup
            import shutil
            if os.path.exists(test_results_dir):
                shutil.rmtree(test_results_dir)

    async def test_delete_all_html_files_empty_directory(self):
        """Test deleting all files when directory is empty."""
        import os
        import shutil

        # Clean up test_results directory
        test_results_dir = "test_results"
        if os.path.exists(test_results_dir):
            shutil.rmtree(test_results_dir)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/api/tests/results")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 0
        assert data["deleted_files"] == []


@pytest.mark.asyncio
class TestTwentyFiveWorkflowConsensus:
    """Integration tests for 25-workflow self-consistency voting."""

    async def test_end_to_end_125_workflows_to_top_5_output(self):
        """
        Test end-to-end flow: 125 workflows (5×25) → consensus voting → top 5 output.

        Validates:
        1. Engine generates 5 responses at different temperatures
        2. Each response contains 25 workflows (125 total)
        3. Consensus voting processes all 125 workflows
        4. Output contains exactly 5 workflows ranked by vote count
        5. Fallback logic still works with 25-workflow tables
        """
        from contexts.workflow.engine import WorkflowEngine
        from contexts.workflow.models import EmailInquiry
        from tests.conftest import MockAIProvider

        # Setup: Create inquiry
        inquiry = EmailInquiry(
            message_id="test-125-workflows",
            from_email="test@example.com",
            from_name="Test Client",
            subject="Need workflow automation",
            body="I need help automating my business operations and improving efficiency across all departments.",
        )

        # Setup: Configure MockAIProvider with 25-row tables
        mock_provider = MockAIProvider()

        # Build 25-row table template
        table_header = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|------------------------|--------------|-------------------|-------------|-------------|"""

        # Create 25 rows for a table
        def build_25_row_table(response_num, consensus_workflow="Efficiency Dashboard"):
            rows = [
                f"| 1 | {consensus_workflow} | Track KPIs | Manual reporting | Automated BI | Tableau | Accuracy | High |",
                f"| 2 | Email Automation {response_num} | Auto-respond | Volume | AI triage | Gmail | Speed | High |",
                f"| 3 | Lead Scoring {response_num} | Prioritize | Manual | ML | Zapier | Conv | Medium |",
                f"| 4 | Invoice Processing {response_num} | Extract data | Manual entry | OCR | QuickBooks | Time | Medium |",
                f"| 5 | Report Generator {response_num} | Create reports | Manual | Templates | Sheets | Quality | High |",
                f"| 6 | CRM Sync {response_num} | Sync data | Outdated | API | Salesforce | Accuracy | Medium |",
                f"| 7 | Social Media {response_num} | Schedule | Manual | Calendar | Buffer | Engagement | High |",
                f"| 8 | Support Bot {response_num} | Auto-respond | Volume | Chatbot | Zendesk | Response | High |",
                f"| 9 | Data Entry {response_num} | Automate | Manual | RPA | UiPath | Speed | Medium |",
                f"| 10 | Onboarding {response_num} | Onboard | Slow | Workflow | n8n | Time | High |",
                f"| 11 | Analytics {response_num} | Insights | Manual | BI | Looker | Accuracy | Medium |",
                f"| 12 | Scheduling {response_num} | Auto-schedule | Manual | Sync | Calendly | Bookings | High |",
                f"| 13 | Inventory {response_num} | Track stock | Manual | Barcode | ShipStation | Accuracy | Medium |",
                f"| 14 | Payroll {response_num} | Process | Manual | Auto | Gusto | Speed | Medium |",
                f"| 15 | Compliance {response_num} | Track | Manual | Checklist | Asana | Completion | High |",
                f"| 16 | Marketing {response_num} | Campaigns | Manual | Sequences | HubSpot | ROI | Medium |",
                f"| 17 | Sales Pipeline {response_num} | Track | Manual | CRM | Pipedrive | Conv | Medium |",
                f"| 18 | Recruiting {response_num} | Screen | Manual | AI | Lever | Hire time | High |",
                f"| 19 | Expense Tracking {response_num} | Track | Manual | OCR | Expensify | Accuracy | High |",
                f"| 20 | Contract Mgmt {response_num} | Manage | Manual | Workflow | DocuSign | Turnaround | Medium |",
                f"| 21 | Feedback Loop {response_num} | Collect | Manual | Surveys | Typeform | Response | High |",
                f"| 22 | Training Delivery {response_num} | Deliver | Manual | LMS | Teachable | Completion | Medium |",
                f"| 23 | Quality Checks {response_num} | Check | Manual | Inspection | QualityAI | Defects | High |",
                f"| 24 | Logistics Routing {response_num} | Optimize | Manual | Routes | Route4Me | Delivery | Medium |",
                f"| 25 | Pricing Engine {response_num} | Dynamic | Static | Algorithm | Price2Spy | Margin | Medium |",
            ]
            return table_header + "\n" + "\n".join(rows) + f"\n\nThe answer is {consensus_workflow}"

        # Set up responses:
        # 1. Normalized prompt (from input rewriter) - FIRST
        # 2. Then 5 self-consistency responses with 25 workflows each
        mock_provider.set_responses([
            "I need help automating business operations and efficiency improvements",  # Normalized prompt
            build_25_row_table(1, "Efficiency Dashboard"),  # temp=0.4
            build_25_row_table(2, "Efficiency Dashboard"),  # temp=0.6
            build_25_row_table(3, "Efficiency Dashboard"),  # temp=0.8
            build_25_row_table(4, "Efficiency Dashboard"),  # temp=1.0
            build_25_row_table(5, "Efficiency Dashboard"),  # temp=1.2
        ])

        # Set up JSON responses
        mock_provider.set_json_responses([
            # Research pack
            {
                "industry": "Technology",
                "business_size": "SMB",
                "pain_points": ["Manual processes", "Low efficiency"],
            },
            # Grouper response
            {
                "phases": [{
                    "phaseNumber": 1,
                    "phaseName": "Foundation",
                    "workflows": [{
                        "name": "Efficiency Dashboard",
                        "objective": "Track KPIs",
                        "tools": ["Tableau"],
                        "description": "Automated BI dashboard",
                    }]
                }],
                "recommendation": "Start with efficiency tracking",
            },
        ])

        # Execute: Run workflow engine
        engine = WorkflowEngine(
            ai_provider=mock_provider,
            temperatures=[0.4, 0.6, 0.8, 1.0, 1.2],
            min_consensus_votes=3,  # Need 3/5 votes for consensus
        )

        result, qa_result = await engine.process_inquiry(inquiry, tier="Standard")

        # Assert: Consensus should be reached (all 5 voted for "Efficiency Dashboard")
        assert result.consensus.had_consensus is True
        assert result.consensus.votes_for_winner == 5
        assert "Efficiency Dashboard" in result.consensus.final_answer

        # Assert: Output should contain exactly 5 workflows (not 25, not 125)
        assert len(result.consensus.all_workflows) == 5, (
            f"Expected exactly 5 workflows in output, got {len(result.consensus.all_workflows)}"
        )

        # Assert: Top workflow should be "Efficiency Dashboard" (consensus winner)
        assert result.consensus.all_workflows[0].name == "Efficiency Dashboard"

        # Assert: Confidence metrics should reflect strong consensus
        assert result.consensus.confidence_percent == 100
        assert result.consensus.consensus_strength == "Strong"
