"""
Priority 1: Real API Core Workflow Tests

Tests the core WorkflowEngine with REAL Claude API.
NO MOCKS - All tests call actual Claude API.

Cost: ~$0.30 per test run (5 parallel Claude API calls)
"""

import pytest


@pytest.mark.real_api
@pytest.mark.asyncio
class TestRealWorkflowEngine:
    """
    Real API tests for WorkflowEngine.

    These tests call the actual Claude API and validate real behavior.
    """

    async def test_should_process_inquiry_with_real_claude_api(
        self,
        real_ai_provider,
        sample_test_inquiry,
    ):
        """
        TDD Test: WorkflowEngine should process inquiry using real Claude API.

        This test validates:
        - Real Claude API integration works
        - Self-consistency voting with real temperature variations
        - Consensus formation on actual AI outputs
        - Proposal generation from real data
        - Budget tier returns exactly 3 workflows

        Cost: ~$0.30 per run (5 parallel Claude calls)

        TDD Workflow:
        RED: Write this test (will initially fail with real API)
        GREEN: Fix integration issues until test passes
        REFACTOR: Optimize and clean up
        """
        from contexts.workflow.engine import WorkflowEngine

        # Arrange: Create engine with REAL AI provider
        engine = WorkflowEngine(
            ai_provider=real_ai_provider,
            temperatures=[0.4, 0.6, 0.8, 1.0, 1.2],  # Real temperature variations
            min_consensus_votes=2,
        )

        # Act: Process inquiry with real Claude API
        result, qa_result = await engine.process_inquiry(
            inquiry=sample_test_inquiry,
            tier="Budget",  # Cheaper tier for testing
        )

        # Assert: Validate real API results
        assert result.run_id is not None, "Should generate run_id"
        assert result.client_name == "Test User", "Should extract client name"
        assert result.business_name is not None, "Should extract business name"

        # Consensus validation
        assert result.consensus is not None, "Should have consensus result"
        assert result.consensus.total_responses >= 5, \
            f"Should have 5 responses from temperatures, got {result.consensus.total_responses}"

        # Budget tier should have exactly 3 workflows
        assert len(result.consensus.all_workflows) == 3, \
            f"Budget tier should return exactly 3 workflows, got {len(result.consensus.all_workflows)}"

        # Each workflow should have required fields
        for idx, wf in enumerate(result.consensus.all_workflows):
            assert wf.name, f"Workflow {idx+1} should have name"
            assert wf.objective, f"Workflow '{wf.name}' should have objective"
            assert isinstance(wf.tools, list), f"Workflow '{wf.name}' should have tools list"
            # Tools can be empty for some workflows, but should be a list
            assert wf.description or wf.objective, \
                f"Workflow '{wf.name}' should have description or objective"

        # Proposal validation
        assert result.proposal is not None, "Should generate proposal"
        assert result.proposal.html_body, "Should have HTML body"
        assert result.proposal.subject, "Should have email subject"
        assert "Test User" in result.proposal.html_body, "HTML should include client name"

        # Phases validation
        assert len(result.proposal.phases) > 0, "Should have at least 1 phase"
        for phase in result.proposal.phases:
            assert phase.phase_number > 0, "Phase should have number"
            assert phase.phase_name, "Phase should have name"
            assert len(phase.workflows) > 0, "Phase should have workflows"

        # AI behavior validation (accounting for non-determinism)
        assert result.consensus.confidence_percent >= 0, "Confidence should be non-negative"
        assert result.consensus.confidence_percent <= 100, "Confidence should be <= 100%"

        # Either consensus was reached OR fallback was used
        assert result.consensus.consensus_strength in [
            "Strong", "Moderate", "Weak", "Fallback"
        ], f"Invalid consensus strength: {result.consensus.consensus_strength}"

        # Log results for debugging
        print(f"\n========== Real API Test Results ==========")
        print(f"Run ID: {result.run_id}")
        print(f"Client: {result.client_name}")
        print(f"Business: {result.business_name}")
        print(f"Tier: {result.tier}")
        print(f"\nConsensus:")
        print(f"  Final Answer: {result.consensus.final_answer}")
        print(f"  Votes: {result.consensus.votes_for_winner}/{result.consensus.total_responses}")
        print(f"  Confidence: {result.consensus.confidence_percent}%")
        print(f"  Strength: {result.consensus.consensus_strength}")
        print(f"\nWorkflows ({len(result.consensus.all_workflows)}):")
        for i, wf in enumerate(result.consensus.all_workflows, 1):
            tools_str = ", ".join(wf.tools) if wf.tools else "TBD"
            print(f"  {i}. {wf.name}")
            print(f"     Objective: {wf.objective}")
            print(f"     Tools: {tools_str}")
        print(f"\nPhases ({len(result.proposal.phases)}):")
        for phase in result.proposal.phases:
            print(f"  Phase {phase.phase_number}: {phase.phase_name} ({len(phase.workflows)} workflows)")
        print(f"=========================================\n")


    async def test_should_handle_standard_tier_with_real_api(
        self,
        real_ai_provider,
        sample_test_inquiry,
    ):
        """
        TDD Test: WorkflowEngine should handle Standard tier with real API.

        Standard tier should return 5 workflows (not 3).

        Cost: ~$0.30 per run
        """
        from contexts.workflow.engine import WorkflowEngine

        # Arrange
        engine = WorkflowEngine(
            ai_provider=real_ai_provider,
            min_consensus_votes=2,
        )

        # Act
        result, _ = await engine.process_inquiry(
            inquiry=sample_test_inquiry,
            tier="Standard",
        )

        # Assert: Standard tier returns 5 workflows
        assert len(result.consensus.all_workflows) == 5, \
            f"Standard tier should return 5 workflows, got {len(result.consensus.all_workflows)}"

        assert result.tier == "Standard", "Should record tier"

        print(f"\n========== Standard Tier Test Results ==========")
        print(f"Run ID: {result.run_id}")
        print(f"Tier: {result.tier}")
        print(f"Workflows: {len(result.consensus.all_workflows)}")
        print(f"Consensus: {result.consensus.final_answer}")
        print(f"===============================================\n")


    async def test_should_extract_business_name_from_prompt(
        self,
        real_ai_provider,
    ):
        """
        TDD Test: Engine should extract business name from various prompt formats.

        Tests identity extraction with real API processing.

        Cost: ~$0.30 per run
        """
        from contexts.workflow.engine import WorkflowEngine
        from contexts.workflow.models import EmailInquiry

        # Arrange: Inquiry with clear business name pattern
        inquiry = EmailInquiry(
            message_id="test-identity",
            from_email="john@example.com",
            from_name="John Smith",
            subject="Business Analysis",
            body="Analyze Acme Corporation at https://acme.com and recommend 3 workflows.",
        )

        engine = WorkflowEngine(
            ai_provider=real_ai_provider,
            min_consensus_votes=2,
        )

        # Act
        result, _ = await engine.process_inquiry(inquiry, tier="Budget")

        # Assert: Identity extraction
        assert result.client_name == "John Smith", "Should extract client name from from_name"

        # Business name should be extracted (exact match depends on AI, so be flexible)
        assert result.business_name, "Should extract business name"
        # Either exact match or default
        assert "Acme" in result.business_name or result.business_name == "Your Business", \
            f"Should extract 'Acme' or use default, got '{result.business_name}'"

        print(f"\n========== Identity Extraction Test ==========")
        print(f"Client Name: {result.client_name}")
        print(f"Business Name: {result.business_name}")
        print(f"============================================\n")


@pytest.mark.real_api
@pytest.mark.asyncio
class TestRealConsensusFormation:
    """
    Tests for consensus formation with real AI outputs.
    """

    async def test_should_form_consensus_or_use_fallback(
        self,
        real_ai_provider,
        minimal_email_inquiry,
    ):
        """
        TDD Test: Self-consistency voting should work with real Claude outputs.

        With a focused prompt, we expect either:
        - Strong consensus (3+ votes for same answer), OR
        - Fallback scoring (if responses are diverse)

        Cost: ~$0.25 per run (simpler prompt)
        """
        from contexts.workflow.engine import WorkflowEngine

        # Arrange: Focused prompt likely to produce consensus
        engine = WorkflowEngine(
            ai_provider=real_ai_provider,
            temperatures=[0.4, 0.6, 0.8, 1.0, 1.2],
            min_consensus_votes=3,  # Need 3/5 to agree
        )

        # Act
        result, _ = await engine.process_inquiry(
            minimal_email_inquiry,
            tier="Budget",
        )

        # Assert: Consensus result exists
        assert result.consensus is not None
        assert result.consensus.total_responses == 5

        # Either consensus reached or fallback used
        if result.consensus.had_consensus:
            # Consensus path
            assert result.consensus.votes_for_winner >= 3, \
                f"Consensus should have >= 3 votes, got {result.consensus.votes_for_winner}"
            assert result.consensus.consensus_strength in ["Strong", "Moderate"], \
                f"With consensus, strength should be Strong/Moderate, got {result.consensus.consensus_strength}"
        else:
            # Fallback path
            assert result.consensus.consensus_strength == "Fallback", \
                f"Without consensus, should use Fallback, got {result.consensus.consensus_strength}"

        # Final answer should always be set
        assert result.consensus.final_answer, "Should always have final answer"

        # Workflows should be ranked (first should be the final answer)
        assert len(result.consensus.all_workflows) == 3, "Budget tier should have 3 workflows"

        print(f"\n========== Consensus Formation Test ==========")
        print(f"Had Consensus: {result.consensus.had_consensus}")
        print(f"Votes: {result.consensus.votes_for_winner}/{result.consensus.total_responses}")
        print(f"Strength: {result.consensus.consensus_strength}")
        print(f"Confidence: {result.consensus.confidence_percent}%")
        print(f"Final Answer: {result.consensus.final_answer}")
        print(f"\nTop 3 Workflows:")
        for i, wf in enumerate(result.consensus.all_workflows, 1):
            print(f"  {i}. {wf.name}")
        print(f"============================================\n")
