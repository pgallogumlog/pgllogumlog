"""Debug script to understand why quality gate is failing."""
import asyncio
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()


async def debug_research():
    from infrastructure.ai.claude_adapter import ClaudeAdapter
    from contexts.compass.models import CompassRequest, SelfAssessment
    from contexts.compass.prompts import DEEP_RESEARCH_SYSTEM, DEEP_RESEARCH_USER_TEMPLATE
    from contexts.compass.validators.research_quality_gate import ResearchQualityGate

    api_key = os.getenv('ANTHROPIC_API_KEY')
    ai = ClaudeAdapter(api_key=api_key)

    request = CompassRequest(
        company_name='Patagonia',
        website='https://www.patagonia.com',
        industry='Retail & Apparel',
        company_size='1000-5000 employees',
        pain_point='Customer service automation',
        description='Outdoor clothing retailer',
        email='test@example.com',
        contact_name='Test',
        self_assessment=SelfAssessment(data_maturity=3, automation_experience=2, change_readiness=4),
    )

    user_prompt = DEEP_RESEARCH_USER_TEMPLATE.format(
        company_name=request.company_name,
        website=request.website,
        industry=request.industry,
        company_size=request.company_size,
        pain_point=request.pain_point,
        description=request.description,
        data_maturity=request.self_assessment.data_maturity,
        automation_experience=request.self_assessment.automation_experience,
        change_readiness=request.self_assessment.change_readiness,
    )

    print('Running research...')
    research, metadata, citations = await ai.generate_json_with_web_search(
        prompt=user_prompt,
        system_prompt=DEEP_RESEARCH_SYSTEM,
        max_tokens=8192,
        max_searches=15,
    )

    print(f'Citations: {len(citations)}')
    print()

    # Check if Patagonia is in research
    research_str = json.dumps(research).lower()
    patagonia_count = research_str.count('patagonia')
    print(f'"Patagonia" mentions in research: {patagonia_count}')

    # Check for retail mentions
    retail_count = research_str.count('retail')
    print(f'"Retail" mentions: {retail_count}')

    # Check for percentage patterns
    pct_matches = re.findall(r'\d+%', research_str)
    print(f'Percentage patterns found: {len(pct_matches)}')
    if pct_matches:
        print(f'  Examples: {pct_matches[:5]}')

    # Test quality gate checks directly
    gate = ResearchQualityGate()

    has_company = gate._has_company_findings(research, 'Patagonia')
    print(f'\n_has_company_findings("Patagonia"): {has_company}')

    has_industry = gate._has_industry_stats(research, 'Retail & Apparel')
    print(f'_has_industry_stats("Retail & Apparel"): {has_industry}')

    # Try with just "Retail"
    has_industry_retail = gate._has_industry_stats(research, 'Retail')
    print(f'_has_industry_stats("Retail"): {has_industry_retail}')

    # Show sample of research
    print('\n=== SAMPLE RESEARCH DATA ===')
    if 'company_analysis' in research:
        ca = research['company_analysis']
        for key in list(ca.keys())[:2]:
            print(f'\ncompany_analysis.{key}:')
            print(json.dumps(ca[key], indent=2)[:500])

    if 'industry_intelligence' in research:
        ii = research['industry_intelligence']
        for key in list(ii.keys())[:2]:
            print(f'\nindustry_intelligence.{key}:')
            print(json.dumps(ii[key], indent=2)[:500])


if __name__ == '__main__':
    asyncio.run(debug_research())
