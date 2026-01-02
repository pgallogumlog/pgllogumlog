"""
Compass Test Cases Dataset.

15 enterprise test cases with varied AI readiness profiles for testing
the AI Readiness Compass system.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CompassTestCase:
    """Test case for AI Readiness Compass."""

    # Company Info
    company_name: str
    website: str
    industry: str
    company_size: str

    # Self-Assessment (1-5 scale)
    data_maturity: int
    automation_experience: int
    change_readiness: int

    # Challenge
    pain_point: str
    description: str

    # Contact
    email: str = "test@example.com"
    contact_name: str = "Test User"

    # Metadata
    category: str = "General"
    expected_score_range: Optional[tuple[int, int]] = None  # (min, max) expected score


# Varied test cases across industries and readiness levels
COMPASS_TEST_CASES: list[CompassTestCase] = [
    # --- LOW READINESS (scores 1-2) ---
    CompassTestCase(
        company_name="Traditional Law Firm LLP",
        website="https://example-lawfirm.com",
        industry="Professional Services",
        company_size="51-200",
        data_maturity=1,
        automation_experience=1,
        change_readiness=2,
        pain_point="Manual Data Entry",
        description="We still use paper files and fax machines. Staff manually enters client data into multiple systems. No centralized database.",
        category="Low Readiness",
        expected_score_range=(20, 40),
    ),
    CompassTestCase(
        company_name="Family Medical Practice",
        website="https://example-medical.com",
        industry="Healthcare",
        company_size="1-50",
        data_maturity=2,
        automation_experience=1,
        change_readiness=1,
        pain_point="Email Overload",
        description="Doctors spend 3+ hours daily on emails. No triage system. Patient inquiries mixed with vendor spam.",
        category="Low Readiness",
        expected_score_range=(15, 35),
    ),
    CompassTestCase(
        company_name="Local Credit Union",
        website="https://example-creditunion.com",
        industry="Financial Services",
        company_size="51-200",
        data_maturity=2,
        automation_experience=2,
        change_readiness=1,
        pain_point="Slow Approvals",
        description="Loan approvals take 2-3 weeks due to manual document verification. Members complain about delays.",
        category="Low Readiness",
        expected_score_range=(25, 45),
    ),

    # --- MEDIUM READINESS (scores 3) ---
    CompassTestCase(
        company_name="Regional Insurance Agency",
        website="https://example-insurance.com",
        industry="Financial Services",
        company_size="201-500",
        data_maturity=3,
        automation_experience=3,
        change_readiness=3,
        pain_point="Customer Support",
        description="500+ support tickets daily. Basic ticketing system but no AI. First response time is 24+ hours.",
        category="Medium Readiness",
        expected_score_range=(45, 65),
    ),
    CompassTestCase(
        company_name="Mid-Size Manufacturing Co",
        website="https://example-manufacturing.com",
        industry="Manufacturing",
        company_size="501-1000",
        data_maturity=3,
        automation_experience=4,
        change_readiness=2,
        pain_point="Report Generation",
        description="Quality reports take 2 days to compile from multiple systems. Management wants real-time dashboards.",
        category="Medium Readiness",
        expected_score_range=(40, 60),
    ),
    CompassTestCase(
        company_name="E-commerce Fashion Brand",
        website="https://example-fashion.com",
        industry="Retail",
        company_size="51-200",
        data_maturity=4,
        automation_experience=3,
        change_readiness=3,
        pain_point="Lead Management",
        description="We have good customer data but can't personalize at scale. Marketing team overwhelmed by lead scoring.",
        category="Medium Readiness",
        expected_score_range=(50, 70),
    ),
    CompassTestCase(
        company_name="Commercial Real Estate Firm",
        website="https://example-realestate.com",
        industry="Real Estate",
        company_size="201-500",
        data_maturity=3,
        automation_experience=2,
        change_readiness=4,
        pain_point="Knowledge Management",
        description="Senior brokers retiring with decades of market knowledge. No system to capture or transfer expertise.",
        category="Medium Readiness",
        expected_score_range=(45, 65),
    ),

    # --- HIGH READINESS (scores 4-5) ---
    CompassTestCase(
        company_name="Tech Startup Inc",
        website="https://example-techstartup.com",
        industry="Technology",
        company_size="51-200",
        data_maturity=5,
        automation_experience=4,
        change_readiness=5,
        pain_point="Customer Support",
        description="We use modern stack (cloud, APIs). Want AI to handle tier-1 support. Already have chatbot but it's rule-based.",
        category="High Readiness",
        expected_score_range=(70, 90),
    ),
    CompassTestCase(
        company_name="Digital Marketing Agency",
        website="https://example-marketing.com",
        industry="Professional Services",
        company_size="51-200",
        data_maturity=4,
        automation_experience=5,
        change_readiness=5,
        pain_point="Report Generation",
        description="Using Zapier and n8n already. Want AI to generate client performance reports automatically.",
        category="High Readiness",
        expected_score_range=(75, 95),
    ),
    CompassTestCase(
        company_name="FinTech Platform",
        website="https://example-fintech.com",
        industry="Financial Services",
        company_size="201-500",
        data_maturity=5,
        automation_experience=5,
        change_readiness=4,
        pain_point="Compliance",
        description="Need AI for real-time transaction monitoring. Already have ML models for fraud but need better explainability.",
        category="High Readiness",
        expected_score_range=(70, 90),
    ),

    # --- VARIED / EDGE CASES ---
    CompassTestCase(
        company_name="University Research Lab",
        website="https://example-university.edu",
        industry="Education",
        company_size="1-50",
        data_maturity=5,  # Great data
        automation_experience=2,  # Low automation
        change_readiness=4,
        pain_point="Knowledge Management",
        description="Massive datasets but manual analysis. Researchers want AI for literature review and hypothesis generation.",
        category="Mixed Readiness",
        expected_score_range=(50, 70),
    ),
    CompassTestCase(
        company_name="Legacy Retailer Corp",
        website="https://example-retailer.com",
        industry="Retail",
        company_size="5000+",
        data_maturity=2,  # Old systems
        automation_experience=4,  # Some automation
        change_readiness=2,  # Resistant
        pain_point="Invoice Processing",
        description="10,000+ invoices monthly. AP team overwhelmed. Have ERP but it's from 2005.",
        category="Mixed Readiness",
        expected_score_range=(35, 55),
    ),
    CompassTestCase(
        company_name="Healthcare SaaS Startup",
        website="https://example-healthtech.com",
        industry="Healthcare",
        company_size="51-200",
        data_maturity=4,
        automation_experience=4,
        change_readiness=5,
        pain_point="Employee Onboarding",
        description="Fast-growing team. Onboarding takes 3 weeks. Need AI to personalize training paths.",
        category="High Readiness",
        expected_score_range=(65, 85),
    ),
    CompassTestCase(
        company_name="Global Consulting Firm",
        website="https://example-consulting.com",
        industry="Professional Services",
        company_size="1001-5000",
        data_maturity=3,
        automation_experience=3,
        change_readiness=3,
        pain_point="Other",
        description="Need AI to match consultants to projects based on skills, availability, and client preferences.",
        category="Medium Readiness",
        expected_score_range=(45, 65),
    ),
    CompassTestCase(
        company_name="Non-Profit Foundation",
        website="https://example-nonprofit.org",
        industry="Nonprofit",
        company_size="51-200",
        data_maturity=2,
        automation_experience=2,
        change_readiness=5,  # Very willing
        pain_point="Manual Data Entry",
        description="Donor data in spreadsheets. Want to automate thank-you emails and grant applications.",
        category="Low-Medium Readiness",
        expected_score_range=(35, 55),
    ),
]


def get_compass_test_cases(count: int = 15) -> list[CompassTestCase]:
    """
    Get compass test cases, limited by count.

    Args:
        count: Number of test cases to return (1-15)

    Returns:
        List of CompassTestCase objects
    """
    count = max(1, min(count, len(COMPASS_TEST_CASES)))
    return COMPASS_TEST_CASES[:count]


def get_compass_test_cases_by_category(category: str) -> list[CompassTestCase]:
    """
    Get compass test cases filtered by category.

    Args:
        category: Category name (e.g., "Low Readiness", "High Readiness")

    Returns:
        List of CompassTestCase objects in that category
    """
    return [tc for tc in COMPASS_TEST_CASES if tc.category == category]
