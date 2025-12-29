"""
Budget tier validation test - 5 different prompts.
Tests duplicate fix across diverse business scenarios.
"""
import asyncio
import sys
from datetime import datetime
from collections import Counter

from contexts.workflow.engine import WorkflowEngine
from contexts.workflow.models import EmailInquiry
from contexts.testing.test_cases import get_test_cases
from config.dependency_injection import get_container


async def test_prompt(prompt_num: int, test_case, engine):
    """Test single prompt."""
    print(f"\n{'=' * 80}")
    print(f"PROMPT {prompt_num}: {test_case.company}")
    print(f"{'=' * 80}")

    inquiry = EmailInquiry(
        message_id=f"budget-test-{prompt_num}",
        from_email="test@example.com",
        from_name=test_case.company,
        subject="Workflow Analysis",
        body=test_case.prompt
    )

    print(f"Company: {test_case.company}")
    print(f"Category: {test_case.category}")
    print(f"Prompt: {test_case.prompt[:100]}...")
    print()

    start = datetime.now()

    try:
        result, _ = await engine.process_inquiry(inquiry, "Budget")
        elapsed = (datetime.now() - start).total_seconds()

        # Check for duplicates
        names = [wf.name for wf in result.consensus.all_workflows]
        unique = set(names)
        has_dups = len(names) != len(unique)

        print(f"\nRESULTS:")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Consensus: {result.consensus.consensus_strength} ({result.consensus.confidence_percent}%)")
        print(f"  Workflows: {len(names)}")
        print(f"  Unique: {len(unique)}")

        if has_dups:
            print(f"  STATUS: FAIL - DUPLICATES FOUND")
            counts = Counter(names)
            dups = [f"{name} (x{count})" for name, count in counts.items() if count > 1]
            print(f"  Duplicates: {', '.join(dups)}")
        else:
            print(f"  STATUS: PASS - No duplicates")

        print(f"\nSelected Workflows:")
        for i, name in enumerate(names, 1):
            print(f"  {i}. {name}")

        return {
            "prompt_num": prompt_num,
            "company": test_case.company,
            "elapsed": elapsed,
            "has_duplicates": has_dups,
            "duplicate_count": len(names) - len(unique) if has_dups else 0,
            "workflows": names,
            "consensus": result.consensus.consensus_strength,
            "confidence": result.consensus.confidence_percent
        }

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "prompt_num": prompt_num,
            "company": test_case.company,
            "error": str(e),
            "has_duplicates": None
        }


async def main():
    print("=" * 80)
    print("BUDGET TIER - 5 PROMPT VALIDATION TEST")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Get 5 test cases
    test_cases = get_test_cases(count=5)

    print(f"Testing {len(test_cases)} prompts:")
    for i, tc in enumerate(test_cases, 1):
        print(f"  {i}. {tc.company} ({tc.category})")
    print()

    # Create engine once and reuse
    container = get_container()
    engine = WorkflowEngine(
        ai_provider=container.ai_provider(),
        temperatures=container.settings.temperatures,
        min_consensus_votes=container.settings.sc_min_consensus_votes,
    )

    # Run all 5 tests
    results = []
    for i, test_case in enumerate(test_cases, 1):
        result = await test_prompt(i, test_case, engine)
        results.append(result)

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}\n")

    total = len(results)
    errors = sum(1 for r in results if "error" in r)
    passed = sum(1 for r in results if not r.get("error") and not r.get("has_duplicates"))
    failed = sum(1 for r in results if not r.get("error") and r.get("has_duplicates"))

    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
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
            print(f"  Consensus: {r['consensus']} ({r['confidence']}%)")
            print(f"  Time: {r['elapsed']:.1f}s")
            if r['has_duplicates']:
                print(f"  Workflows: {r['workflows']}")

    # Final verdict
    print(f"\n{'=' * 80}")
    if passed == total:
        print("VALIDATION SUCCESS: All prompts passed with no duplicates!")
    elif errors == 0 and failed == 0:
        print("VALIDATION SUCCESS: All prompts passed!")
    else:
        print(f"VALIDATION PARTIAL: {passed}/{total} passed, {failed} failed, {errors} errors")

    if failed > 0:
        print("\nDUPLICATE BUG STILL PRESENT in some prompts")
    else:
        print("\nDUPLICATE BUG FIXED across all test prompts")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    # Set stdout encoding to UTF-8 to handle Unicode
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    asyncio.run(main())
