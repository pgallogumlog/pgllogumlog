"""
Automated validation test for duplicate workflow fix.

Runs 1×3 test (Latham & Watkins LLP across Budget/Standard/Premium tiers)
to validate that duplicate workflow bug is fixed.
"""
import asyncio
import json
from datetime import datetime

from contexts.testing.orchestrator import TestOrchestrator
from contexts.testing.test_cases import get_test_case_by_name
from contexts.testing.models import TestConfig
from config.dependency_injection import get_container


async def run_validation_test():
    """Run 1×3 validation test and analyze results."""
    print("=" * 80)
    print("DUPLICATE WORKFLOW FIX - VALIDATION TEST")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get test case
    test_case = get_test_case_by_name("Latham & Watkins LLP")
    if not test_case:
        print("❌ ERROR: Could not find 'Latham & Watkins LLP' test case")
        return

    print(f"Test Case: {test_case.name}")
    print(f"Prompt: {test_case.normalized_prompt[:100]}...")
    print()

    # Configure test
    config = TestConfig(
        test_cases=[test_case],
        tiers=["Budget", "Standard", "Premium"],
        count_per_tier=1,
        enable_qa=True,
        save_html_results=False
    )

    # Get container and orchestrator
    container = get_container()
    orchestrator = TestOrchestrator(
        ai_provider=container.ai_provider(),
        sheets_client=container.sheets_client(),
        settings=container.settings
    )

    # Run test
    print("Running test suite...")
    print("-" * 80)
    results = await orchestrator.run_test_suite(config)

    # Analyze results
    print()
    print("=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)
    print()

    total_tests = len(results)
    passed = sum(1 for r in results if r.qa_result and r.qa_result.passed)
    failed = total_tests - passed

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()

    # Detailed results by tier
    print("DETAILED RESULTS BY TIER:")
    print("-" * 80)

    tiers = ["Budget", "Standard", "Premium"]
    tier_results = {tier: [] for tier in tiers}

    for result in results:
        tier_results[result.tier].append(result)

    for tier in tiers:
        tier_test_results = tier_results[tier]
        if not tier_test_results:
            continue

        result = tier_test_results[0]  # We only ran 1 per tier
        qa_result = result.qa_result

        print(f"\n{tier} Tier:")
        print(f"  QA Score: {qa_result.score}/10")
        print(f"  Status: {'✅ PASS' if qa_result.passed else '❌ FAIL'}")
        print(f"  Severity: {qa_result.severity.value}")

        # Check for duplicates in selected workflows
        workflow_names = [wf.name for wf in result.consensus.all_workflows]
        unique_names = set(workflow_names)

        if len(workflow_names) != len(unique_names):
            print(f"  ❌ DUPLICATE DETECTED!")
            print(f"  Selected workflows: {workflow_names}")
            # Find duplicates
            from collections import Counter
            counts = Counter(workflow_names)
            duplicates = [name for name, count in counts.items() if count > 1]
            print(f"  Duplicates: {duplicates}")
        else:
            print(f"  ✅ No duplicates (all {len(workflow_names)} workflows unique)")

        print(f"  Workflows: {workflow_names}")
        print(f"  Run ID: {result.run_id}")

        if not qa_result.passed:
            print(f"  Failure Reason: {qa_result.root_cause}")
            print(f"  Critique: {qa_result.critique[:200]}...")

    # Summary
    print()
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()

    # Check if Budget tier is fixed
    budget_results = tier_results.get("Budget", [])
    if budget_results:
        budget_result = budget_results[0]
        budget_workflows = [wf.name for wf in budget_result.consensus.all_workflows]
        budget_unique = set(budget_workflows)

        if len(budget_workflows) == len(budget_unique):
            print("✅ Budget Tier: NO DUPLICATES (Bug fixed!)")
        else:
            print("❌ Budget Tier: DUPLICATES STILL PRESENT")
            duplicates = [name for name in budget_workflows if budget_workflows.count(name) > 1]
            print(f"   Duplicates: {set(duplicates)}")

        if budget_result.qa_result.passed:
            print(f"✅ Budget Tier: QA PASSED ({budget_result.qa_result.score}/10)")
        else:
            print(f"❌ Budget Tier: QA FAILED ({budget_result.qa_result.score}/10)")

    # Check Standard and Premium
    for tier in ["Standard", "Premium"]:
        tier_test_results = tier_results.get(tier, [])
        if tier_test_results:
            result = tier_test_results[0]
            if result.qa_result.passed:
                print(f"✅ {tier} Tier: QA PASSED ({result.qa_result.score}/10) - No regression")
            else:
                print(f"❌ {tier} Tier: QA FAILED ({result.qa_result.score}/10) - REGRESSION!")

    print()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Return summary for programmatic use
    return {
        "total": total_tests,
        "passed": passed,
        "failed": failed,
        "budget_has_duplicates": len(budget_workflows) != len(budget_unique) if budget_results else None,
        "budget_qa_passed": budget_result.qa_result.passed if budget_results else None,
        "results_by_tier": {
            tier: {
                "qa_score": tier_results[tier][0].qa_result.score if tier_results[tier] else None,
                "qa_passed": tier_results[tier][0].qa_result.passed if tier_results[tier] else None,
                "workflow_count": len(tier_results[tier][0].consensus.all_workflows) if tier_results[tier] else None,
            }
            for tier in tiers
        }
    }


if __name__ == "__main__":
    asyncio.run(run_validation_test())
