"""
Run comprehensive workflow analysis: 50 prompts × 3 tiers = 150 test runs.

Generates 3,750 workflows (150 runs × 25 workflows per run) and exports to JSON
for data-driven analysis of workflow selection methods.

Usage:
    python run_workflow_analysis.py                      # Run all 50×3, export to data/workflow_analysis.json
    python run_workflow_analysis.py --count 10           # Test with 10 prompts first
    python run_workflow_analysis.py --output custom.json # Custom output path
    python run_workflow_analysis.py --mock               # Use mock AI (for testing)
    python run_workflow_analysis.py --save-html          # Also save HTML proposals
"""

import asyncio
import sys
from datetime import datetime

from config import get_container
from contexts.testing import TestOrchestrator, TestConfig
from contexts.testing.models import Environment, Tier


def parse_args():
    """Parse command line arguments."""
    args = {
        "count": 50,  # Default to 50 prompts for full analysis
        "output": "data/workflow_analysis.json",  # Default output path
        "use_mock": "--mock" in sys.argv,
        "save_html": "--save-html" in sys.argv,
    }

    # Parse --count argument
    if "--count" in sys.argv:
        idx = sys.argv.index("--count")
        if idx + 1 < len(sys.argv):
            try:
                args["count"] = int(sys.argv[idx + 1])
            except ValueError:
                pass

    # Parse --output argument
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            args["output"] = sys.argv[idx + 1]

    return args


async def run_workflow_analysis(count: int = 50, output: str = "data/workflow_analysis.json",
                                 use_mock: bool = False, save_html: bool = False):
    """
    Run comprehensive workflow analysis.

    Args:
        count: Number of test prompts to run (default: 50)
        output: JSON output file path
        use_mock: Use mock AI provider instead of real API
        save_html: Also save HTML proposals to test_results/
    """
    container = get_container()
    settings = container.settings

    print("=" * 80)
    print("WORKFLOW ANALYSIS - DATA COLLECTION")
    print("=" * 80)
    print(f"Prompts: {count}")
    print(f"Tiers: 3 (Budget, Standard, Premium)")
    print(f"Total Runs: {count * 3}")
    print(f"Expected Workflows: {count * 3 * 25} (assuming 25 workflows per run)")
    print(f"Output JSON: {output}")
    print(f"AI Provider: {'MOCK' if use_mock else 'REAL (Claude API)'}")
    print(f"Save HTML: {'ENABLED' if save_html else 'DISABLED'}")
    print("=" * 80)
    print()

    # Estimate cost
    if not use_mock:
        estimated_cost = count * 3 * 0.40  # Rough estimate: $0.40 per run
        print(f"WARNING: ESTIMATED API COST: ${estimated_cost:.2f}")
        print(f"         (Based on ~$0.40/run x {count * 3} runs)")
        print()
        response = input("Continue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("CANCELLED by user")
            return

    start_time = datetime.now()

    # Choose AI provider
    if use_mock:
        from tests.conftest import MockAIProvider
        base_provider = MockAIProvider()
        print("\nUsing MOCK AI provider (no API calls)")
    else:
        base_provider = container.ai_provider()
        print("\nUsing REAL Claude API")

    # QA not needed for this data collection
    ai_provider = base_provider

    # Create test orchestrator with JSON export enabled
    orchestrator = TestOrchestrator(
        ai_provider=ai_provider,
        sheets_client=container.sheets_client(),
        qa_spreadsheet_id=settings.google_sheets_qa_log_id,
        email_client=None,  # Don't send emails
        send_emails=False,
        html_output_dir="test_results" if save_html else None,
        json_export_path=output,  # ENABLE JSON EXPORT
    )

    print(f"\nStarting workflow analysis...")
    print(f"Collecting data from {count} prompts across 3 tiers")
    print()

    # Create test config for ALL tiers
    config = TestConfig(
        environment=Environment.PRODUCTION,  # Use production environment
        tier=Tier.ALL,  # Run all 3 tiers
        count=count,
        parallel=True,  # Run in parallel for speed
        max_parallel=5,  # Limit concurrent API calls
    )

    # Run the test suite
    suite_result = await orchestrator.run_tests(config)

    # Calculate duration
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Summary
    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Total Runs: {suite_result.total_tests}")
    print(f"Passed: {suite_result.passed}")
    print(f"Failed: {suite_result.failed}")
    print(f"Pass Rate: {suite_result.pass_rate:.1f}%")
    print(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
    print(f"JSON Export: {output}")
    print("=" * 80)
    print()
    print("Next Steps:")
    print(f"   1. Review exported data: {output}")
    print(f"   2. Analyze workflow patterns to determine selection method")
    print(f"   3. Use insights to design optimal workflow ranking algorithm")
    print()


def main():
    """Main entry point."""
    args = parse_args()

    print("\nWorkflow Analysis Tool")
    print("----------------------")
    print(f"This will generate {args['count'] * 3 * 25} workflow recommendations")
    print(f"across {args['count']} prompts and 3 tiers for data-driven analysis.\n")

    asyncio.run(run_workflow_analysis(
        count=args["count"],
        output=args["output"],
        use_mock=args["use_mock"],
        save_html=args["save_html"],
    ))


if __name__ == "__main__":
    main()
