"""
End-to-end workflow system test.
Runs the complete workflow pipeline as it would in production.
"""
import asyncio
from datetime import datetime

from contexts.workflow.engine import WorkflowEngine
from contexts.workflow.models import EmailInquiry
from contexts.qa.auditor import QAAuditor
from config.dependency_injection import get_container


async def run_end_to_end_workflow(tier: str):
    """Run complete workflow pipeline for a single tier."""
    print(f"\n{'=' * 80}")
    print(f"RUNNING {tier.upper()} TIER WORKFLOW")
    print(f"{'=' * 80}\n")

    # Get container
    container = get_container()

    # Create workflow engine
    engine = WorkflowEngine(
        ai_provider=container.ai_provider(),
        temperatures=container.settings.temperatures,
        min_consensus_votes=container.settings.sc_min_consensus_votes,
    )

    # Create QA auditor
    qa_auditor = QAAuditor(
        ai_provider=container.ai_provider(),
        sheets_client=None,  # Don't log to sheets for this test
        qa_spreadsheet_id=None
    )

    # Create test inquiry (Latham & Watkins LLP - M&A due diligence)
    inquiry = EmailInquiry(
        message_id=f"test-validation-{tier.lower()}",
        from_email="test@example.com",
        from_name="Latham & Watkins LLP",
        subject="Workflow Analysis Request",
        body="""Our law firm specializes in cross-border M&A transactions and we need to streamline our due diligence process. We handle hundreds of documents across multiple jurisdictions, need to verify compliance with various regulatory frameworks, and coordinate between multiple practice groups. What workflow automations would you recommend?"""
    )

    print(f"From: {inquiry.from_name}")
    print(f"Tier: {tier}")
    print(f"Prompt: {inquiry.body[:150]}...")
    print()

    # Process workflow
    print("Processing workflow...")
    start_time = datetime.now()

    try:
        workflow_result, _ = await engine.process_inquiry(inquiry, tier)
        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"✅ Workflow processing complete ({elapsed:.1f}s)")
        print()

        # Analyze results
        print(f"{'─' * 80}")
        print("WORKFLOW RESULTS")
        print(f"{'─' * 80}\n")

        print(f"Run ID: {workflow_result.run_id}")
        print(f"Consensus Strength: {workflow_result.consensus.consensus_strength}")
        print(f"Confidence: {workflow_result.consensus.confidence_percent}%")
        print(f"Votes for Winner: {workflow_result.consensus.votes_for_winner}/{workflow_result.consensus.total_responses}")
        print()

        # Check for duplicates in selected workflows
        selected_workflows = workflow_result.consensus.all_workflows
        workflow_names = [wf.name for wf in selected_workflows]
        unique_names = set(workflow_names)

        print(f"Selected Workflows: {len(workflow_names)}")
        print(f"Unique Workflows: {len(unique_names)}")
        print()

        if len(workflow_names) != len(unique_names):
            print("❌ DUPLICATE WORKFLOWS DETECTED!")
            from collections import Counter
            counts = Counter(workflow_names)
            duplicates = [name for name, count in counts.items() if count > 1]
            print(f"Duplicates: {duplicates}")
            print()
        else:
            print("✅ NO DUPLICATES - All workflows are unique")
            print()

        print("Workflow Names:")
        for i, name in enumerate(workflow_names, 1):
            print(f"  {i}. {name}")
        print()

        # Run QA audit
        print(f"{'─' * 80}")
        print("QA AUDIT")
        print(f"{'─' * 80}\n")

        print("Running QA audit...")
        qa_result = await qa_auditor.audit(workflow_result)

        print(f"QA Score: {qa_result.score}/10")
        print(f"Status: {'✅ PASS' if qa_result.passed else '❌ FAIL'}")
        print(f"Severity: {qa_result.severity.value}")
        print()

        if not qa_result.passed:
            print(f"Failure Type: {qa_result.failure_type.value}")
            print(f"Root Cause: {qa_result.root_cause}")
            print()
            print("Critique:")
            print(qa_result.critique)
            print()

        return {
            "tier": tier,
            "run_id": workflow_result.run_id,
            "consensus_strength": workflow_result.consensus.consensus_strength,
            "confidence": workflow_result.consensus.confidence_percent,
            "workflow_count": len(workflow_names),
            "unique_count": len(unique_names),
            "has_duplicates": len(workflow_names) != len(unique_names),
            "workflow_names": workflow_names,
            "qa_score": qa_result.score,
            "qa_passed": qa_result.passed,
            "qa_severity": qa_result.severity.value,
            "elapsed_seconds": elapsed
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "tier": tier,
            "error": str(e),
            "qa_passed": False
        }


async def main():
    """Run end-to-end test for all three tiers."""
    print("=" * 80)
    print("END-TO-END WORKFLOW SYSTEM TEST - 1×3 VALIDATION")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    tiers = ["Budget", "Standard", "Premium"]
    results = []

    for tier in tiers:
        result = await run_end_to_end_workflow(tier)
        results.append(result)

    # Final summary
    print()
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()

    for result in results:
        if "error" in result:
            print(f"❌ {result['tier']}: ERROR - {result['error']}")
        else:
            tier = result['tier']
            duplicates_status = "❌ HAS DUPLICATES" if result['has_duplicates'] else "✅ NO DUPLICATES"
            qa_status = f"✅ PASS ({result['qa_score']}/10)" if result['qa_passed'] else f"❌ FAIL ({result['qa_score']}/10)"

            print(f"{tier} Tier:")
            print(f"  Duplicates: {duplicates_status}")
            print(f"  QA: {qa_status}")
            print(f"  Consensus: {result['consensus_strength']} ({result['confidence']}%)")
            print(f"  Time: {result['elapsed_seconds']:.1f}s")
            print()

    # Overall verdict
    print("=" * 80)
    budget_result = next((r for r in results if r['tier'] == 'Budget'), None)

    if budget_result and not budget_result.get('error'):
        if not budget_result['has_duplicates']:
            print("✅ DUPLICATE BUG FIX VALIDATED - Budget tier has no duplicates!")
        else:
            print("❌ DUPLICATE BUG STILL PRESENT - Budget tier has duplicates")

        if budget_result['qa_passed']:
            print("✅ QA VALIDATION PASSED - Budget tier meets quality standards")
        else:
            print(f"⚠️  QA VALIDATION: Budget tier scored {budget_result['qa_score']}/10")

    all_passed = all(r.get('qa_passed', False) for r in results if 'error' not in r)
    if all_passed:
        print("✅ ALL TIERS PASSED QA - System working correctly")
    else:
        failed_tiers = [r['tier'] for r in results if not r.get('qa_passed', False)]
        print(f"⚠️  Some tiers did not pass QA: {', '.join(failed_tiers)}")

    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
