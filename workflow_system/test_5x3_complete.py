"""
Complete 5×3 end-to-end validation test.
5 prompts × 3 tiers = 15 total workflow runs.

This is the ultimate validation test for the duplicate fix.
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
    """Print progress with indentation."""
    indent = "  " * level
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {indent}{msg}")


async def test_single_run(prompt_num: int, test_case, tier: str, engine):
    """Test single prompt+tier combination."""
    run_label = f"P{prompt_num}-{tier}"

    print_progress(f"Starting {run_label}: {test_case.company} ({tier})", level=1)

    inquiry = EmailInquiry(
        message_id=f"test-{run_label.lower()}",
        from_email="test@example.com",
        from_name=test_case.company,
        subject="Workflow Analysis",
        body=test_case.prompt
    )

    start = datetime.now()

    try:
        result, _ = await engine.process_inquiry(inquiry, tier)
        elapsed = (datetime.now() - start).total_seconds()

        # Check for duplicates
        names = [wf.name for wf in result.consensus.all_workflows]
        unique = set(names)
        has_dups = len(names) != len(unique)

        # Status
        status = "FAIL" if has_dups else "PASS"
        dup_info = f"{len(names) - len(unique)} dups" if has_dups else "no dups"

        print_progress(
            f"{run_label}: {status} - {result.consensus.consensus_strength} "
            f"({result.consensus.confidence_percent}%) - {dup_info} - {elapsed:.1f}s",
            level=2
        )

        if has_dups:
            counts = Counter(names)
            dups = [name for name, count in counts.items() if count > 1]
            print_progress(f"Duplicates: {dups}", level=3)

        return {
            "prompt_num": prompt_num,
            "tier": tier,
            "company": test_case.company,
            "run_label": run_label,
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
        print_progress(f"{run_label}: ERROR - {str(e)[:50]} - {elapsed:.1f}s", level=2)
        return {
            "prompt_num": prompt_num,
            "tier": tier,
            "company": test_case.company,
            "run_label": run_label,
            "error": str(e),
            "elapsed": elapsed,
            "status": "ERROR"
        }


async def test_prompt_all_tiers(prompt_num: int, test_case, engine):
    """Test single prompt across all 3 tiers."""
    print_progress(f"PROMPT {prompt_num}: {test_case.company} ({test_case.category})")

    results = []
    for tier in ["Budget", "Standard", "Premium"]:
        result = await test_single_run(prompt_num, test_case, tier, engine)
        results.append(result)

    return results


async def main():
    print("=" * 80)
    print("COMPLETE 5x3 END-TO-END VALIDATION TEST")
    print("=" * 80)
    print_progress("Test started")
    print()

    # Get 5 test cases
    test_cases = get_test_cases(count=5)

    print("Test Matrix: 5 prompts × 3 tiers = 15 total runs")
    print()
    print("Prompts:")
    for i, tc in enumerate(test_cases, 1):
        print(f"  {i}. {tc.company} ({tc.category})")
    print()
    print("Tiers: Budget, Standard, Premium")
    print("=" * 80)
    print()

    # Create engine once and reuse
    container = get_container()
    engine = WorkflowEngine(
        ai_provider=container.ai_provider(),
        temperatures=container.settings.temperatures,
        min_consensus_votes=container.settings.sc_min_consensus_votes,
    )

    # Run all tests
    all_results = []
    overall_start = datetime.now()

    for i, test_case in enumerate(test_cases, 1):
        prompt_results = await test_prompt_all_tiers(i, test_case, engine)
        all_results.extend(prompt_results)
        print()

    overall_elapsed = (datetime.now() - overall_start).total_seconds()

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print_progress("Test completed")
    print()

    total = len(all_results)
    passed = sum(1 for r in all_results if r.get("status") == "PASS")
    failed = sum(1 for r in all_results if r.get("status") == "FAIL")
    errors = sum(1 for r in all_results if r.get("status") == "ERROR")

    print(f"Total Runs: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"Errors: {errors} ({errors/total*100:.1f}%)")
    print(f"Total Time: {overall_elapsed/60:.1f} minutes")
    print(f"Avg Time per Run: {overall_elapsed/total:.1f}s")
    print()

    # Results by tier
    print("RESULTS BY TIER:")
    print("-" * 80)

    for tier in ["Budget", "Standard", "Premium"]:
        tier_results = [r for r in all_results if r.get("tier") == tier]
        tier_passed = sum(1 for r in tier_results if r.get("status") == "PASS")
        tier_failed = sum(1 for r in tier_results if r.get("status") == "FAIL")
        tier_errors = sum(1 for r in tier_results if r.get("status") == "ERROR")

        status_icon = "PASS" if tier_failed == 0 and tier_errors == 0 else "FAIL"
        print(f"\n{tier} Tier: {status_icon}")
        print(f"  Passed: {tier_passed}/5")
        print(f"  Failed: {tier_failed}/5")
        print(f"  Errors: {tier_errors}/5")

        if tier_failed > 0:
            print(f"  Failed runs:")
            for r in tier_results:
                if r.get("status") == "FAIL":
                    print(f"    - {r['run_label']}: {r['company']} ({r['duplicate_count']} duplicates)")

    # Results by prompt
    print()
    print("RESULTS BY PROMPT:")
    print("-" * 80)

    for i in range(1, 6):
        prompt_results = [r for r in all_results if r.get("prompt_num") == i]
        prompt_passed = sum(1 for r in prompt_results if r.get("status") == "PASS")
        prompt_failed = sum(1 for r in prompt_results if r.get("status") == "FAIL")

        status_icon = "PASS" if prompt_failed == 0 else "FAIL"
        company = prompt_results[0]['company'] if prompt_results else "Unknown"
        print(f"\nPrompt {i} ({company}): {status_icon}")
        print(f"  Budget: {prompt_results[0].get('status', 'N/A')}")
        print(f"  Standard: {prompt_results[1].get('status', 'N/A')}")
        print(f"  Premium: {prompt_results[2].get('status', 'N/A')}")

    # Duplicate analysis
    print()
    print("DUPLICATE ANALYSIS:")
    print("-" * 80)

    total_dups = sum(r.get("duplicate_count", 0) for r in all_results if "duplicate_count" in r)
    runs_with_dups = sum(1 for r in all_results if r.get("has_duplicates"))

    print(f"Total duplicate workflows found: {total_dups}")
    print(f"Runs with duplicates: {runs_with_dups}/{total}")

    if runs_with_dups > 0:
        print("\nRuns with duplicates:")
        for r in all_results:
            if r.get("has_duplicates"):
                print(f"  {r['run_label']}: {r['company']} - {r['duplicate_count']} duplicates")
                counts = Counter(r['workflows'])
                dups = [f"{name} (x{count})" for name, count in counts.items() if count > 1]
                print(f"    Duplicates: {', '.join(dups)}")

    # Final verdict
    print()
    print("=" * 80)
    if passed == total:
        print("VALIDATION SUCCESS: ALL 15 RUNS PASSED!")
        print("No duplicates found in any tier or prompt.")
        print("Duplicate bug fix is FULLY VALIDATED.")
    elif errors == 0 and failed == 0:
        print("TEST COMPLETED SUCCESSFULLY")
    else:
        print("VALIDATION INCOMPLETE:")
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
