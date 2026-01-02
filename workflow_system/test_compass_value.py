"""
COO Value Assessment: AI Readiness Compass Report Evaluation

Tests 5 diverse scenarios to evaluate:
- Report quality and completeness
- Dollar value delivered vs $497 price point
- Target: $1,000-$2,000 value per report

Run with: python test_compass_value.py
"""

import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from contexts.compass.engine import CompassEngine
from contexts.compass.models import CompassRequest, SelfAssessment
from infrastructure.ai.claude_adapter import ClaudeAdapter


# 5 Diverse Test Scenarios
TEST_SCENARIOS = [
    {
        "name": "Scenario 1: Mid-Market CRE Firm",
        "request": CompassRequest(
            company_name="Pinnacle Commercial Properties",
            website="https://pinnaclecommercial.com",
            industry="Commercial Real Estate",
            company_size="50-200 employees",
            self_assessment=SelfAssessment(
                data_maturity=3,
                automation_experience=2,
                change_readiness=4,
            ),
            pain_point="Tenant communication and lease management",
            description="We manage 45 commercial properties across 3 states. Our property managers spend 60% of their time on routine tenant inquiries and lease paperwork. We're losing deals because response times are too slow.",
            email="test@pinnaclecommercial.com",
            contact_name="Sarah Chen",
        ),
    },
    {
        "name": "Scenario 2: Regional Healthcare Network",
        "request": CompassRequest(
            company_name="MidWest Health Partners",
            website="https://midwesthealthpartners.org",
            industry="Healthcare",
            company_size="500-1000 employees",
            self_assessment=SelfAssessment(
                data_maturity=4,
                automation_experience=3,
                change_readiness=3,
            ),
            pain_point="Patient intake and appointment scheduling",
            description="Our 12-clinic network processes 500+ new patient intakes weekly. Staff spend hours on manual data entry and phone scheduling. No-show rates are 18% and we have no good way to predict or prevent them.",
            email="test@midwesthealthpartners.org",
            contact_name="Dr. Michael Torres",
        ),
    },
    {
        "name": "Scenario 3: E-commerce Retailer",
        "request": CompassRequest(
            company_name="Urban Gear Collective",
            website="https://urbangearcollective.com",
            industry="E-commerce Retail",
            company_size="20-50 employees",
            self_assessment=SelfAssessment(
                data_maturity=4,
                automation_experience=3,
                change_readiness=5,
            ),
            pain_point="Customer service and returns processing",
            description="We get 200+ support tickets daily, mostly about order status, sizing, and returns. Our 5-person support team is overwhelmed. Returns are 12% of revenue and we need to predict and reduce them.",
            email="test@urbangearcollective.com",
            contact_name="Alex Rivera",
        ),
    },
    {
        "name": "Scenario 4: Manufacturing Company",
        "request": CompassRequest(
            company_name="Precision Dynamics Manufacturing",
            website="https://precisiondynamics.com",
            industry="Manufacturing",
            company_size="200-500 employees",
            self_assessment=SelfAssessment(
                data_maturity=2,
                automation_experience=2,
                change_readiness=3,
            ),
            pain_point="Quality control and defect prediction",
            description="We manufacture precision components for aerospace. Quality inspection is manual and time-consuming. We need to catch defects earlier in the process and reduce waste from scrapped parts.",
            email="test@precisiondynamics.com",
            contact_name="Robert Martinez",
        ),
    },
    {
        "name": "Scenario 5: Professional Services Firm",
        "request": CompassRequest(
            company_name="Sterling Advisory Group",
            website="https://sterlingadvisory.com",
            industry="Professional Services / Consulting",
            company_size="100-200 employees",
            self_assessment=SelfAssessment(
                data_maturity=3,
                automation_experience=2,
                change_readiness=4,
            ),
            pain_point="Proposal creation and knowledge management",
            description="Our consultants spend 20+ hours per proposal pulling from past work, case studies, and expertise across the firm. Knowledge is siloed. We're losing to competitors who respond faster with more tailored proposals.",
            email="test@sterlingadvisory.com",
            contact_name="Jennifer Walsh",
        ),
    },
]


async def run_compass_test(scenario: dict, output_dir: Path) -> dict:
    """Run a single compass test and return metrics."""
    print(f"\n{'='*70}")
    print(f"RUNNING: {scenario['name']}")
    print(f"{'='*70}")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "No API key"}

    # Initialize engine
    ai_provider = ClaudeAdapter(api_key=api_key)
    engine = CompassEngine(
        ai_provider=ai_provider,
        enable_web_research=True,
    )

    start_time = datetime.now()

    try:
        result = await engine.process(scenario["request"])

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        if result.report:
            # Save HTML report
            report_file = output_dir / f"{scenario['request'].company_name.replace(' ', '_')}_report.html"
            report_file.write_text(result.report.html_content, encoding='utf-8')

            # Calculate metrics
            metrics = {
                "scenario": scenario["name"],
                "company": scenario["request"].company_name,
                "industry": scenario["request"].industry,
                "success": True,
                "duration_seconds": round(duration, 1),
                "ai_readiness_score": round(result.report.ai_readiness_score.overall_score, 1),
                "self_assessment_score": round(result.report.ai_readiness_score.self_assessment_score, 1),
                "research_score": round(result.report.ai_readiness_score.research_score, 1),
                "priorities_count": len(result.report.priorities),
                "avoid_count": len(result.report.avoid),
                "roadmap_phases": len(result.report.roadmap),
                "html_length": len(result.report.html_content),
                "qa_passed": result.qa_passed,
                "qa_score": result.qa_score,
                "report_file": str(report_file),
            }

            # Extract priority details for value assessment
            priorities_detail = []
            for p in result.report.priorities:
                priorities_detail.append({
                    "rank": p.rank,
                    "problem": p.problem_name,
                    "solution": p.solution.name,
                    "vendor": getattr(p.solution, 'vendor', 'N/A'),
                    "expected_impact": p.solution.expected_impact,
                    "time_to_value": getattr(p.solution, 'time_to_value', 'N/A'),
                })
            metrics["priorities_detail"] = priorities_detail

            # Extract anti-recommendations
            avoid_detail = []
            for a in result.report.avoid:
                avoid_detail.append({
                    "name": a.name,
                    "cost_of_mistake": getattr(a, 'cost_of_mistake', 'N/A'),
                })
            metrics["avoid_detail"] = avoid_detail

            print(f"\n[PASS] SUCCESS")
            print(f"   Score: {metrics['ai_readiness_score']}/100")
            print(f"   Duration: {metrics['duration_seconds']}s")
            print(f"   Priorities: {metrics['priorities_count']}")
            print(f"   Report: {report_file.name}")

        else:
            metrics = {
                "scenario": scenario["name"],
                "company": scenario["request"].company_name,
                "success": False,
                "error": result.error or "Unknown error",
                "duration_seconds": round(duration, 1),
            }
            print(f"\n[FAIL] FAILED: {result.error}")

    except Exception as e:
        metrics = {
            "scenario": scenario["name"],
            "company": scenario["request"].company_name,
            "success": False,
            "error": str(e),
        }
        print(f"\n[ERROR] EXCEPTION: {e}")

    finally:
        await engine.close()

    return metrics


async def main():
    """Run all compass tests and generate summary."""
    print("\n" + "="*70)
    print("COO VALUE ASSESSMENT: AI Readiness Compass Reports")
    print("="*70)
    print(f"Target: $1,000-$2,000 value for $497 cost (2x-4x ROI)")
    print(f"Running {len(TEST_SCENARIOS)} diverse test scenarios...")

    # Create output directory
    output_dir = Path("test_reports") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run all tests
    all_metrics = []
    for scenario in TEST_SCENARIOS:
        metrics = await run_compass_test(scenario, output_dir)
        all_metrics.append(metrics)

    # Save metrics
    metrics_file = output_dir / "metrics.json"
    metrics_file.write_text(json.dumps(all_metrics, indent=2), encoding='utf-8')

    # Generate summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    successful = [m for m in all_metrics if m.get("success")]
    failed = [m for m in all_metrics if not m.get("success")]

    print(f"\nResults: {len(successful)}/{len(all_metrics)} successful")

    if successful:
        avg_score = sum(m["ai_readiness_score"] for m in successful) / len(successful)
        avg_duration = sum(m["duration_seconds"] for m in successful) / len(successful)
        avg_priorities = sum(m["priorities_count"] for m in successful) / len(successful)
        avg_html_length = sum(m["html_length"] for m in successful) / len(successful)

        print(f"\nAverage Metrics:")
        print(f"   AI Readiness Score: {avg_score:.1f}/100")
        print(f"   Generation Time: {avg_duration:.1f}s")
        print(f"   Priorities per Report: {avg_priorities:.1f}")
        print(f"   Report Size: {avg_html_length/1000:.1f} KB")

        print(f"\nIndividual Results:")
        for m in successful:
            print(f"\n   {m['company']} ({m['industry']})")
            print(f"      Score: {m['ai_readiness_score']}/100")
            print(f"      Time: {m['duration_seconds']}s")
            if m.get("priorities_detail"):
                print(f"      Top Priority: {m['priorities_detail'][0]['problem']}")
                print(f"      Solution: {m['priorities_detail'][0]['solution']}")
                print(f"      Impact: {m['priorities_detail'][0]['expected_impact']}")

    if failed:
        print(f"\nFailed Tests:")
        for m in failed:
            print(f"   [FAIL] {m['company']}: {m.get('error', 'Unknown')}")

    print(f"\nReports saved to: {output_dir}")
    print(f"Metrics saved to: {metrics_file}")

    return all_metrics


if __name__ == "__main__":
    asyncio.run(main())
