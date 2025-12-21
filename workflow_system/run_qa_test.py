"""
Test script to demonstrate QA capture functionality.

This runs a workflow with the CapturingAIAdapter enabled to show
how AI calls are captured and validated.
"""

import asyncio
import sys

# Add workflow_system to path
sys.path.insert(0, ".")

from tests.conftest import MockAIProvider
from contexts.qa.scoring import ValidationPipeline
from contexts.workflow import WorkflowEngine
from contexts.workflow.models import EmailInquiry
from infrastructure.ai.capturing_adapter import CapturingAIAdapter


async def main():
    print("=" * 60)
    print("QA CAPTURE TEST")
    print("=" * 60)

    # Create mock AI provider
    mock_ai = MockAIProvider()

    # Set up specific responses for QA auditor
    mock_ai.set_json_responses([
        # Research response
        {
            "businessSummary": "Starbucks is a global coffeehouse chain",
            "customerSegments": ["Coffee lovers", "Mobile app users"],
            "operationalPainPoints": ["High volume orders", "Inventory management"],
            "growthOpportunities": ["AI-powered ordering", "Predictive inventory"],
        },
        # Grouper response
        {
            "phases": [
                {
                    "phaseNumber": 1,
                    "phaseName": "Quick Wins",
                    "workflows": [
                        {
                            "name": "Customer Support Bot",
                            "objective": "Automate customer inquiries",
                            "tools": ["n8n", "OpenAI"],
                            "description": "AI chatbot for FAQs",
                        }
                    ],
                },
                {
                    "phaseNumber": 2,
                    "phaseName": "Growth Phase",
                    "workflows": [
                        {
                            "name": "Inventory Predictor",
                            "objective": "Predict inventory needs",
                            "tools": ["Python", "ML"],
                            "description": "ML-based forecasting",
                        }
                    ],
                },
            ],
            "recommendation": "Start with Customer Support Bot for quick ROI",
        },
        # QA Auditor response
        {
            "score": 8,
            "pass": True,
            "severity": "low",
            "failureType": "none",
            "failingNodeName": "None",
            "rootCause": "Minor formatting issue in phase descriptions",
            "suggestedPromptFix": "Add explicit formatting instructions",
            "critique": "Workflow is well-structured with good recommendations",
        },
    ])

    # Create validation pipeline (deterministic only for speed)
    pipeline = ValidationPipeline(
        ai_provider=None,  # No probabilistic checks
        run_probabilistic=False,
    )

    # Create capturing adapter
    run_id = "qa-test-001"
    capturing_ai = CapturingAIAdapter(
        wrapped=mock_ai,
        run_id=run_id,
        validation_pipeline=pipeline,
        enable_capture=True,
        min_pass_score=7,
    )

    # Create workflow engine with capturing adapter
    engine = WorkflowEngine(
        ai_provider=capturing_ai,
        temperatures=[0.5, 0.7],  # Fewer temps for faster test
        min_consensus_votes=1,
    )

    print(f"\nRun ID: {run_id}")
    print(f"QA Capture Enabled: {engine.is_capturing}")
    print("-" * 60)

    # Create test inquiry
    inquiry = EmailInquiry(
        message_id="test-qa-001",
        from_email="test@example.com",
        from_name="Test User",
        subject="Starbucks Analysis",
        body="Analyze Starbucks at https://www.starbucks.com and recommend the top 5 AI workflows.",
    )

    print("\nRunning workflow...")

    # Run the workflow
    result, qa_result = await engine.process_inquiry(inquiry, tier="Standard")

    print("\n" + "=" * 60)
    print("WORKFLOW RESULT")
    print("=" * 60)
    print(f"Run ID: {result.run_id}")
    print(f"Client: {result.client_name}")
    print(f"Workflows Found: {len(result.consensus.all_workflows)}")
    print(f"Phases: {len(result.proposal.phases)}")
    print(f"Consensus: {result.consensus.consensus_strength} ({result.consensus.confidence_percent}%)")

    print("\n" + "=" * 60)
    print("QA CAPTURE RESULTS")
    print("=" * 60)

    if qa_result:
        print(f"Overall Score: {qa_result.overall_score}/10")
        print(f"Passed: {qa_result.passed}")
        print(f"Total AI Calls: {qa_result.total_calls}")
        print(f"Calls Passed: {qa_result.calls_passed}")
        print(f"Calls Failed: {qa_result.calls_failed}")
        print(f"Worst Severity: {qa_result.worst_severity.value}")
        print(f"Worst Call ID: {qa_result.worst_call_id or 'None'}")

        if qa_result.semantic_result:
            print(f"\nSemantic Analysis:")
            print(f"  Score: {qa_result.semantic_result.score}/10")
            print(f"  Severity: {qa_result.semantic_result.severity.value}")
            print(f"  Root Cause: {qa_result.semantic_result.root_cause}")
    else:
        print("No QA result (capture not enabled)")

    # Show captured calls
    print("\n" + "=" * 60)
    print("CAPTURED AI CALLS")
    print("=" * 60)

    call_store = capturing_ai.call_store
    for call in call_store.calls:
        print(f"\n[{call.call_id}] {call.method}")
        print(f"  Context: {call.caller_context}")
        print(f"  Tokens: {call.input_tokens} in / {call.output_tokens} out")
        print(f"  Stop Reason: {call.stop_reason}")
        print(f"  Duration: {call.duration_ms:.1f}ms")

        if call.call_score:
            print(f"  Score: {call.call_score.overall_score}/10 ({'PASS' if call.call_score.passed else 'FAIL'})")
            print(f"  Checks: {call.call_score.check_scores}")

        if call.validation_results:
            failed = [r for r in call.validation_results if not r.passed]
            if failed:
                print(f"  Failed Checks:")
                for f in failed:
                    print(f"    - {f.check_name}: {f.message}")
                    if f.recommended_fix:
                        print(f"      Fix: {f.recommended_fix}")

    # Summary stats
    print("\n" + "=" * 60)
    print("SUMMARY STATS")
    print("=" * 60)
    summary = call_store.summary()
    print(f"Total Calls: {summary['total_calls']}")
    print(f"Calls Passed: {summary['calls_passed']}")
    print(f"Calls Failed: {summary['calls_failed']}")
    print(f"Total Input Tokens: {summary['total_input_tokens']}")
    print(f"Total Output Tokens: {summary['total_output_tokens']}")
    print(f"Total Duration: {summary['total_duration_ms']:.1f}ms")
    print(f"Methods Used: {summary['methods']}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
