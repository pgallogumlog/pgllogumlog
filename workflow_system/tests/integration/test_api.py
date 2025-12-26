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
