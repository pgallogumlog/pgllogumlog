"""
Budget tier validation test - 20 different prompts.
Tests duplicate fix across maximum business scenario diversity.
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
    """Test single prompt."""
    print_progress(f"PROMPT {prompt_num}: {test_case.company} ({test_case.category})", level=1)

    inquiry = EmailInquiry(
        message_id=f"budget-test-{prompt_num}",
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

        print_progress(
            f"{status} - {result.consensus.consensus_strength} ({result.consensus.confidence_percent}%) - "
            f"{len(names)} workflows - {dup_info} - {elapsed:.1f}s",
            level=2
        )

        if has_dups:
            counts = Counter(names)
            dups = [name for name, count in counts.items() if count > 1]
            print_progress(f"Duplicates: {dups}", level=3)

        return {
            "prompt_num": prompt_num,
            "company": test_case.company,
            "category": test_case.category,
            "elapsed": elapsed,
            "has_duplicates": has_dups,
            "duplicate_count": len(names) - len(unique) if has_dups else 0,
            "workflows": names,
            "consensus": result.consensus.consensus_strength,
            "confidence": result.consensus.confidence_percent,
            "status": "PASS" if not has_dups else "FAIL"
        }

    except Exception as e:
        elapsed = (datetime.now() - start).total_seconds()
        print_progress(f"ERROR - {str(e)[:50]} - {elapsed:.1f}s", level=2)
        return {
            "prompt_num": prompt_num,
            "company": test_case.company,
            "error": str(e),
            "elapsed": elapsed,
            "status": "ERROR"
        }


async def main():
    print("=" * 80)
    print("BUDGET TIER - 20 PROMPT VALIDATION TEST")
    print("=" * 80)
    print_progress("Test started")
    print()

    # Get 20 test cases
    test_cases = get_test_cases(count=20)

    print(f"Testing {len(test_cases)} prompts:")
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

    # Run all 20 tests
    results = []
    overall_start = datetime.now()

    for i, test_case in enumerate(test_cases, 1):
        result = await test_prompt(i, test_case, engine)
        results.append(result)

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
            status = "PASS" if not r['has_duplicates'] else f"FAIL ({r['duplicate_count']} duplicates)"
            print(f"\nPrompt {r['prompt_num']} ({r['company']}): {status}")
            print(f"  Category: {r['category']}")
            print(f"  Consensus: {r['consensus']} ({r['confidence']}%)")
            print(f"  Workflows: {len(r['workflows'])}")
            print(f"  Time: {r['elapsed']:.1f}s")
            if r['has_duplicates']:
                counts = Counter(r['workflows'])
                dups = [f"{name} (x{count})" for name, count in counts.items() if count > 1]
                print(f"  Duplicates: {', '.join(dups)}")

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

    # Final verdict
    print()
    print("=" * 80)
    if passed == total:
        print("VALIDATION SUCCESS: ALL 20 RUNS PASSED!")
        print("No duplicates found in any prompt.")
        print("Duplicate bug fix is VALIDATED across 20 diverse scenarios.")
    elif errors == 0 and failed == 0:
        print("TEST COMPLETED SUCCESSFULLY")
    else:
        print("VALIDATION RESULTS:")
        print(f"  {passed}/{total} runs passed")
        print(f"  {failed} runs failed (duplicates)")
        print(f"  {errors} runs had errors")

        if runs_with_dups > 0:
            print("\nDUPLICATE BUG STILL PRESENT in some runs")
        else:
            print("\nNo duplicates, but some runs had other issues")

    print()
    print(f"Test Duration: {overall_elapsed/60:.1f} minutes ({overall_elapsed:.0f} seconds)")
    print("=" * 80)


if __name__ == "__main__":
    # Set stdout encoding to UTF-8 to handle Unicode
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    asyncio.run(main())
