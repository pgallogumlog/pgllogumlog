"""
Integration test for RAG Orchestrator.

Tests real web search functionality with Claude's native tools.
Run with: python test_rag_orchestrator.py
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from infrastructure.research.rag_orchestrator import RAGOrchestrator


async def test_basic_search():
    """Test basic web search functionality."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return False

    print("\n" + "=" * 60)
    print("TEST: Basic Web Search")
    print("=" * 60)

    rag = RAGOrchestrator(api_key=api_key)

    try:
        result = await rag.search_web(
            query="commercial real estate AI adoption statistics 2024 McKinsey",
            num_results=5,
        )

        print(f"\nQuery: {result.query}")
        print(f"Results found: {len(result.results)}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Summary length: {len(result.summary)} chars")

        if result.results:
            print("\nTop Results:")
            for i, r in enumerate(result.results[:3], 1):
                print(f"\n{i}. {r.title[:60]}...")
                print(f"   URL: {r.url}")
                print(f"   Credibility: {r.credibility}")
                print(f"   Snippet: {r.snippet[:100]}...")

            print("\n[PASS] Basic search working")
            return True
        else:
            print("\n[WARN] No results returned - web search may not be active")
            return False

    except Exception as e:
        print(f"\n[FAIL] Error: {str(e)}")
        return False


async def test_industry_research():
    """Test industry research functionality."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return False

    print("\n" + "=" * 60)
    print("TEST: Industry Research")
    print("=" * 60)

    rag = RAGOrchestrator(api_key=api_key)

    try:
        result = await rag.research_industry(
            industry="Commercial Real Estate",
            pain_point="property management efficiency",
        )

        print(f"\nIndustry: {result.industry}")
        print(f"Total citations: {len(result.all_citations)}")
        print(f"Statistics found: {len(result.statistics)}")
        print(f"Trends found: {len(result.trends)}")
        print(f"Competitors found: {len(result.competitor_initiatives)}")
        print(f"Adoption data: {len(result.adoption_data)}")

        if result.all_citations:
            print("\nSample Citations:")
            for citation in result.all_citations[:3]:
                print(f"  - {citation.get('title', 'N/A')[:50]}...")
                print(f"    URL: {citation.get('url', 'N/A')}")
                print(f"    Credibility: {citation.get('credibility', 'N/A')}")

            print("\n[PASS] Industry research working")
            return True
        else:
            print("\n[WARN] No citations returned")
            return False

    except Exception as e:
        print(f"\n[FAIL] Error: {str(e)}")
        return False


async def test_company_research():
    """Test company research functionality."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return False

    print("\n" + "=" * 60)
    print("TEST: Company Research")
    print("=" * 60)

    rag = RAGOrchestrator(api_key=api_key)

    try:
        result = await rag.research_company(
            company_name="Cushman & Wakefield",
            website="https://www.cushmanwakefield.com",
            industry="Commercial Real Estate",
        )

        print(f"\nCompany: {result.company_name}")
        print(f"Total citations: {len(result.all_citations)}")
        print(f"Tech initiatives: {len(result.technology_initiatives)}")
        print(f"News mentions: {len(result.news_mentions)}")
        print(f"AI initiatives: {len(result.ai_initiatives)}")

        if result.all_citations:
            print("\nSample Citations:")
            for citation in result.all_citations[:3]:
                print(f"  - {citation.get('title', 'N/A')[:50]}...")
                print(f"    URL: {citation.get('url', 'N/A')}")

            print("\n[PASS] Company research working")
            return True
        else:
            print("\n[WARN] No citations returned")
            return False

    except Exception as e:
        print(f"\n[FAIL] Error: {str(e)}")
        return False


async def test_case_study_research():
    """Test case study research functionality."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return False

    print("\n" + "=" * 60)
    print("TEST: Case Study Research")
    print("=" * 60)

    rag = RAGOrchestrator(api_key=api_key)

    try:
        result = await rag.research_case_studies(
            industry="Commercial Real Estate",
            pain_point="property management automation",
            company_size="mid-market",
        )

        print(f"\nIndustry: {result.industry}")
        print(f"Pain Point: {result.pain_point}")
        print(f"Total citations: {len(result.all_citations)}")
        print(f"Case studies: {len(result.case_studies)}")
        print(f"ROI data: {len(result.roi_data)}")
        print(f"Implementation guides: {len(result.implementation_guides)}")

        if result.all_citations:
            print("\nSample Citations:")
            for citation in result.all_citations[:3]:
                print(f"  - {citation.get('title', 'N/A')[:50]}...")
                print(f"    URL: {citation.get('url', 'N/A')}")

            print("\n[PASS] Case study research working")
            return True
        else:
            print("\n[WARN] No citations returned")
            return False

    except Exception as e:
        print(f"\n[FAIL] Error: {str(e)}")
        return False


async def main():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("RAG ORCHESTRATOR INTEGRATION TESTS")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set your API key to run tests.")
        return

    results = []

    # Run tests
    results.append(("Basic Search", await test_basic_search()))
    results.append(("Industry Research", await test_industry_research()))
    results.append(("Company Research", await test_company_research()))
    results.append(("Case Study Research", await test_case_study_research()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nRAG Orchestrator is ready for production!")
    else:
        print("\nSome tests failed - check web search beta availability")


if __name__ == "__main__":
    asyncio.run(main())
