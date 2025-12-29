"""
Priority 4: Real QA Capture Validation Tests

Tests QA capture system with REAL Claude API calls.
NO MOCKS - Validates QA pipeline with actual API responses.

Cost: ~$0.30 per test
"""

import pytest


@pytest.mark.real_api
@pytest.mark.asyncio
class TestRealQACapture:
    """
    Tests for QA capture system with real API calls.

    Validates that QA validation pipeline works with real Claude responses.
    """

    async def test_should_capture_and_validate_real_api_calls(
        self,
        real_capturing_ai_provider,
        sample_test_inquiry,
    ):
        """
        TDD Test: QA system should capture and validate real Claude API calls.

        This test validates:
        - CapturingAIAdapter intercepts real API calls
        - Deterministic validators run on real responses
        - Call scoring works with real data
        - Validation results are accurate
        - Call store tracks all calls

        Cost: ~$0.30 per run
        """
        from contexts.workflow.engine import WorkflowEngine

        # Arrange: Create engine with capturing adapter
        engine = WorkflowEngine(
            ai_provider=real_capturing_ai_provider,
            min_consensus_votes=2,
        )

        # Act: Process inquiry (all AI calls will be captured)
        result, qa_result = await engine.process_inquiry(
            inquiry=sample_test_inquiry,
            tier="Budget",
        )

        # Assert: Calls were captured
        call_store = real_capturing_ai_provider.call_store
        assert len(call_store.calls) > 0, "Should capture AI calls"

        # Expected calls:
        # 1. Input rewriter (normalize prompt)
        # 2. Research pack generator
        # 3-7. Self-consistency voting (5 parallel calls)
        # 8. Grouper
        # Total: 8 calls
        assert len(call_store.calls) >= 7, \
            f"Should capture at least 7 AI calls, got {len(call_store.calls)}"

        # Assert: Each call has validation results
        for call in call_store.calls:
            assert call.validation_results is not None, \
                f"Call {call.call_id} should have validation results"
            assert call.call_score is not None, \
                f"Call {call.call_id} should have score"

            # Validate call metadata
            assert call.call_id.startswith("test-"), "Call ID should have test prefix"
            assert call.method in ["generate", "generate_json", "generate_parallel"], \
                f"Invalid method: {call.method}"
            assert call.caller_context, "Should track caller context"
            assert call.input_tokens > 0, "Should track input tokens"
            assert call.output_tokens > 0, "Should track output tokens"
            assert call.duration_ms > 0, "Should track duration"

            # Validate scoring
            assert 0 <= call.call_score.overall_score <= 10, \
                f"Score should be 0-10, got {call.call_score.overall_score}"

        # Assert: QA result was generated
        assert qa_result is not None, "Should generate QA result"
        assert qa_result.overall_score > 0, "Should have overall score"
        assert qa_result.total_calls == len(call_store.calls), \
            "QA result should track all calls"

        # Assert: QA metrics
        assert qa_result.total_calls > 0
        assert qa_result.calls_passed >= 0
        assert qa_result.calls_failed >= 0
        assert qa_result.calls_passed + qa_result.calls_failed == qa_result.total_calls

        # Print detailed QA metrics
        print(f"\n========== QA Capture Test Results ==========")
        print(f"Run ID: {result.run_id}")
        print(f"Total Calls Captured: {len(call_store.calls)}")
        print(f"\nOverall QA Metrics:")
        print(f"  Overall Score: {qa_result.overall_score}/10")
        print(f"  Passed: {qa_result.passed}")
        print(f"  Total Calls: {qa_result.total_calls}")
        print(f"  Calls Passed: {qa_result.calls_passed}")
        print(f"  Calls Failed: {qa_result.calls_failed}")

        print(f"\nDetailed Call Breakdown:")
        for idx, call in enumerate(call_store.calls, 1):
            status = "PASS" if call.call_score.passed else "FAIL"
            print(f"\n  Call {idx}: {call.call_id}")
            print(f"    Method: {call.method}")
            print(f"    Context: {call.caller_context}")
            print(f"    Score: {call.call_score.overall_score}/10 ({status})")
            print(f"    Tokens: {call.input_tokens} in / {call.output_tokens} out")
            print(f"    Duration: {call.duration_ms:.0f}ms")
            print(f"    Temperature: {call.temperature}")

            # Show failed validations if any
            if call.validation_results:
                failed = [r for r in call.validation_results if not r.passed]
                if failed:
                    print(f"    Failed Checks:")
                    for f in failed:
                        print(f"      - {f.check_name}: {f.message}")

        print(f"\nCall Store Summary:")
        summary = call_store.summary()
        print(f"  Total Calls: {summary['total_calls']}")
        print(f"  Calls Passed: {summary['calls_passed']}")
        print(f"  Calls Failed: {summary['calls_failed']}")

        # Calculate average score from calls
        scores = [call.call_score.overall_score for call in call_store.calls if call.call_score]
        avg_score = sum(scores) / len(scores) if scores else 0
        print(f"  Average Score: {avg_score:.1f}/10")
        print(f"===========================================\n")


    async def test_should_validate_deterministic_checks_on_real_responses(
        self,
        real_capturing_ai_provider,
        minimal_email_inquiry,
    ):
        """
        TDD Test: Deterministic validators should run on real API responses.

        Validates that basic quality checks work:
        - Response time is reasonable
        - Token counts are tracked
        - Response format is valid
        - No truncation occurred

        Cost: ~$0.25 per run (minimal prompt)
        """
        from contexts.workflow.engine import WorkflowEngine

        # Arrange
        engine = WorkflowEngine(
            ai_provider=real_capturing_ai_provider,
            min_consensus_votes=2,
        )

        # Act
        result, _ = await engine.process_inquiry(
            inquiry=minimal_email_inquiry,
            tier="Budget",
        )

        # Assert: All calls should have deterministic validation (via call_score)
        call_store = real_capturing_ai_provider.call_store

        for call in call_store.calls:
            # Check that call has score with check_scores
            assert call.call_score is not None, \
                f"Call {call.call_id} should have call_score"

            assert call.call_score.check_scores is not None, \
                f"Call {call.call_id} should have check_scores"

            # Deterministic checks should have passed (via deterministic_passed flag)
            assert call.call_score.deterministic_passed is True, \
                f"Call {call.call_id} should pass deterministic checks"

        print(f"\n========== Deterministic Validation Test ==========")
        print(f"Calls Analyzed: {len(call_store.calls)}")
        print(f"\nDeterministic Check Results:")

        for call in call_store.calls:
            print(f"\n  {call.call_id} ({call.method}):")
            print(f"    Deterministic Passed: {call.call_score.deterministic_passed}")
            print(f"    Overall Score: {call.call_score.overall_score}/10")
            if call.call_score.check_scores:
                print(f"    Check Scores: {call.call_score.check_scores}")

        print(f"================================================\n")


    async def test_should_track_context_stack_for_caller_identification(
        self,
        real_capturing_ai_provider,
        sample_test_inquiry,
    ):
        """
        TDD Test: QA capture should track caller context for each AI call.

        Validates that we can identify which component made each call:
        - WorkflowEngine._rewrite_input
        - WorkflowEngine._run_research
        - WorkflowEngine._run_self_consistency
        - WorkflowEngine._run_grouper

        Cost: ~$0.30 per run
        """
        from contexts.workflow.engine import WorkflowEngine

        # Arrange
        engine = WorkflowEngine(
            ai_provider=real_capturing_ai_provider,
            min_consensus_votes=2,
        )

        # Act
        result, _ = await engine.process_inquiry(
            inquiry=sample_test_inquiry,
            tier="Budget",
        )

        # Assert: Caller contexts are tracked
        call_store = real_capturing_ai_provider.call_store

        # Expected contexts
        expected_contexts = {
            "WorkflowEngine._rewrite_input",
            "WorkflowEngine._run_research",
            "WorkflowEngine._run_self_consistency",
            "WorkflowEngine._run_grouper",
        }

        found_contexts = {call.caller_context for call in call_store.calls}

        # All expected contexts should be present
        for expected in expected_contexts:
            assert expected in found_contexts, \
                f"Should find context '{expected}', found: {found_contexts}"

        print(f"\n========== Context Tracking Test ==========")
        print(f"Expected Contexts: {len(expected_contexts)}")
        print(f"Found Contexts: {len(found_contexts)}")
        print(f"\nCall Context Breakdown:")

        context_counts = {}
        for call in call_store.calls:
            ctx = call.caller_context
            context_counts[ctx] = context_counts.get(ctx, 0) + 1

        for ctx, count in sorted(context_counts.items()):
            print(f"  {ctx}: {count} call(s)")

        print(f"========================================\n")


@pytest.mark.real_api
@pytest.mark.asyncio
class TestRealQAScoring:
    """
    Tests for QA scoring with real API data.
    """

    async def test_should_assign_quality_scores_to_real_calls(
        self,
        real_capturing_ai_provider,
        sample_test_inquiry,
    ):
        """
        TDD Test: QA scorer should assign meaningful scores to real API calls.

        Validates:
        - Each call gets a score (0-10)
        - Overall workflow score is calculated
        - Pass/fail determination works

        Cost: ~$0.30 per run
        """
        from contexts.workflow.engine import WorkflowEngine

        # Arrange
        engine = WorkflowEngine(
            ai_provider=real_capturing_ai_provider,
            min_consensus_votes=2,
        )

        # Act
        result, qa_result = await engine.process_inquiry(
            inquiry=sample_test_inquiry,
            tier="Budget",
        )

        # Assert: QA scoring works
        assert qa_result is not None
        assert qa_result.overall_score > 0, "Should have positive overall score"
        assert 0 <= qa_result.overall_score <= 10, "Score should be 0-10"

        # Individual call scores
        call_store = real_capturing_ai_provider.call_store
        for call in call_store.calls:
            assert call.call_score is not None, f"Call {call.call_id} should have score"
            assert 0 <= call.call_score.overall_score <= 10, \
                f"Call {call.call_id} score should be 0-10"

            # Score breakdown should exist (via passed flags)
            assert call.call_score.deterministic_passed is not None, \
                "Should have deterministic validation status"
            # Probabilistic can be None if not run
            assert call.call_score.probabilistic_passed is None or \
                   isinstance(call.call_score.probabilistic_passed, bool), \
                "Probabilistic status should be None or boolean"

        # Most real API calls should pass (Claude is reliable)
        pass_rate = qa_result.calls_passed / qa_result.total_calls * 100
        assert pass_rate >= 50, \
            f"At least 50% of real API calls should pass QA, got {pass_rate:.1f}%"

        print(f"\n========== QA Scoring Test Results ==========")
        print(f"Overall Score: {qa_result.overall_score}/10")
        print(f"Passed: {qa_result.passed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print(f"\nScore Distribution:")

        scores = [call.call_score.overall_score for call in call_store.calls]
        print(f"  Min: {min(scores):.1f}")
        print(f"  Max: {max(scores):.1f}")
        print(f"  Avg: {sum(scores)/len(scores):.1f}")

        print(f"\nIndividual Call Scores:")
        for call in call_store.calls:
            status = "PASS" if call.call_score.passed else "FAIL"
            det_status = "PASS" if call.call_score.deterministic_passed else "FAIL"
            prob_status = "N/A" if call.call_score.probabilistic_passed is None else \
                          ("PASS" if call.call_score.probabilistic_passed else "FAIL")

            print(f"  {call.call_id}: {call.call_score.overall_score:.1f}/10 ({status})")
            print(f"    Deterministic: {det_status}")
            print(f"    Probabilistic: {prob_status}")

        print(f"==========================================\n")
