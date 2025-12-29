"""
Priority 2: Real End-to-End Flow Tests

Tests complete user flows with REAL APIs.
NO MOCKS - Tests entire workflow from inquiry to delivery.

Cost: ~$0.40 per test (includes Sheets/Email operations)
"""

import pytest


@pytest.mark.real_api
@pytest.mark.asyncio
class TestRealEndToEndWorkflow:
    """
    End-to-end tests with REAL APIs.

    Tests complete user flows from inquiry to delivery/logging.
    """

    async def test_should_complete_full_workflow_with_real_apis(
        self,
        real_ai_provider,
        sample_test_inquiry,
    ):
        """
        TDD Test: Complete workflow from inquiry to proposal generation.

        Flow:
        1. Receive inquiry
        2. Process with real Claude API
        3. Normalize prompt (AI call)
        4. Generate research pack (AI call)
        5. Run self-consistency voting (5 parallel AI calls)
        6. Group workflows (AI call)
        7. Generate proposal HTML

        Total AI Calls: 8 (1 + 1 + 5 + 1)
        Cost: ~$0.30 per run
        """
        from contexts.workflow.engine import WorkflowEngine

        # Arrange: Set up workflow engine with real APIs
        engine = WorkflowEngine(
            ai_provider=real_ai_provider,
            min_consensus_votes=2,
        )

        # Act: Run complete workflow
        result, qa_result = await engine.process_inquiry(
            inquiry=sample_test_inquiry,
            tier="Budget",
        )

        # Assert: All workflow stages completed successfully

        # 1. Basic metadata
        assert result.run_id is not None, "Should generate run_id"
        assert result.timestamp is not None, "Should have timestamp"
        assert result.tier == "Budget", "Should record tier"

        # 2. Identity extraction
        assert result.client_name == "Test User", "Should extract client name"
        assert result.business_name, "Should extract business name"

        # 3. Prompt normalization
        assert result.normalized_prompt, "Should normalize prompt"
        assert result.normalized_prompt != result.original_question, \
            "Normalized prompt should differ from original"

        # 4. Research pack
        assert result.research_pack is not None, "Should generate research pack"
        assert isinstance(result.research_pack, dict), "Research pack should be dict"

        # 5. Self-consistency voting
        assert result.consensus is not None, "Should have consensus result"
        assert result.consensus.total_responses >= 5, "Should have 5 temperature responses"
        assert result.consensus.final_answer, "Should have final answer"
        assert len(result.consensus.all_workflows) == 3, "Budget tier should have 3 workflows"

        # 6. Workflow grouping
        assert result.proposal is not None, "Should generate proposal"
        assert len(result.proposal.phases) > 0, "Should group workflows into phases"

        # 7. HTML proposal generation
        assert result.proposal.html_body, "Should generate HTML body"
        assert result.proposal.subject, "Should generate email subject"

        # Validate HTML content
        html = result.proposal.html_body
        assert result.client_name in html, "HTML should include client name"
        assert result.business_name in html, "HTML should include business name"

        # Each workflow should appear in HTML
        for wf in result.consensus.all_workflows:
            assert wf.name in html, f"HTML should include workflow '{wf.name}'"

        # Each phase should appear in HTML
        for phase in result.proposal.phases:
            assert phase.phase_name in html, f"HTML should include phase '{phase.phase_name}'"

        # Print comprehensive results
        print(f"\n========== End-to-End Test Results ==========")
        print(f"Run ID: {result.run_id}")
        print(f"Timestamp: {result.timestamp}")
        print(f"Tier: {result.tier}")
        print(f"\nIdentity:")
        print(f"  Client: {result.client_name}")
        print(f"  Business: {result.business_name}")
        print(f"\nPrompt Processing:")
        print(f"  Original: {result.original_question[:100]}...")
        print(f"  Normalized: {result.normalized_prompt[:100]}...")
        print(f"\nResearch Pack Keys: {list(result.research_pack.keys())}")
        print(f"\nConsensus:")
        print(f"  Strength: {result.consensus.consensus_strength}")
        print(f"  Confidence: {result.consensus.confidence_percent}%")
        print(f"  Final Answer: {result.consensus.final_answer}")
        print(f"\nWorkflows: {len(result.consensus.all_workflows)}")
        for i, wf in enumerate(result.consensus.all_workflows, 1):
            print(f"  {i}. {wf.name} - {wf.objective[:50]}...")
        print(f"\nPhases: {len(result.proposal.phases)}")
        for phase in result.proposal.phases:
            print(f"  Phase {phase.phase_number}: {phase.phase_name} ({len(phase.workflows)} workflows)")
        print(f"\nProposal:")
        print(f"  Subject: {result.proposal.subject}")
        print(f"  HTML Length: {len(result.proposal.html_body)} chars")
        print(f"===========================================\n")


    @pytest.mark.sheets
    async def test_should_log_to_real_google_sheets(
        self,
        real_capturing_ai_provider,
        real_sheets_client,
        test_spreadsheet_id,
        sample_test_inquiry,
    ):
        """
        TDD Test: Complete workflow with Google Sheets logging.

        Flow:
        1. Process inquiry with QA capture enabled
        2. Log QA results to real Google Sheets
        3. Verify data was written

        NOTE: Requires TEST_SPREADSHEET_ID environment variable.
        Run with: pytest --run-sheets-tests

        Cost: ~$0.30 (Claude API) + $0 (Sheets API is free)
        """
        from contexts.workflow.engine import WorkflowEngine
        from contexts.qa.sheets_logger import QASheetsLogger

        # Arrange: Set up QA logger with real Sheets client
        qa_logger = QASheetsLogger(
            sheets_client=real_sheets_client,
            spreadsheet_id=test_spreadsheet_id,
        )

        engine = WorkflowEngine(
            ai_provider=real_capturing_ai_provider,
            min_consensus_votes=2,
            qa_sheets_logger=qa_logger,
        )

        # Act: Run workflow with QA capture
        result, qa_result = await engine.process_inquiry(
            inquiry=sample_test_inquiry,
            tier="Budget",
        )

        # Assert: QA capture worked
        call_store = real_capturing_ai_provider.call_store
        assert len(call_store.calls) > 0, "Should capture AI calls"

        # Assert: QA result generated
        assert qa_result is not None, "Should generate QA result"
        assert qa_result.overall_score > 0, "Should have overall score"

        # Assert: Workflow completed
        assert result.consensus is not None
        assert result.proposal is not None

        # Note: Actual Sheets write verification would require
        # implementing a read-back mechanism in sheets_client

        print(f"\n========== Sheets Logging Test Results ==========")
        print(f"Run ID: {result.run_id}")
        print(f"AI Calls Captured: {len(call_store.calls)}")
        print(f"QA Overall Score: {qa_result.overall_score}/10")
        print(f"QA Passed: {qa_result.passed}")
        print(f"Logged to Spreadsheet: {test_spreadsheet_id}")
        print(f"\nCaptured Calls:")
        for call in call_store.calls:
            score = call.call_score.overall_score if call.call_score else "N/A"
            print(f"  {call.call_id}: {call.method} - Score: {score}/10")
        print(f"===============================================\n")


@pytest.mark.real_api
@pytest.mark.asyncio
class TestRealMultipleTiers:
    """
    Tests for processing across different tiers.
    """

    async def test_should_handle_all_tiers_consistently(
        self,
        real_ai_provider,
    ):
        """
        TDD Test: Engine should handle Budget, Standard, and Premium tiers.

        Validates tier-specific behavior:
        - Budget: 3 workflows
        - Standard: 5 workflows
        - Premium: 5 workflows (same as Standard for now)

        Cost: ~$0.90 per run (3 tiers × $0.30)
        """
        from contexts.workflow.engine import WorkflowEngine
        from contexts.workflow.models import EmailInquiry

        # Arrange: Create inquiry
        inquiry = EmailInquiry(
            message_id="test-tiers",
            from_email="tier@example.com",
            from_name="Tier Test",
            subject="Tier Test",
            body="Recommend automation workflows for a small business.",
        )

        engine = WorkflowEngine(
            ai_provider=real_ai_provider,
            min_consensus_votes=2,
        )

        # Act: Process each tier
        results = {}
        for tier in ["Budget", "Standard", "Premium"]:
            result, _ = await engine.process_inquiry(inquiry, tier=tier)
            results[tier] = result

        # Assert: Budget tier
        assert len(results["Budget"].consensus.all_workflows) == 3, \
            "Budget tier should have 3 workflows"
        assert results["Budget"].tier == "Budget"

        # Assert: Standard tier
        assert len(results["Standard"].consensus.all_workflows) == 5, \
            "Standard tier should have 5 workflows"
        assert results["Standard"].tier == "Standard"

        # Assert: Premium tier
        assert len(results["Premium"].consensus.all_workflows) == 5, \
            "Premium tier should have 5 workflows"
        assert results["Premium"].tier == "Premium"

        # All should have valid proposals
        for tier, result in results.items():
            assert result.proposal is not None, f"{tier} should have proposal"
            assert result.proposal.html_body, f"{tier} should have HTML"
            assert len(result.proposal.phases) > 0, f"{tier} should have phases"

        print(f"\n========== Multi-Tier Test Results ==========")
        for tier, result in results.items():
            print(f"\n{tier} Tier:")
            print(f"  Run ID: {result.run_id}")
            print(f"  Workflows: {len(result.consensus.all_workflows)}")
            print(f"  Phases: {len(result.proposal.phases)}")
            print(f"  Consensus: {result.consensus.final_answer}")
            print(f"  Confidence: {result.consensus.confidence_percent}%")
        print(f"===========================================\n")
