"""Test synthesis with improved anti-hallucination prompts."""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_synthesis():
    from infrastructure.ai.claude_adapter import ClaudeAdapter
    from contexts.compass.two_call_engine import TwoCallCompassEngine
    from contexts.compass.models import CompassRequest, SelfAssessment

    api_key = os.getenv('ANTHROPIC_API_KEY')
    ai = ClaudeAdapter(api_key=api_key)
    engine = TwoCallCompassEngine(ai_provider=ai)

    request = CompassRequest(
        company_name='Patagonia',
        website='https://www.patagonia.com',
        industry='Retail & Apparel',
        company_size='1000-5000 employees',
        pain_point='Customer service automation and inventory management',
        description='Outdoor clothing and gear retailer focused on sustainability.',
        email='test@example.com',
        contact_name='Test User',
        self_assessment=SelfAssessment(data_maturity=3, automation_experience=2, change_readiness=4),
    )

    print('=' * 70)
    print('TESTING SYNTHESIS ANTI-HALLUCINATION')
    print('=' * 70)
    print(f'Company: {request.company_name}')
    print('=' * 70)
    print()

    result = await engine.process(request)

    print('=' * 70)
    print('RESULTS')
    print('=' * 70)

    if result.research_quality:
        rq = result.research_quality
        print(f'Research Quality: {"PASS" if rq.passed else "FAIL"}')
        print(f'  Verified Sources: {rq.verified_source_count}')
        print(f'  Unique Domains: {rq.unique_domain_count}')

    print()
    print(f'QA Passed: {result.qa_passed}')

    if result.qa_issues:
        print()
        print('QA ISSUES:')
        hallucinations = [i for i in result.qa_issues if 'HALLUCINATION' in i.upper()]
        print(f'  Hallucinations detected: {len(hallucinations)}')
        for h in hallucinations[:5]:
            print(f'    - {h[:80]}...' if len(h) > 80 else f'    - {h}')

    if result.report:
        print()
        print('REPORT GENERATED: YES')
        print(f'  AI Readiness: {result.report.ai_readiness_score.overall_score}/100')

    print()
    print('=' * 70)
    print('COMPLETE')
    print('=' * 70)


if __name__ == '__main__':
    asyncio.run(test_synthesis())
