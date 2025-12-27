"""
Run test with QA capture enabled.

Usage:
    python run_test.py                    # All 3 tiers, 1 test case
    python run_test.py --qa               # With QA capture enabled
    python run_test.py --qa --mock        # With QA capture using mock AI
    python run_test.py --tier standard    # Single tier only
    python run_test.py --count 3          # Run 3 test cases
    python run_test.py --send-emails      # Send proposal emails after processing
    python run_test.py --save-html        # Save HTML proposals to test_results/ folder
    python run_test.py --qa --save-html   # With QA capture AND save HTML files
"""

import asyncio
import sys

from config import get_container
from contexts.testing import TestOrchestrator, TestConfig
from contexts.testing.models import Environment, Tier


def parse_args():
    """Parse command line arguments."""
    args = {
        "enable_qa": "--qa" in sys.argv,
        "use_mock": "--mock" in sys.argv,
        "send_emails": "--send-emails" in sys.argv,
        "save_html": "--save-html" in sys.argv,
        "tier": Tier.ALL,
        "count": 1,
    }

    # Parse --tier argument
    if "--tier" in sys.argv:
        idx = sys.argv.index("--tier")
        if idx + 1 < len(sys.argv):
            tier_name = sys.argv[idx + 1].upper()
            if tier_name == "BUDGET":
                args["tier"] = Tier.BUDGET
            elif tier_name == "STANDARD":
                args["tier"] = Tier.STANDARD
            elif tier_name == "PREMIUM":
                args["tier"] = Tier.PREMIUM
            elif tier_name == "ALL":
                args["tier"] = Tier.ALL

    # Parse --count argument
    if "--count" in sys.argv:
        idx = sys.argv.index("--count")
        if idx + 1 < len(sys.argv):
            try:
                args["count"] = int(sys.argv[idx + 1])
            except ValueError:
                pass

    return args


async def run_one_test(enable_qa: bool = False, use_mock: bool = False,
                       tier: Tier = Tier.ALL, count: int = 1, send_emails: bool = False,
                       save_html: bool = False):
    container = get_container()
    settings = container.settings

    print("=" * 60)
    print("WORKFLOW TEST" + (" WITH QA CAPTURE" if enable_qa else ""))
    print("=" * 60)
    print(f"Tier: {tier.value}")
    print(f"Test Cases: {count}")
    print(f"QA Capture: {'ENABLED' if enable_qa else 'DISABLED'}")
    print(f"AI Provider: {'MOCK' if use_mock else 'REAL (Claude API)'}")
    print(f"Send Emails: {'ENABLED' if send_emails else 'DISABLED'}")
    print(f"Save HTML: {'ENABLED' if save_html else 'DISABLED'}")
    print("=" * 60)

    # Choose AI provider based on flags
    if use_mock:
        from tests.conftest import MockAIProvider
        base_provider = MockAIProvider()
        print("\nUsing MockAIProvider (no API calls)")

        if enable_qa:
            # Wrap mock with capturing adapter for QA
            from contexts.qa.scoring import ValidationPipeline
            from infrastructure.ai.capturing_adapter import CapturingAIAdapter

            pipeline = ValidationPipeline(
                ai_provider=None,  # No probabilistic checks with mock
                run_probabilistic=False,
            )
            ai_provider = CapturingAIAdapter(
                wrapped=base_provider,
                run_id="mock-qa-test",
                validation_pipeline=pipeline,
                enable_capture=True,
                min_pass_score=7,
            )
            print("Wrapped with CapturingAIAdapter for QA validation")
        else:
            ai_provider = base_provider
    elif enable_qa:
        # Use capturing adapter for QA with real API
        ai_provider = container.capturing_ai_provider(
            run_id="test-run",
            run_probabilistic=False,  # Skip probabilistic for speed
            probabilistic_sample_rate=0.0,
        )
        print("\nUsing CapturingAIAdapter with validation pipeline")
    else:
        ai_provider = container.ai_provider()
        print("\nUsing standard ClaudeAdapter")

    # Initialize orchestrator
    html_output_dir = "test_results" if save_html else None
    orchestrator = TestOrchestrator(
        ai_provider=ai_provider,
        sheets_client=container.sheets_client() if not use_mock else None,
        qa_spreadsheet_id=settings.google_sheets_qa_log_id if not use_mock else None,
        email_client=container.email_client() if send_emails and not use_mock else None,
        send_emails=send_emails,
        html_output_dir=html_output_dir,
    )

    config = TestConfig(
        environment=Environment.PRODUCTION,
        tier=tier,  # Runs specified tier(s)
        count=count,  # Number of test cases
        parallel=True,  # Parallel execution
    )

    tiers_desc = "all tiers" if tier == Tier.ALL else f"{tier.value} tier"
    print(f"\nRunning {count} test case(s) across {tiers_desc}...")
    print("-" * 60)

    result = await orchestrator.run_tests(config)

    # Print results
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Total Tests: {result.total_tests}")
    print(f"Passed: {result.passed}")
    print(f"Failed: {result.failed}")
    print(f"Pass Rate: {result.pass_rate:.1f}%")
    print(f"Duration: {result.duration_seconds:.1f}s")

    # Print individual test details
    for test_result in result.results:
        print(f"\n--- {test_result.test_case.company} ({test_result.tier}) ---")
        print(f"  Success: {test_result.success}")
        print(f"  Run ID: {test_result.run_id}")
        print(f"  Consensus: {test_result.consensus_strength} ({test_result.confidence_percent}%)")
        print(f"  Workflows: {test_result.workflow_count}")
        print(f"  Phases: {test_result.phase_count}")
        if test_result.qa_score is not None:
            print(f"  QA Score: {test_result.qa_score}/10 ({'PASS' if test_result.qa_passed else 'FAIL'})")
        if test_result.error_message:
            print(f"  Error: {test_result.error_message}")

    # If using capturing adapter, show call details
    if enable_qa and hasattr(ai_provider, 'call_store'):
        print("\n" + "=" * 60)
        print("CAPTURED AI CALLS")
        print("=" * 60)

        call_store = ai_provider.call_store
        for call in call_store.calls:
            status = "PASS" if (call.call_score and call.call_score.passed) else "FAIL"
            score = call.call_score.overall_score if call.call_score else "N/A"
            print(f"\n[{call.call_id}] {call.method} - Score: {score}/10 ({status})")
            print(f"  Context: {call.caller_context}")
            print(f"  Tokens: {call.input_tokens} in / {call.output_tokens} out")

            if call.validation_results:
                failed = [r for r in call.validation_results if not r.passed]
                if failed:
                    print(f"  Failed Checks:")
                    for f in failed:
                        print(f"    - {f.check_name}: {f.message}")

        summary = call_store.summary()
        print(f"\nTotal Calls: {summary['total_calls']}")
        print(f"Passed: {summary['calls_passed']} | Failed: {summary['calls_failed']}")

    # Log to sheets if not mock
    if not use_mock:
        await orchestrator.log_results_to_sheets(result)
        print("\nResults logged to Google Sheets")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_one_test(
        enable_qa=args["enable_qa"],
        use_mock=args["use_mock"],
        tier=args["tier"],
        count=args["count"],
        send_emails=args["send_emails"],
        save_html=args["save_html"],
    ))

