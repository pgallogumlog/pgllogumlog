"""
Fixtures for real API integration tests.

NO MOCKS - all fixtures return real API clients.
"""

import pytest
import os
import uuid
from config import get_container
from config.settings import Settings


@pytest.fixture(scope="session")
def real_settings():
    """Real settings from environment variables."""
    return Settings()


@pytest.fixture(scope="session")
def real_container():
    """Real dependency injection container."""
    return get_container()


@pytest.fixture
def real_ai_provider(real_container):
    """
    Real Claude API client (NO MOCKS).

    Each test gets a fresh client to avoid state pollution.
    """
    return real_container.ai_provider()


@pytest.fixture
def real_capturing_ai_provider(real_container):
    """
    Real Claude API with QA capture enabled.

    Use this for tests that validate QA pipeline.
    """
    run_id = f"test-{uuid.uuid4().hex[:8]}"

    return real_container.capturing_ai_provider(
        run_id=run_id,
        run_probabilistic=False,  # Faster without probabilistic checks
        probabilistic_sample_rate=0.0,
    )


@pytest.fixture
def real_email_client(real_container):
    """Real Gmail API client (NO MOCKS)."""
    return real_container.email_client()


@pytest.fixture
def real_sheets_client(real_container):
    """Real Google Sheets API client (NO MOCKS)."""
    return real_container.sheets_client()


@pytest.fixture
def test_spreadsheet_id(real_settings):
    """
    Test-only spreadsheet ID for QA logging.

    Uses separate spreadsheet from production to avoid pollution.
    Set TEST_SPREADSHEET_ID in .env for testing.
    """
    test_id = os.getenv("TEST_SPREADSHEET_ID")
    if not test_id:
        pytest.skip("TEST_SPREADSHEET_ID not set - skipping Sheets test")
    return test_id


@pytest.fixture
def test_email_recipient(real_settings):
    """
    Test email recipient for email delivery tests.

    Set TEST_EMAIL_RECIPIENT in .env for testing.
    """
    test_email = os.getenv("TEST_EMAIL_RECIPIENT")
    if not test_email:
        pytest.skip("TEST_EMAIL_RECIPIENT not set - skipping email test")
    return test_email


@pytest.fixture
def sample_test_inquiry():
    """
    Sample inquiry for workflow tests.

    Uses minimal, predictable prompt to reduce API costs.
    """
    from contexts.workflow.models import EmailInquiry

    return EmailInquiry(
        message_id="test-real-001",
        from_email="test@example.com",
        from_name="Test User",
        subject="Workflow Test",
        body="Analyze a small coffee shop and recommend 3 simple automation workflows.",
    )


@pytest.fixture
def budget_tier_inquiry():
    """Inquiry specifically for Budget tier testing (3 workflows)."""
    from contexts.workflow.models import EmailInquiry

    return EmailInquiry(
        message_id="test-budget-001",
        from_email="budget@example.com",
        from_name="Budget Client",
        subject="Budget Workflow",
        body="Recommend 3 quick automation ideas for a small retail store.",
    )


@pytest.fixture
def minimal_email_inquiry():
    """Minimal inquiry for cost-effective testing."""
    from contexts.workflow.models import EmailInquiry

    return EmailInquiry(
        message_id="test-minimal-001",
        from_email="minimal@example.com",
        from_name="Minimal Test",
        subject="Quick Test",
        body="Recommend the single most important workflow for email automation.",
    )
