"""Simple validation test - no emojis, Windows-compatible output."""
import asyncio
import sys
from datetime import datetime
from collections import Counter

from contexts.workflow.engine import WorkflowEngine
from contexts.workflow.models import EmailInquiry
from contexts.qa.auditor import QAAuditor
from config.dependency_injection import get_container


async def test_tier(tier: str):
    """Test single tier."""
    print(f"\n{'-' * 80}")
    print(f"TESTING {tier.upper()} TIER")
    print(f"{'-' * 80}")

    container = get_container()
    engine = WorkflowEngine(
        ai_provider=container.ai_provider(),
        temperatures=container.settings.temperatures,
        min_consensus_votes=container.settings.sc_min_consensus_votes,
    )

    inquiry = EmailInquiry(
        message_id=f"test-{tier.lower()}",
        from_email="test@example.com",
        from_name="Latham & Watkins LLP",
        subject="Workflow Analysis",
        body="Our law firm specializes in cross-border M&A transactions and we need to streamline our due diligence process. We handle hundreds of documents across multiple jurisdictions, need to verify compliance with various regulatory frameworks, and coordinate between multiple practice groups. What workflow automations would you recommend?"
    )

    print(f"\nProcessing {tier} tier workflow...")
    start = datetime.now()

    try:
        result, _ = await engine.process_inquiry(inquiry, tier)
        elapsed = (datetime.now() - start).total_seconds()

        # Check for duplicates
        names = [wf.name for wf in result.consensus.all_workflows]
        unique = set(names)
        has_dups = len(names) != len(unique)

        print(f"\nRESULTS:")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Consensus: {result.consensus.consensus_strength} ({result.consensus.confidence_percent}%)")
        print(f"  Workflows selected: {len(names)}")
        print(f"  Unique workflows: {len(unique)}")

        if has_dups:
            print(f"  DUPLICATE BUG: {len(names) - len(unique)} duplicates found")
            counts = Counter(names)
            dups = [f"{name} (x{count})" for name, count in counts.items() if count > 1]
            print(f"  Duplicates: {', '.join(dups)}")
        else:
            print(f"  PASS: No duplicates")

        print(f"\nSelected Workflows:")
        for i, name in enumerate(names, 1):
            print(f"  {i}. {name}")

        # QA Audit
        print(f"\nRunning QA audit...")
        qa_auditor = QAAuditor(
            ai_provider=container.ai_provider(),
            sheets_client=None,
            qa_spreadsheet_id=None
        )
        qa = await qa_auditor.audit(result)

        print(f"  QA Score: {qa.score}/10")
        print(f"  QA Status: {'PASS' if qa.passed else 'FAIL'}")
        print(f"  Severity: {qa.severity.value}")

        if not qa.passed:
            print(f"  Root Cause: {qa.root_cause}")

        return {
            "tier": tier,
            "elapsed": elapsed,
            "has_duplicates": has_dups,
            "workflow_count": len(names),
            "qa_score": qa.score,
            "qa_passed": qa.passed,
            "workflows": names
        }

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"tier": tier, "error": str(e)}


async def main():
    print("=" * 80)
    print("END-TO-END VALIDATION TEST - DUPLICATE BUG FIX")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []
    for tier in ["Budget", "Standard", "Premium"]:
        result = await test_tier(tier)
        results.append(result)

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}\n")

    for r in results:
        if "error" in r:
            print(f"{r['tier']}: ERROR - {r['error']}")
        else:
            dup_status = "FAIL - HAS DUPLICATES" if r['has_duplicates'] else "PASS - NO DUPLICATES"
            qa_status = f"PASS ({r['qa_score']}/10)" if r['qa_passed'] else f"FAIL ({r['qa_score']}/10)"
            print(f"{r['tier']} Tier:")
            print(f"  Duplicates: {dup_status}")
            print(f"  QA: {qa_status}")
            print(f"  Time: {r['elapsed']:.1f}s\n")

    # Final verdict
    print(f"{'=' * 80}")
    budget = next((r for r in results if r['tier'] == 'Budget'), None)
    if budget and not budget.get('error'):
        if not budget['has_duplicates']:
            print("VALIDATION SUCCESS: Budget tier has no duplicates!")
        else:
            print("VALIDATION FAILED: Budget tier still has duplicates")

        if all(not r.get('has_duplicates', True) for r in results if 'error' not in r):
            print("All tiers passed duplicate check")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    # Set stdout encoding to UTF-8 to handle Unicode
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    asyncio.run(main())
