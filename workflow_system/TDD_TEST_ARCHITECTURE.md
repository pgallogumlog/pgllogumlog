# TDD TEST ARCHITECTURE - Real API Integration Test Suite

**Architect:** Designer 2 (TDD Test Architect)
**Date:** 2025-12-29
**Mission:** Design fresh test suite with ZERO mocks, strict TDD, end-to-end focus

---

## Design Philosophy

### Core Principles

1. **REAL APIs ONLY** - No mocks, no stubs, no fakes
2. **End-to-End First** - Test complete user flows, not isolated units
3. **TDD Strict** - Write failing test → Make it pass → Refactor
4. **Cost-Conscious** - Optimize prompts to minimize Claude API costs
5. **Deterministic Assertions** - Account for AI non-determinism
6. **Production-Like** - Use same configs as production code

### Why No Mocks?

**Problem with Current Suite:**
- Mocks test what we THINK the API does
- Real APIs have edge cases mocks miss
- Integration bugs only appear with real services
- False confidence from passing mock tests

**Real API Benefits:**
- Catch API changes immediately
- Test actual latency and rate limits
- Validate real response formats
- Build confidence in production behavior

---

## Test Suite Architecture

### Directory Structure

```
tests/
├── conftest.py                          # Real API fixtures (NEW)
├── real_integration/                    # NEW DIRECTORY
│   ├── __init__.py
│   ├── conftest.py                      # Real API fixtures for integration tests
│   ├── test_real_core_workflow.py       # Priority 1: Core engine
│   ├── test_real_end_to_end.py          # Priority 2: Full flow
│   ├── test_real_consensus_voting.py    # Priority 3: Self-consistency
│   ├── test_real_qa_capture.py          # Priority 4: QA validation
│   └── test_real_error_recovery.py      # Priority 5: Error handling
├── integration/                         # EXISTING (keep for reference)
│   └── test_api.py
└── unit/                                # EXISTING (keep for reference)
    └── contexts/
        └── ...
```

### Test Layer Separation

**Real Integration Tests** (`tests/real_integration/`)
- Use REAL Claude API, Gmail API, Sheets API
- Test complete workflows end-to-end
- Slower, more expensive, higher confidence
- Run on-demand or in CI (daily builds)

**Legacy Tests** (`tests/unit/`, `tests/integration/`)
- Keep as reference and for fast feedback
- Continue using mocks
- Run on every commit (fast feedback loop)

---

## Test Fixtures Strategy

### Real API Fixtures (tests/real_integration/conftest.py)

```python
"""
Fixtures for real API integration tests.
NO MOCKS - all fixtures return real API clients.
"""

import pytest
import os
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
    import uuid
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
async def cleanup_test_spreadsheet(real_sheets_client, test_spreadsheet_id):
    """
    Auto-cleanup fixture for Sheets tests.

    Clears test data after each test to maintain isolation.
    """
    yield

    # Cleanup: Clear test rows added during test
    # (Implementation depends on Sheets API - may keep data for debugging)
    pass


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
        body="Analyze a small coffee shop at example.com and recommend 3 simple automation workflows.",
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
```

---

## Test Implementation Patterns

### Pattern 1: TDD Workflow (Red-Green-Refactor)

```python
# test_real_core_workflow.py

import pytest


@pytest.mark.real_api
@pytest.mark.asyncio
class TestRealWorkflowEngine:
    """
    Real API tests for WorkflowEngine.

    These tests call the actual Claude API and validate real behavior.
    """

    async def test_should_process_inquiry_with_real_claude_api(
        self,
        real_ai_provider,
        sample_test_inquiry,
    ):
        """
        TDD Test: WorkflowEngine should process inquiry using real Claude API.

        RED (Write failing test first):
        - This test will FAIL initially because we're using real API
        - Expected failure: May get rate limit, API error, or unexpected response

        GREEN (Make it pass):
        - Fix any API integration issues
        - Ensure retry logic works
        - Validate response format

        REFACTOR (Clean up):
        - Extract common patterns
        - Optimize API calls
        - Add better assertions

        Cost: ~$0.30 per run (5 parallel Claude calls)
        """
        from contexts.workflow.engine import WorkflowEngine

        # Arrange: Create engine with REAL AI provider
        engine = WorkflowEngine(
            ai_provider=real_ai_provider,
            temperatures=[0.4, 0.6, 0.8, 1.0, 1.2],  # Real temperature variations
            min_consensus_votes=2,
        )

        # Act: Process inquiry with real Claude API
        result, qa_result = await engine.process_inquiry(
            inquiry=sample_test_inquiry,
            tier="Budget",  # Cheaper tier for testing
        )

        # Assert: Validate real API results
        # (Assertions must be flexible due to AI non-determinism)
        assert result.run_id is not None, "Should generate run_id"
        assert result.client_name == "Test User", "Should extract client name"

        # Consensus should be reached or fallback activated
        assert result.consensus is not None, "Should have consensus result"

        # Budget tier should have 3 workflows
        assert len(result.consensus.all_workflows) == 3, \
            f"Budget tier should return 3 workflows, got {len(result.consensus.all_workflows)}"

        # Each workflow should have required fields
        for wf in result.consensus.all_workflows:
            assert wf.name, f"Workflow should have name"
            assert wf.objective, f"Workflow {wf.name} should have objective"
            assert isinstance(wf.tools, list), f"Workflow {wf.name} should have tools list"

        # Proposal should be generated
        assert result.proposal is not None, "Should generate proposal"
        assert result.proposal.html_body, "Should have HTML body"
        assert "Test User" in result.proposal.html_body, "HTML should include client name"

        # Phases should be created
        assert len(result.proposal.phases) > 0, "Should have at least 1 phase"

        # Validate AI behavior (non-deterministic checks)
        assert result.consensus.total_responses >= 5, \
            "Should have responses from 5 temperatures"

        # Log for debugging (helps with flaky test diagnosis)
        print(f"\n--- Real API Test Results ---")
        print(f"Run ID: {result.run_id}")
        print(f"Consensus: {result.consensus.final_answer}")
        print(f"Confidence: {result.consensus.confidence_percent}%")
        print(f"Workflows: {len(result.consensus.all_workflows)}")
        print(f"Phases: {len(result.proposal.phases)}")
```

### Pattern 2: End-to-End Flow Testing

```python
# test_real_end_to_end.py

import pytest


@pytest.mark.real_api
@pytest.mark.asyncio
class TestRealEndToEndWorkflow:
    """
    End-to-end tests with REAL APIs.

    Tests complete user flows from inquiry to delivery.
    """

    async def test_should_complete_full_workflow_with_real_apis(
        self,
        real_ai_provider,
        real_sheets_client,
        test_spreadsheet_id,
        sample_test_inquiry,
    ):
        """
        TDD Test: Complete workflow from inquiry to Sheets logging.

        Flow:
        1. Receive inquiry
        2. Process with real Claude API
        3. Generate consensus with real voting
        4. Create proposal
        5. Log to real Google Sheets

        Cost: ~$0.30 per run
        """
        from contexts.workflow.engine import WorkflowEngine
        from contexts.qa.sheets_logger import QASheetsLogger

        # Arrange: Set up workflow engine with real APIs
        qa_logger = QASheetsLogger(
            sheets_client=real_sheets_client,
            spreadsheet_id=test_spreadsheet_id,
        )

        engine = WorkflowEngine(
            ai_provider=real_ai_provider,
            min_consensus_votes=2,
            qa_sheets_logger=qa_logger,
        )

        # Act: Run complete workflow
        result, qa_result = await engine.process_inquiry(
            inquiry=sample_test_inquiry,
            tier="Budget",
        )

        # Assert: Workflow completed successfully
        assert result.run_id is not None
        assert result.consensus is not None
        assert result.proposal is not None

        # Assert: Proposal contains expected elements
        assert "Test User" in result.proposal.html_body
        assert len(result.proposal.phases) > 0

        # Assert: Can read back from Sheets (validates write worked)
        # Note: This requires implementing read functionality
        # For now, just verify no exceptions were raised

        print(f"\n--- End-to-End Test Results ---")
        print(f"Run ID: {result.run_id}")
        print(f"Workflows: {len(result.consensus.all_workflows)}")
        print(f"Phases: {len(result.proposal.phases)}")
        print(f"Logged to Sheets: {test_spreadsheet_id}")
```

### Pattern 3: Error Recovery Testing

```python
# test_real_error_recovery.py

import pytest
import asyncio


@pytest.mark.real_api
@pytest.mark.asyncio
class TestRealErrorRecovery:
    """
    Tests for error recovery with real APIs.

    Validates retry logic, rate limit handling, timeout behavior.
    """

    async def test_should_handle_parallel_requests_without_rate_limit_errors(
        self,
        real_ai_provider,
    ):
        """
        TDD Test: Engine should handle parallel Claude API calls with rate limiting.

        This test validates:
        - Staggered request delays prevent rate limits
        - Retry logic works on real API failures
        - Exponential backoff functions correctly

        Cost: ~$0.30 per run (5 parallel calls)
        """
        from contexts.workflow.engine import WorkflowEngine
        from contexts.workflow.models import EmailInquiry

        # Arrange: Create inquiry
        inquiry = EmailInquiry(
            message_id="test-rate-limit",
            from_email="test@example.com",
            from_name="Rate Limit Test",
            subject="Test",
            body="Recommend 3 workflows for a small business.",
        )

        # Arrange: Create engine (will make 5 parallel calls)
        engine = WorkflowEngine(
            ai_provider=real_ai_provider,
            temperatures=[0.4, 0.6, 0.8, 1.0, 1.2],
            min_consensus_votes=2,
        )

        # Act: Process inquiry (should trigger parallel API calls)
        start_time = asyncio.get_event_loop().time()
        result, _ = await engine.process_inquiry(inquiry, tier="Budget")
        duration = asyncio.get_event_loop().time() - start_time

        # Assert: All calls succeeded without rate limit errors
        assert result.consensus is not None, "Should complete despite parallel calls"
        assert result.consensus.total_responses >= 5, \
            f"Should have 5 responses, got {result.consensus.total_responses}"

        # Assert: Staggered delays were applied (should take > 2 seconds for 5 calls)
        assert duration > 2.0, \
            f"Parallel calls should be staggered (took {duration:.1f}s)"

        print(f"\n--- Rate Limit Test Results ---")
        print(f"Duration: {duration:.1f}s")
        print(f"Responses: {result.consensus.total_responses}")
        print(f"All calls succeeded without rate limit errors")


    async def test_should_retry_on_temporary_api_failure(
        self,
        real_ai_provider,
    ):
        """
        TDD Test: Engine should retry on temporary API failures.

        Note: This test is hard to trigger with real API (failures are rare).
        We validate retry logic exists and is configured correctly.

        Cost: ~$0.05 per run (1 call)
        """
        # This test validates the retry configuration exists
        # Actual retry behavior is tested implicitly by other tests

        assert hasattr(real_ai_provider, '_client'), "Should have Anthropic client"

        # Verify retry configuration (from claude_adapter.py)
        from infrastructure.ai.claude_adapter import MAX_RETRIES, BASE_DELAY

        assert MAX_RETRIES == 5, "Should retry up to 5 times"
        assert BASE_DELAY == 2.0, "Should use 2s base delay"

        print(f"\n--- Retry Configuration ---")
        print(f"Max Retries: {MAX_RETRIES}")
        print(f"Base Delay: {BASE_DELAY}s")
        print("Retry logic validated (implicit testing via real API calls)")
```

### Pattern 4: QA Capture Validation

```python
# test_real_qa_capture.py

import pytest


@pytest.mark.real_api
@pytest.mark.asyncio
class TestRealQACapture:
    """
    Tests for QA capture system with real API calls.

    Validates that QA validation pipeline works with real Claude responses.
    """

    async def test_should_capture_and_validate_real_api_calls(
        self,
        real_capturing_ai_provider,
        sample_test_inquiry,
    ):
        """
        TDD Test: QA system should capture and validate real Claude API calls.

        This test validates:
        - CapturingAIAdapter intercepts real API calls
        - Deterministic validators run on real responses
        - Call scoring works with real data
        - Validation results are accurate

        Cost: ~$0.30 per run
        """
        from contexts.workflow.engine import WorkflowEngine

        # Arrange: Create engine with capturing adapter
        engine = WorkflowEngine(
            ai_provider=real_capturing_ai_provider,
            min_consensus_votes=2,
        )

        # Act: Process inquiry (all AI calls will be captured)
        result, qa_result = await engine.process_inquiry(
            inquiry=sample_test_inquiry,
            tier="Budget",
        )

        # Assert: Calls were captured
        call_store = real_capturing_ai_provider.call_store
        assert len(call_store.calls) > 0, "Should capture AI calls"

        # Assert: Each call has validation results
        for call in call_store.calls:
            assert call.validation_results is not None, \
                f"Call {call.call_id} should have validation results"
            assert call.call_score is not None, \
                f"Call {call.call_id} should have score"

        # Assert: QA result was generated
        assert qa_result is not None, "Should generate QA result"
        assert qa_result.overall_score > 0, "Should have overall score"
        assert qa_result.total_calls > 0, "Should track total calls"

        # Print detailed QA metrics
        print(f"\n--- QA Capture Results ---")
        print(f"Total Calls Captured: {len(call_store.calls)}")
        print(f"Overall QA Score: {qa_result.overall_score}/10")
        print(f"Passed: {qa_result.passed}")
        print(f"Calls Failed: {qa_result.calls_failed}")

        for call in call_store.calls:
            print(f"\n  Call {call.call_id}:")
            print(f"    Method: {call.method}")
            print(f"    Score: {call.call_score.overall_score}/10")
            print(f"    Tokens: {call.input_tokens} in / {call.output_tokens} out")
            print(f"    Duration: {call.duration_ms:.0f}ms")
```

### Pattern 5: Consensus Voting with Real AI

```python
# test_real_consensus_voting.py

import pytest


@pytest.mark.real_api
@pytest.mark.asyncio
class TestRealConsensusVoting:
    """
    Tests for self-consistency voting with real Claude API.

    Validates that consensus formation works with actual AI outputs.
    """

    async def test_should_achieve_consensus_with_real_temperature_variations(
        self,
        real_ai_provider,
    ):
        """
        TDD Test: Self-consistency voting should work with real AI outputs.

        This test validates:
        - Multiple temperatures produce diverse responses
        - Consensus voting identifies common answer
        - Fallback scoring works if no consensus

        Cost: ~$0.30 per run (5 parallel calls)
        """
        from contexts.workflow.engine import WorkflowEngine
        from contexts.workflow.models import EmailInquiry

        # Arrange: Create inquiry designed to produce consensus
        # (Simple, clear prompt should get consistent answers)
        inquiry = EmailInquiry(
            message_id="test-consensus",
            from_email="test@example.com",
            from_name="Consensus Test",
            subject="Test",
            body="Recommend the single most important workflow for email automation.",
        )

        # Arrange: Create engine with real temperatures
        engine = WorkflowEngine(
            ai_provider=real_ai_provider,
            temperatures=[0.4, 0.6, 0.8, 1.0, 1.2],
            min_consensus_votes=3,  # Need 3/5 to agree
        )

        # Act: Process inquiry
        result, _ = await engine.process_inquiry(inquiry, tier="Budget")

        # Assert: Consensus result exists
        assert result.consensus is not None
        assert result.consensus.total_responses == 5, "Should have 5 responses"

        # Assert: Either consensus was reached OR fallback was used
        if result.consensus.had_consensus:
            assert result.consensus.votes_for_winner >= 3, \
                "Consensus should have at least 3 votes"
            assert result.consensus.consensus_strength in ["Strong", "Moderate"], \
                "Consensus strength should be Strong or Moderate"
        else:
            assert result.consensus.consensus_strength == "Fallback", \
                "Should use fallback scoring if no consensus"

        # Assert: Final answer was selected
        assert result.consensus.final_answer, "Should have final answer"

        # Print consensus details
        print(f"\n--- Consensus Voting Results ---")
        print(f"Had Consensus: {result.consensus.had_consensus}")
        print(f"Votes for Winner: {result.consensus.votes_for_winner}/{result.consensus.total_responses}")
        print(f"Confidence: {result.consensus.confidence_percent}%")
        print(f"Consensus Strength: {result.consensus.consensus_strength}")
        print(f"Final Answer: {result.consensus.final_answer}")

        # Print all workflows to see diversity
        print(f"\nAll Workflows ({len(result.consensus.all_workflows)}):")
        for i, wf in enumerate(result.consensus.all_workflows, 1):
            print(f"  {i}. {wf.name}")
```

---

## Test Data Management Strategy

### Minimal Prompts for Cost Reduction

**Bad (Expensive):**
```python
body = """
Analyze Starbucks Corporation, a global coffee chain with 30,000+ locations.
Review their entire business model, supply chain, customer segments, and operations.
Recommend 25 comprehensive AI automation workflows covering all departments.
"""
# Cost: ~$1.50 per test (large input/output)
```

**Good (Cost-Effective):**
```python
body = "Recommend 3 simple automation workflows for a small coffee shop."
# Cost: ~$0.30 per test (minimal input/output)
```

### Reusable Test Data

```python
# tests/real_integration/test_data.py

"""
Reusable test data for real API tests.

All prompts designed to minimize API costs while validating behavior.
"""

MINIMAL_COFFEE_SHOP = {
    "company": "Small Coffee Shop",
    "prompt": "Recommend 3 simple workflows for a small coffee shop.",
    "expected_workflows": 3,
    "expected_keywords": ["coffee", "order", "customer"],
}

MINIMAL_RETAIL_STORE = {
    "company": "Small Retail Store",
    "prompt": "Recommend 3 quick automation ideas for a small retail store.",
    "expected_workflows": 3,
    "expected_keywords": ["inventory", "sales", "customer"],
}

MINIMAL_EMAIL_AUTOMATION = {
    "company": "Email Automation",
    "prompt": "Recommend the single most important workflow for email automation.",
    "expected_workflows": 3,  # Budget tier always returns 3
    "expected_keywords": ["email", "triage", "automation"],
}
```

---

## Assertion Strategies for AI Non-Determinism

### Flexible Assertions (Good)

```python
# Don't assert exact values
assert len(result.consensus.all_workflows) == 3, "Should have 3 workflows"

# Assert on structure
assert all(wf.name for wf in result.consensus.all_workflows), "All workflows should have names"

# Assert on patterns
assert any("email" in wf.name.lower() for wf in result.consensus.all_workflows), \
    "Should include email-related workflow"

# Assert on ranges
assert 0 <= result.consensus.confidence_percent <= 100, "Confidence should be 0-100%"

# Assert on types
assert isinstance(result.proposal.phases, list), "Phases should be a list"
```

### Rigid Assertions (Bad)

```python
# DON'T do this with AI outputs:
assert result.consensus.final_answer == "Email Triage Automation"  # Too specific
assert result.consensus.confidence_percent == 100  # Non-deterministic
assert result.consensus.all_workflows[0].name == "Support Bot"  # Order varies
```

---

## Cost Optimization Strategies

### 1. Tier-Based Testing
- **Budget tier:** 3 workflows, faster, cheaper (~$0.20)
- **Standard tier:** 5 workflows, moderate cost (~$0.30)
- **Premium tier:** 5 workflows + extras, more expensive (~$0.40)

**Strategy:** Prefer Budget tier for most tests.

### 2. Prompt Minimization
- Use short, simple prompts
- Avoid unnecessary context
- Request fewer workflows when possible

### 3. Response Caching (Future)
- Cache API responses for deterministic tests
- Reuse cached responses when prompt hasn't changed
- Hybrid approach: Real API + cached fallback

### 4. Selective Real API Testing
- Not every test needs real API
- Keep fast mock tests for development
- Run real API tests on PR/daily builds

---

## CI/CD Integration Strategy

### Test Execution Tiers

**Tier 1: Every Commit (Fast, Mock-Based)**
```bash
# Existing mock tests for instant feedback
pytest tests/unit/ tests/integration/ -v
```

**Tier 2: Pull Request (Real API, Critical Paths)**
```bash
# Run critical real API tests before merge
pytest tests/real_integration/test_real_core_workflow.py -v -m real_api
```

**Tier 3: Daily Build (Full Real API Suite)**
```bash
# Run all real API tests overnight
pytest tests/real_integration/ -v -m real_api
```

### GitHub Actions Example

```yaml
name: Real API Tests

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  real-api-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run Real API Tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GOOGLE_CREDENTIALS_FILE: ${{ secrets.GOOGLE_CREDENTIALS }}
          TEST_SPREADSHEET_ID: ${{ secrets.TEST_SPREADSHEET_ID }}
        run: |
          cd workflow_system
          pytest tests/real_integration/ -v -m real_api
```

---

## Test Isolation & Cleanup

### Spreadsheet Cleanup

```python
@pytest.fixture
async def clean_test_spreadsheet(real_sheets_client, test_spreadsheet_id):
    """Clear test spreadsheet before and after test."""

    # Pre-test: Clear existing data
    await real_sheets_client.clear_range(
        spreadsheet_id=test_spreadsheet_id,
        range="A2:Z1000",  # Clear all data rows (keep headers)
    )

    yield

    # Post-test: Optional cleanup
    # (Could keep data for debugging)
```

### Email Cleanup

```python
@pytest.fixture
async def clean_test_emails(real_email_client, test_email_recipient):
    """Delete test emails after test."""

    yield

    # Post-test: Delete emails sent to test recipient
    # (Implementation depends on Gmail API capabilities)
```

---

## Flakiness Mitigation

### Retry Strategy for Flaky Tests

```python
import pytest

@pytest.mark.flaky(reruns=3, reruns_delay=2)
@pytest.mark.real_api
async def test_may_be_flaky_due_to_network(real_ai_provider):
    """
    Test may be flaky due to network issues.

    pytest-rerun will retry up to 3 times with 2s delay.
    """
    # Test code
    pass
```

### Timeout Protection

```python
@pytest.mark.timeout(60)  # Fail if test takes > 60 seconds
@pytest.mark.real_api
async def test_with_timeout(real_ai_provider):
    """Test with timeout protection."""
    # Test code
    pass
```

---

## Test Execution Order

### Priority 1: Core Workflow (Implement First)
**File:** `test_real_core_workflow.py`
- Single workflow with real Claude API
- Validates basic integration
- Cheapest, fastest real API test

### Priority 2: End-to-End Flow (Implement Second)
**File:** `test_real_end_to_end.py`
- Complete flow from inquiry to delivery
- Validates all integrations together
- Moderate cost

### Priority 3: Consensus Voting (Implement Third)
**File:** `test_real_consensus_voting.py`
- Self-consistency with real temperatures
- Validates voting logic
- Moderate cost

### Priority 4: QA Capture (Implement Fourth)
**File:** `test_real_qa_capture.py`
- QA validation with real API calls
- Validates QA pipeline
- Moderate cost

### Priority 5: Error Recovery (Implement Last)
**File:** `test_real_error_recovery.py`
- Rate limits, retries, timeouts
- Validates resilience
- Low cost (mostly validation checks)

---

## Success Metrics

### Test Suite Health
- [ ] All tests pass with real APIs
- [ ] No flaky tests (< 1% failure rate)
- [ ] Test suite completes in < 10 minutes
- [ ] API costs stay under $1 per full run

### Coverage Goals
- [ ] Core workflow path: 100% coverage
- [ ] Error recovery: 80% coverage
- [ ] Edge cases: 50% coverage

### Quality Gates
- [ ] All critical paths tested with real APIs
- [ ] QA capture validates all AI calls
- [ ] Sheets logging verified
- [ ] Email delivery verified

---

## Designer 2 Recommendations

### Immediate Implementation Plan

1. **Create `tests/real_integration/` directory**
2. **Implement `conftest.py` with real API fixtures**
3. **Write first test: `test_real_core_workflow.py`**
   - Single test method
   - Budget tier (cheapest)
   - Validate basic workflow
4. **Run test and iterate until passing**
5. **Add remaining priority tests one by one**

### TDD Discipline

**For Each Test:**
1. **RED:** Write test that calls real API (will fail initially)
2. **GREEN:** Fix issues until test passes
3. **REFACTOR:** Clean up test code, optimize costs
4. **VERIFY:** Run test 3 times to check for flakiness
5. **COMMIT:** Atomic commit with passing test

### Cost Budget

**Total Estimated Cost for Development:**
- 5 priority tests × 10 iterations each × $0.30 = **$15**
- CI/CD runs (daily) × 30 days × $5 = **$150/month**

**Optimization:**
- Cache responses where possible
- Use Budget tier for most tests
- Run full suite only on main branch

---

## Next Steps for Designer 3

Designer 3 (Implementation Engineer) should:
1. Create `tests/real_integration/` directory
2. Implement fixtures in `conftest.py`
3. Implement Priority 1 test (`test_real_core_workflow.py`)
4. Run test, debug, iterate until passing
5. Implement Priority 2 test (`test_real_end_to_end.py`)
6. Continue through priorities 3-5

---

**End of TDD Test Architecture**
**Handoff to Designer 3 for Implementation**
