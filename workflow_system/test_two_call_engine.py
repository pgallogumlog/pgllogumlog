"""
Test script for the Two-Call Compass Engine.

Runs a single test with the new architecture to validate:
1. Deep research call with low temperature (0.2)
2. Strategic synthesis call with moderate temperature (0.4)
3. Hallucination validation
4. Full report generation
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add workflow_system to path
sys.path.insert(0, str(Path(__file__).parent))

from contexts.compass.models import CompassRequest, SelfAssessment
from contexts.compass.two_call_engine import TwoCallCompassEngine
from infrastructure.ai.claude_adapter import ClaudeAdapter


async def run_two_call_test():
    """Run a single test with the two-call engine."""

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return

    # Initialize AI provider
    ai_provider = ClaudeAdapter(api_key=api_key)

    # Initialize two-call engine
    engine = TwoCallCompassEngine(
        ai_provider=ai_provider,
        enable_web_search=True,
    )

    # Create test request
    request = CompassRequest(
        company_name="TechStart Solutions",
        website="https://techstartsolutions.com",
        industry="Software Development",
        company_size="10-50 employees",
        self_assessment=SelfAssessment(
            data_maturity=3,
            automation_experience=2,
            change_readiness=4,
        ),
        pain_point="Developer productivity",
        description="Our development team spends too much time on repetitive tasks like code reviews, documentation, and debugging. We want to explore how AI can help automate these processes and free up developers for more creative work.",
        email="test@techstartsolutions.com",
        contact_name="Alex Chen",
    )

    print("=" * 70)
    print("TWO-CALL COMPASS ENGINE TEST")
    print("=" * 70)
    print(f"\nCompany: {request.company_name}")
    print(f"Industry: {request.industry}")
    print(f"Pain Point: {request.pain_point}")
    print(f"\nSelf-Assessment Scores:")
    print(f"  - Data Maturity: {request.self_assessment.data_maturity}/5")
    print(f"  - Automation Experience: {request.self_assessment.automation_experience}/5")
    print(f"  - Change Readiness: {request.self_assessment.change_readiness}/5")
    print("\n" + "-" * 70)
    print("Starting two-call processing...")
    print("-" * 70)

    start_time = datetime.now()

    try:
        result = await engine.process(request)

        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"\n{'=' * 70}")
        print("RESULTS")
        print("=" * 70)

        if result.error:
            print(f"\nERROR: {result.error}")
            return

        print(f"\nProcessing Time: {elapsed:.1f} seconds")
        print(f"QA Passed: {result.qa_passed}")
        print(f"QA Score: {result.qa_score}/10")

        if result.report:
            score = result.report.ai_readiness_score
            print(f"\n--- AI Readiness Score ---")
            print(f"Overall Score: {score.overall_score:.1f}/100")
            print(f"  - Self-Assessment (30%): {score.self_assessment_score:.1f}")
            print(f"  - Research (70%): {score.research_score:.1f}")

            print(f"\n--- Priorities ({len(result.report.priorities)}) ---")
            for p in result.report.priorities:
                print(f"\n  #{p.rank}: {p.problem_name}")
                print(f"      Solution: {p.solution.name}")
                print(f"      Approach: {p.solution.approach_type}")
                print(f"      Complexity: {p.solution.complexity}")
                if p.solution.tools:
                    print(f"      Tools: {', '.join(p.solution.tools[:3])}")

            print(f"\n--- Anti-Recommendations ({len(result.report.avoid)}) ---")
            for a in result.report.avoid:
                print(f"\n  AVOID: {a.name}")
                print(f"      Why tempting: {a.why_tempting[:80]}...")

            print(f"\n--- 90-Day Roadmap ({len(result.report.roadmap)} phases) ---")
            for r in result.report.roadmap:
                print(f"\n  Month {r.month}: {r.focus}")
                print(f"      Decision Gate: {r.decision_gate[:60]}...")

            # Save HTML report
            html_dir = Path("test_results")
            html_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = html_dir / f"two_call_test_{timestamp}.html"
            html_path.write_text(result.report.html_content, encoding="utf-8")
            print(f"\n--- HTML Report Saved ---")
            print(f"Path: {html_path}")
            print(f"Size: {len(result.report.html_content):,} bytes")

        # Show research metadata
        if result.research_findings:
            metadata = result.research_findings.get("research_metadata", {})
            print(f"\n--- Research Quality ---")
            print(f"Total Findings: {metadata.get('total_findings', 'N/A')}")
            print(f"High Confidence: {metadata.get('high_confidence_findings', 'N/A')}")
            print(f"Sources Consulted: {metadata.get('sources_consulted', 'N/A')}")
            gaps = metadata.get("research_gaps", [])
            if gaps:
                print(f"Research Gaps: {len(gaps)}")
                for gap in gaps[:3]:
                    print(f"  - {gap}")

        # Show synthesis metadata
        if result.synthesis_output:
            syn_meta = result.synthesis_output.get("synthesis_metadata", {})
            print(f"\n--- Synthesis Quality ---")
            print(f"Confidence Level: {syn_meta.get('confidence_level', 'N/A')}")
            print(f"Findings Used: {syn_meta.get('research_findings_used', 'N/A')}")
            validation_issues = syn_meta.get("validation_issues", [])
            if validation_issues:
                print(f"Validation Issues: {len(validation_issues)}")
                for issue in validation_issues[:3]:
                    print(f"  - {issue}")

        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)

    except Exception as e:
        print(f"\nEXCEPTION: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Load .env if available
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    asyncio.run(run_two_call_test())
