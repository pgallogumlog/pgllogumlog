"""
Self-Consistency Call Count Validation Test
Tests that Budget tier runs 3 SC calls while Standard and Premium run 5 SC calls.
"""
import asyncio
import sys
import re
from datetime import datetime
from io import StringIO

from contexts.workflow.engine import WorkflowEngine
from contexts.workflow.models import EmailInquiry
from contexts.testing.test_cases import get_test_cases
from config.dependency_injection import get_container


class LogCapture:
    """Capture log output to count SC calls."""
    def __init__(self):
        self.logs = []

    def write(self, msg):
        self.logs.append(msg)
        sys.__stdout__.write(msg)

    def flush(self):
        pass

    def get_sc_call_count(self):
        """Count parallel SC calls from logs."""
        for log in self.logs:
            if "claude_parallel_generation" in log and "num_requests=" in log:
                match = re.search(r'num_requests=(\d+)', log)
                if match:
                    return int(match.group(1))
        return 0

    def get_temperatures_used(self):
        """Extract temperatures from logs."""
        for log in self.logs:
            if "claude_parallel_generation" in log and "temperatures=" in log:
                match = re.search(r'temperatures=(\[[\d\., ]+\])', log)
                if match:
                    return match.group(1)
        return None


def print_progress(msg, level=0):
    """Print progress with timestamp and indentation."""
    indent = "  " * level
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {indent}{msg}")


async def test_tier_sc_calls(tier: str, test_case, engine):
    """Test a single tier and count SC calls."""
    print_progress(f"TIER: {tier} - {test_case.company}", level=1)

    # Capture logs
    old_stderr = sys.stderr
    log_capture = LogCapture()
    sys.stderr = log_capture

    inquiry = EmailInquiry(
        message_id=f"sc-count-test-{tier.lower()}",
        from_email="test@example.com",
        from_name=test_case.company,
        subject="Workflow Analysis",
        body=test_case.prompt
    )

    start = datetime.now()

    try:
        result, _ = await engine.process_inquiry(inquiry, tier)
        elapsed = (datetime.now() - start).total_seconds()

        # Restore stderr
        sys.stderr = old_stderr

        # Extract SC call count from logs
        sc_call_count = log_capture.get_sc_call_count()
        temperatures = log_capture.get_temperatures_used()
        workflow_count = len(result.consensus.all_workflows)
        total_workflows = len(result.consensus.raw_workflows)

        # Expected values
        expected_sc_calls = 3 if tier == "Budget" else 5
        expected_workflows = 3 if tier == "Budget" else 5
        expected_total = 75 if tier == "Budget" else 125  # 25 per SC call

        # Validation
        sc_ok = sc_call_count == expected_sc_calls
        wf_ok = workflow_count == expected_workflows
        total_ok = total_workflows == expected_total

        status = "PASS" if (sc_ok and wf_ok and total_ok) else "FAIL"

        print_progress(f"{status} - {elapsed:.1f}s", level=2)
        print_progress(f"SC Calls: {sc_call_count} (expected: {expected_sc_calls}) {'✓' if sc_ok else '✗'}", level=3)
        print_progress(f"Temperatures: {temperatures}", level=3)
        print_progress(f"Total Workflows Generated: {total_workflows} (expected: {expected_total}) {'✓' if total_ok else '✗'}", level=3)
        print_progress(f"Final Workflows Selected: {workflow_count} (expected: {expected_workflows}) {'✓' if wf_ok else '✗'}", level=3)
        print_progress(f"Consensus: {result.consensus.consensus_strength} ({result.consensus.confidence_percent}%)", level=3)

        return {
            "tier": tier,
            "company": test_case.company,
            "sc_call_count": sc_call_count,
            "expected_sc_calls": expected_sc_calls,
            "sc_calls_ok": sc_ok,
            "temperatures": temperatures,
            "total_workflows": total_workflows,
            "expected_total": expected_total,
            "total_ok": total_ok,
            "workflow_count": workflow_count,
            "expected_workflows": expected_workflows,
            "workflows_ok": wf_ok,
            "consensus": result.consensus.consensus_strength,
            "confidence": result.consensus.confidence_percent,
            "elapsed": elapsed,
            "status": status
        }

    except Exception as e:
        sys.stderr = old_stderr
        elapsed = (datetime.now() - start).total_seconds()
        print_progress(f"ERROR - {str(e)[:100]}", level=2)
        return {
            "tier": tier,
            "company": test_case.company,
            "error": str(e),
            "elapsed": elapsed,
            "status": "ERROR"
        }


async def main():
    print("=" * 80)
    print("SELF-CONSISTENCY CALL COUNT VALIDATION TEST")
    print("=" * 80)
    print_progress("Test started")
    print()

    print("Testing SC call counts across all tiers:")
    print("  Budget tier: EXPECTED 3 SC calls → 75 workflows → 3 final")
    print("  Standard tier: EXPECTED 5 SC calls → 125 workflows → 5 final")
    print("  Premium tier: EXPECTED 5 SC calls → 125 workflows → 5 final")
    print()
    print("=" * 80)
    print()

    # Get 1 test case (same prompt for all tiers)
    test_case = get_test_cases(count=1)[0]

    # Create engine
    container = get_container()
    engine = WorkflowEngine(
        ai_provider=container.ai_provider(),
        temperatures=container.settings.temperatures,
        min_consensus_votes=container.settings.sc_min_consensus_votes,
    )

    # Test all 3 tiers
    results = []
    overall_start = datetime.now()

    for tier in ["Budget", "Standard", "Premium"]:
        result = await test_tier_sc_calls(tier, test_case, engine)
        results.append(result)
        print()

    overall_elapsed = (datetime.now() - overall_start).total_seconds()

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print_progress("Test completed")
    print()

    passed = sum(1 for r in results if r.get("status") == "PASS")
    failed = sum(1 for r in results if r.get("status") == "FAIL")
    errors = sum(1 for r in results if r.get("status") == "ERROR")

    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    print(f"Total Time: {overall_elapsed/60:.1f} minutes ({overall_elapsed:.0f}s)")
    print()

    # Detailed results per tier
    print("DETAILED RESULTS BY TIER:")
    print("-" * 80)

    for r in results:
        if "error" in r:
            print(f"\n{r['tier']} Tier: ERROR")
            print(f"  Error: {r['error']}")
        else:
            print(f"\n{r['tier']} Tier: {r['status']}")
            print(f"  SC Calls: {r['sc_call_count']} (expected: {r['expected_sc_calls']}) {'✓' if r['sc_calls_ok'] else '✗ MISMATCH'}")
            print(f"  Temperatures: {r['temperatures']}")
            print(f"  Total Workflows: {r['total_workflows']} (expected: {r['expected_total']}) {'✓' if r['total_ok'] else '✗ MISMATCH'}")
            print(f"  Final Workflows: {r['workflow_count']} (expected: {r['expected_workflows']}) {'✓' if r['workflows_ok'] else '✗ MISMATCH'}")
            print(f"  Consensus: {r['consensus']} ({r['confidence']}%)")
            print(f"  Time: {r['elapsed']:.1f}s")

    # SC Call Count Analysis
    print()
    print("SC CALL COUNT ANALYSIS:")
    print("-" * 80)

    budget_result = next((r for r in results if r['tier'] == 'Budget'), None)
    standard_result = next((r for r in results if r['tier'] == 'Standard'), None)
    premium_result = next((r for r in results if r['tier'] == 'Premium'), None)

    if budget_result and 'sc_call_count' in budget_result:
        if budget_result['sc_calls_ok']:
            print(f"✓ Budget tier: Correctly running {budget_result['sc_call_count']} SC calls")
        else:
            print(f"✗ Budget tier: Running {budget_result['sc_call_count']} SC calls, expected {budget_result['expected_sc_calls']}")
            print(f"  ISSUE: Budget tier should run only 3 SC calls to reduce API costs")

    if standard_result and 'sc_call_count' in standard_result:
        if standard_result['sc_calls_ok']:
            print(f"✓ Standard tier: Correctly running {standard_result['sc_call_count']} SC calls")
        else:
            print(f"✗ Standard tier: Running {standard_result['sc_call_count']} SC calls, expected {standard_result['expected_sc_calls']}")

    if premium_result and 'sc_call_count' in premium_result:
        if premium_result['sc_calls_ok']:
            print(f"✓ Premium tier: Correctly running {premium_result['sc_call_count']} SC calls")
        else:
            print(f"✗ Premium tier: Running {premium_result['sc_call_count']} SC calls, expected {premium_result['expected_sc_calls']}")

    # Final verdict
    print()
    print("=" * 80)
    if passed == len(results):
        print("✓ VALIDATION SUCCESS: All tiers using correct SC call counts!")
        print()
        print("Budget tier: 3 SC calls → 75 workflows → 3 final")
        print("Standard tier: 5 SC calls → 125 workflows → 5 final")
        print("Premium tier: 5 SC calls → 125 workflows → 5 final")
    else:
        print("✗ VALIDATION FAILED: SC call count mismatch detected")
        print()
        if budget_result and not budget_result.get('sc_calls_ok', True):
            print(f"ISSUE: Budget tier is running {budget_result.get('sc_call_count', 'unknown')} SC calls instead of 3")
            print("IMPACT: Higher API costs for Budget tier customers")
            print("FIX NEEDED: Implement tier-specific temperature configuration in WorkflowEngine")

        if not all(r.get('workflows_ok', False) for r in results if 'workflows_ok' in r):
            print()
            print("ISSUE: Final workflow counts don't match tier expectations")

    print()
    print(f"Test Duration: {overall_elapsed/60:.1f} minutes ({overall_elapsed:.0f} seconds)")
    print("=" * 80)


if __name__ == "__main__":
    # Set stdout encoding to UTF-8 to handle Unicode
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    asyncio.run(main())
