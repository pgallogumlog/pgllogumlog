"""
Budget tier validation test - 3 prompts with SC=5.
Tests that Budget tier runs Self-Consistency with 5 votes and returns 5 workflows.
"""
import asyncio
import sys
from datetime import datetime
from collections import Counter

from contexts.workflow.engine import WorkflowEngine
from contexts.workflow.models import EmailInquiry
from contexts.testing.test_cases import get_test_cases
from config.dependency_injection import get_container


def print_progress(msg, level=0):
    """Print progress with timestamp and indentation."""
    indent = "  " * level
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {indent}{msg}")


async def test_prompt(prompt_num: int, test_case, engine):
    """Test single prompt on Budget tier."""
    print_progress(f"PROMPT {prompt_num}: {test_case.company} ({test_case.category})", level=1)

    inquiry = EmailInquiry(
        message_id=f"budget-sc3-test-{prompt_num}",
        from_email="test@example.com",
        from_name=test_case.company,
        subject="Workflow Analysis",
        body=test_case.prompt
    )

    start = datetime.now()

    try:
        result, _ = await engine.process_inquiry(inquiry, "Budget")
        elapsed = (datetime.now() - start).total_seconds()

        # Check for duplicates
        names = [wf.name for wf in result.consensus.all_workflows]
        unique = set(names)
        has_dups = len(names) != len(unique)

        # Status
        status = "FAIL" if has_dups else "PASS"
        dup_info = f"{len(names) - len(unique)} dups" if has_dups else "no dups"

        # Check workflow count (Budget tier should return 5 workflows)
        workflow_count_ok = len(names) == 5
        count_status = "OK" if workflow_count_ok else f"WRONG ({len(names)} workflows)"

        print_progress(
            f"{status} - {count_status} - {result.consensus.consensus_strength} "
            f"({result.consensus.confidence_percent}%) - {dup_info} - {elapsed:.1f}s",
            level=2
        )

        if has_dups:
            counts = Counter(names)
            dups = [name for name, count in counts.items() if count > 1]
            print_progress(f"Duplicates: {dups}", level=3)

        if not workflow_count_ok:
            print_progress(f"Expected 5 workflows, got {len(names)}", level=3)

        return {
            "prompt_num": prompt_num,
            "company": test_case.company,
            "category": test_case.category,
            "elapsed": elapsed,
            "has_duplicates": has_dups,
            "duplicate_count": len(names) - len(unique) if has_dups else 0,
            "workflows": names,
            "workflow_count": len(names),
            "workflow_count_ok": workflow_count_ok,
            "consensus": result.consensus.consensus_strength,
            "confidence": result.consensus.confidence_percent,
            "status": "PASS" if (not has_dups and workflow_count_ok) else "FAIL"
        }

    except Exception as e:
        elapsed = (datetime.now() - start).total_seconds()
        print_progress(f"ERROR - {str(e)[:100]} - {elapsed:.1f}s", level=2)
        return {
            "prompt_num": prompt_num,
            "company": test_case.company,
            "error": str(e),
            "elapsed": elapsed,
            "status": "ERROR"
        }


async def main():
    print("=" * 80)
    print("BUDGET TIER - 3 PROMPT VALIDATION TEST (SC=5)")
    print("=" * 80)
    print_progress("Test started")
    print()

    # Get 3 test cases
    test_cases = get_test_cases(count=3)

    print(f"Testing {len(test_cases)} prompts on Budget tier:")
    for i, tc in enumerate(test_cases, 1):
        print(f"  {i}. {tc.company} ({tc.category})")
    print()
    print("=" * 80)
    print()

    # Create engine once and reuse
    container = get_container()
    engine = WorkflowEngine(
        ai_provider=container.ai_provider(),
        temperatures=container.settings.temperatures,
        min_consensus_votes=container.settings.sc_min_consensus_votes,
    )

    # Run all 3 tests
    results = []
    overall_start = datetime.now()

    for i, test_case in enumerate(test_cases, 1):
        result = await test_prompt(i, test_case, engine)
        results.append(result)
        print()  # Blank line between tests

    overall_elapsed = (datetime.now() - overall_start).total_seconds()

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print_progress("Test completed")
    print()

    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "PASS")
    failed = sum(1 for r in results if r.get("status") == "FAIL")
    errors = sum(1 for r in results if r.get("status") == "ERROR")

    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"Errors: {errors} ({errors/total*100:.1f}%)")
    print(f"Total Time: {overall_elapsed/60:.1f} minutes ({overall_elapsed:.0f}s)")
    print(f"Avg Time per Run: {overall_elapsed/total:.1f}s")
    print()

    # Detailed results
    print("DETAILED RESULTS:")
    print("-" * 80)
    for r in results:
        if "error" in r:
            print(f"\nPrompt {r['prompt_num']} ({r['company']}): ERROR - {r['error']}")
        else:
            status = "PASS" if r['status'] == "PASS" else f"FAIL"
            print(f"\nPrompt {r['prompt_num']} ({r['company']}): {status}")
            print(f"  Category: {r['category']}")
            print(f"  Consensus: {r['consensus']} ({r['confidence']}%)")
            print(f"  Workflows: {r['workflow_count']} (expected: 5)")
            print(f"  Duplicates: {r['duplicate_count']}")
            print(f"  Time: {r['elapsed']:.1f}s")
            if r['duplicate_count'] > 0:
                counts = Counter(r['workflows'])
                dups = [f"{name} (x{count})" for name, count in counts.items() if count > 1]
                print(f"  Duplicate Names: {', '.join(dups)}")
            if not r['workflow_count_ok']:
                print(f"  WARNING: Expected 5 workflows, got {r['workflow_count']}")

    # Duplicate analysis
    print()
    print("DUPLICATE ANALYSIS:")
    print("-" * 80)

    total_dups = sum(r.get("duplicate_count", 0) for r in results if "duplicate_count" in r)
    runs_with_dups = sum(1 for r in results if r.get("has_duplicates"))

    print(f"Total duplicate workflows found: {total_dups}")
    print(f"Runs with duplicates: {runs_with_dups}/{total}")

    if runs_with_dups > 0:
        print("\nRuns with duplicates:")
        for r in results:
            if r.get("has_duplicates"):
                print(f"  Prompt {r['prompt_num']} ({r['company']}): {r['duplicate_count']} duplicates")

    # Workflow count validation
    print()
    print("WORKFLOW COUNT VALIDATION:")
    print("-" * 80)

    count_mismatches = sum(1 for r in results if not r.get("workflow_count_ok", False))
    print(f"Expected workflow count: 5 (Budget tier)")
    print(f"Runs with correct count: {total - count_mismatches}/{total}")
    print(f"Runs with wrong count: {count_mismatches}/{total}")

    if count_mismatches > 0:
        print("\nRuns with wrong workflow count:")
        for r in results:
            if not r.get("workflow_count_ok", False):
                print(f"  Prompt {r['prompt_num']} ({r['company']}): {r.get('workflow_count', 0)} workflows")

    # Final verdict
    print()
    print("=" * 80)
    if passed == total and count_mismatches == 0:
        print("VALIDATION SUCCESS: ALL 3 RUNS PASSED!")
        print("No duplicates found in any prompt.")
        print("All runs returned exactly 5 workflows as expected for Budget tier.")
        print("Budget tier SC=5 configuration is VALIDATED.")
    elif errors == 0 and failed == 0:
        print("TEST COMPLETED SUCCESSFULLY")
    else:
        print("VALIDATION RESULTS:")
        print(f"  {passed}/{total} runs passed")
        print(f"  {failed} runs failed")
        print(f"  {errors} runs had errors")

        if runs_with_dups > 0:
            print("\n  DUPLICATE BUG STILL PRESENT in some runs")
        if count_mismatches > 0:
            print(f"\n  WORKFLOW COUNT MISMATCH in {count_mismatches} runs")

    print()
    print(f"Test Duration: {overall_elapsed/60:.1f} minutes ({overall_elapsed:.0f} seconds)")
    print("=" * 80)


if __name__ == "__main__":
    # Set stdout encoding to UTF-8 to handle Unicode
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    asyncio.run(main())
