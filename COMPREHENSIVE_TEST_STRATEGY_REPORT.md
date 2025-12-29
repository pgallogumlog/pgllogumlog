# Comprehensive Testing Strategy Report
## Automated Testing Plan for Workflow System

**Date:** 2025-12-28
**Orchestrator:** Lead Testing Architect
**Designers:** Integration-First Architect, Layered Testing Strategist, Behavior-Driven Quality Engineer

---

## Executive Summary

After analyzing three distinct testing approaches, we recommend a **Hybrid Strategy** that combines the best elements of each:

- **Integration-first foundation** for validating real API behavior
- **Layered execution strategy** for fast feedback loops
- **BDD scenarios** for critical business workflows

**Expected Outcomes:**
- Test validity: **5/10 → 9/10**
- Test count: **86 → ~200 tests**
- Real API coverage: **0% → 90%**
- API cost: **$0 → ~$20-40/month** (on-demand, pre-production)
- Feedback time: **2+ min → <30s local, <2min PR**

---

## Phase 1: Individual Designer Plans Summary

### Designer 1: Integration-First Architect

**Philosophy:** "If it's not tested with real services, it's not truly tested."

**Key Strengths:**
- Prioritizes real API validation (60% integration tests)
- Comprehensive error scenario coverage
- Catches real bugs that mocks miss
- High confidence in production readiness

**Test Distribution:**
- 60% Integration Tests (~120 tests) - Real APIs
- 20% E2E Tests (~40 tests) - Full workflows
- 20% Unit Tests (~40 tests) - Pure logic

**Cost:** $90/month
**Validity Score:** 9/10

**Highlights:**
- Extensive real Claude/Gmail/Sheets/Stripe testing
- Error scenario coverage (timeouts, rate limits, failures)
- Cost management through caching and selective running
- Smoke tests on PR, full suite nightly

**Weaknesses:**
- Slower feedback loops (integration tests are slower)
- Higher API costs
- Potential test flakiness from real services

---

### Designer 2: Layered Testing Strategist

**Philosophy:** "Different tests, different purposes, different cadences."

**Key Strengths:**
- Balanced test pyramid (70% unit, 20% integration, 10% E2E)
- Fast developer feedback (<30s local unit tests)
- Contract testing validates API structures without cost
- Intelligent test scheduling (unit on commit, E2E nightly)

**Test Distribution:**
- 70% Unit Tests (~140 tests) - Pure logic
- 20% Integration Tests (~40 tests) - Contract + service tests
- 10% E2E Tests (~20 tests) - Critical workflows

**Cost:** $150/month
**Validity Score:** 8.5/10

**Highlights:**
- Contract tests prevent API breakage without cost
- pytest marker system for selective execution
- Parallel execution optimization
- Comprehensive cost vs speed trade-off analysis

**Weaknesses:**
- More complex test organization
- Contract tests could drift from reality
- Requires discipline to maintain pyramid

---

### Designer 3: Behavior-Driven Quality Engineer

**Philosophy:** "Tests should validate business outcomes, not implementation details."

**Key Strengths:**
- Business-readable tests (Given/When/Then)
- Tests serve as living documentation
- Stakeholder communication via Gherkin scenarios
- User-centric validation (outcomes over implementation)

**Test Distribution:**
- 40% Business Scenario Tests (~80 tests) - E2E in BDD format
- 40% Component Behavior Tests (~80 tests) - Service behaviors
- 20% Domain Logic Tests (~40 tests) - Pure logic

**Cost:** $180/month
**Validity Score:** 8/10

**Highlights:**
- pytest-bdd framework for Gherkin scenarios
- Acceptance criteria as test specifications
- Non-technical stakeholders can read tests
- Living documentation for onboarding

**Weaknesses:**
- BDD framework overhead
- Higher proportion of expensive E2E tests
- Step definition maintenance burden

---

## Phase 2: Debate Analysis

### Evaluation Criteria Scoring

| Criterion | Designer 1 (Integration) | Designer 2 (Layered) | Designer 3 (BDD) |
|-----------|-------------------------|---------------------|-----------------|
| **Effectiveness** | 10/10 - Catches real bugs | 8/10 - Some contract drift risk | 9/10 - Validates outcomes |
| **Repeatability** | 7/10 - Real service flakiness | 9/10 - Fast, deterministic | 7/10 - Real service dependency |
| **Quality** | 9/10 - High confidence | 8.5/10 - Balanced approach | 8/10 - Business alignment |
| **Speed** | 6/10 - Slower feedback | 10/10 - Fast local tests | 6/10 - Heavy E2E focus |
| **Cost** | 8/10 - $90/month | 7/10 - $150/month | 6/10 - $180/month |
| **Maintainability** | 8/10 - Simple structure | 7/10 - Complex organization | 7/10 - BDD overhead |
| **Coverage** | 10/10 - All APIs real | 8/10 - Contract + smoke | 9/10 - Business scenarios |
| **TOTAL** | **58/70 (83%)** | **57.5/70 (82%)** | **52/70 (74%)** |

### Detailed Criterion Analysis

#### 1. Effectiveness (Catching Real Bugs)

**Designer 1 (10/10):** Real API tests catch actual production issues:
- API contract changes detected immediately
- Real error scenarios (timeouts, rate limits) validated
- No false confidence from mocks

**Designer 2 (8/10):** Good coverage but contract drift risk:
- Contract tests validate structure, not behavior
- Could miss API behavior changes between real test runs
- Mitigated by nightly real service tests

**Designer 3 (9/10):** Business outcome validation:
- E2E tests catch integration failures
- User workflows validated end-to-end
- May miss lower-level API issues

**Winner:** Designer 1 (Integration-First)

---

#### 2. Repeatability (Deterministic Tests)

**Designer 1 (7/10):** Real services introduce variability:
- API rate limits can cause intermittent failures
- Network issues affect reliability
- Requires robust retry logic

**Designer 2 (9/10):** Layered approach maximizes determinism:
- 70% unit tests are perfectly deterministic
- Contract tests always consistent
- Real tests isolated to nightly runs

**Designer 3 (7/10):** Heavy E2E creates flakiness:
- 40% E2E tests subject to real service issues
- BDD scenarios might have timing issues
- Requires careful test data management

**Winner:** Designer 2 (Layered)

---

#### 3. Quality (Production Confidence)

**Designer 1 (9/10):** High confidence through real validation:
- Zero critical paths rely on mocks
- All external integrations validated
- Error recovery proven

**Designer 2 (8.5/10):** Balanced confidence:
- Unit tests prove logic correctness
- Contract tests prevent breakage
- Selective real tests validate integration

**Designer 3 (8/10):** Business outcome confidence:
- Critical workflows proven end-to-end
- User acceptance validated
- Less coverage of edge cases

**Winner:** Designer 1 (Integration-First)

---

#### 4. Speed (Feedback Loop)

**Designer 1 (6/10):** Integration tests are inherently slower:
- Even optimized integration tests take seconds
- Full suite 5+ minutes
- Local dev feedback delayed

**Designer 2 (10/10):** Optimized for fast feedback:
- Local unit tests <30 seconds
- PR builds <2 minutes
- Developers stay in flow

**Designer 3 (6/10):** BDD scenarios can be slow:
- 40% E2E tests expensive to run
- Full scenario execution takes time
- Local dev limited to unit tests

**Winner:** Designer 2 (Layered)

---

#### 5. Cost (API Usage)

**Designer 1 (8/10):** Moderate cost, high value:
- $90/month sustainable
- Caching optimizations
- Selective running on PR

**Designer 2 (7/10):** Higher cost for comprehensive E2E:
- $150/month
- More extensive E2E suite
- Extra $60/month for faster feedback

**Designer 3 (6/10):** Highest cost:
- $180/month
- Heavy E2E focus (40% vs 10%)
- BDD framework overhead

**Winner:** Designer 1 (Integration-First)

---

#### 6. Maintainability (Long-term)

**Designer 1 (8/10):** Simple, straightforward:
- Clear test purpose (integration vs E2E vs unit)
- Real tests don't need mock updates
- Straightforward structure

**Designer 2 (7/10):** Complexity from layers:
- Multiple test types to maintain
- Contract test updates when APIs change
- Requires discipline to maintain pyramid

**Designer 3 (7/10):** BDD overhead:
- Step definition maintenance
- Feature file + step def synchronization
- Worth it for documentation value

**Winner:** Designer 1 (Integration-First)

---

#### 7. Coverage (Completeness)

**Designer 1 (10/10):** All critical paths with real services:
- 100% external API coverage
- 100% error scenario coverage
- 100% E2E workflow coverage

**Designer 2 (8/10):** Comprehensive but some contract-only:
- 100% unit coverage of logic
- Contract tests for API structure
- Smoke tests for real validation

**Designer 3 (9/10):** Business scenario coverage:
- All user workflows validated
- All acceptance criteria tested
- May miss internal edge cases

**Winner:** Designer 1 (Integration-First)

---

### Key Trade-offs Identified

#### Trade-off 1: Speed vs Confidence
- **Layered (Fast):** 70% unit tests run in seconds, but relies on contracts
- **Integration (Confident):** 60% real tests give certainty, but slower
- **Resolution:** Hybrid - unit tests for local dev, real tests in CI

#### Trade-off 2: Cost vs Coverage
- **Integration (Cheap):** $90/month, extensive real testing
- **BDD (Expensive):** $180/month, business-readable scenarios
- **Resolution:** Hybrid - selective BDD for critical paths only

#### Trade-off 3: Complexity vs Readability
- **BDD (Readable):** Gherkin scenarios for stakeholders, but setup overhead
- **Integration (Simple):** Straightforward pytest, less documentation value
- **Resolution:** Hybrid - BDD for acceptance criteria, pytest for most tests

---

## Phase 3: Final Unified Plan

### Hybrid Strategy: Best of All Three

**Core Philosophy:**
1. **Real APIs for confidence** (Designer 1)
2. **Layered execution for speed** (Designer 2)
3. **BDD for critical acceptance criteria** (Designer 3)

### Test Distribution (200 tests total)

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: BDD Acceptance Tests          10% (20 tests) │
│  - Critical user workflows in Gherkin                  │
│  - Stakeholder-readable scenarios                      │
│  - Living documentation                                │
│  Run: On-Demand (manual trigger)                       │
│  Cost: High (real services)                            │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: Integration Tests (Real)      25% (50 tests) │
│  - Real Claude/Gmail/Sheets/Stripe                     │
│  - Error scenarios (timeouts, failures)                │
│  - API contract validation                             │
│  Run: On-Demand (full), subset on merge                │
│  Cost: Medium                                          │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: Service Tests (Mocked)        15% (30 tests) │
│  - Component integration                               │
│  - Contract tests (API structure)                      │
│  - Workflow orchestration                              │
│  Run: Every PR                                         │
│  Cost: None                                            │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: Unit Tests                    50% (100 tests)│
│  - Pure business logic                                 │
│  - Domain models, validators                           │
│  - Voting, scoring algorithms                          │
│  Run: Every commit, local dev                          │
│  Cost: None                                            │
└─────────────────────────────────────────────────────────┘
```

### Test Execution Schedule

```
┌─────────────────────────────────────────────────────────┐
│  LOCAL DEV (Every save)                                │
│  - Layer 1: Unit tests (100 tests)                     │
│  - Duration: <30 seconds                               │
│  - Cost: $0                                            │
│  Command: pytest -m unit                               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PR / COMMIT (Every push)                              │
│  - Layer 1: Unit tests (100 tests)                     │
│  - Layer 2: Service tests (30 tests)                   │
│  - Duration: <2 minutes                                │
│  - Cost: $0                                            │
│  Command: pytest -m "unit or service"                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  MERGE TO MAIN (Every merge)                           │
│  - Layer 1: Unit tests (100 tests)                     │
│  - Layer 2: Service tests (30 tests)                   │
│  - Layer 3: Smoke integration (10 tests)               │
│  - Duration: <5 minutes                                │
│  - Cost: ~$1                                           │
│  Command: pytest -m "unit or service or smoke"         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  ON-DEMAND FULL SUITE (Manual trigger)                 │
│  - All layers (200 tests)                              │
│  - Full integration suite with real APIs               │
│  - All BDD acceptance scenarios                        │
│  - Duration: ~15 minutes                               │
│  - Cost: ~$4 per run                                   │
│  Command: pytest --all                                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PRE-RELEASE (Before production deploy)                │
│  - All tests (200 tests)                               │
│  - Extended error scenarios                            │
│  - Load/performance tests                              │
│  - Duration: ~30 minutes                               │
│  - Cost: ~$10                                          │
│  Command: pytest --release --performance               │
└─────────────────────────────────────────────────────────┘
```

**Monthly Cost (Pre-Production):** ~$20-40 (5-10 on-demand runs + merge smoke tests)

### Test Layer Details

#### Layer 1: Unit Tests (50% - 100 tests)

**Philosophy:** Fast, deterministic, pure logic validation

**What to Test:**
- Domain models (`workflow/models.py`)
- Consensus voting (`workflow/voter.py` - keep existing 44 tests)
- QA validators (`qa/validators/`)
- Scoring algorithms (`qa/scoring.py`)
- Business rule calculations

**Characteristics:**
- No external dependencies
- No mocks needed (pure functions)
- Run in <10ms per test
- 100% deterministic

**Example Test:**
```python
# tests/unit/contexts/workflow/test_models.py
def test_budget_tier_should_limit_max_tokens():
    """Budget tier limited to 1000 tokens."""
    inquiry = WorkflowInquiry(
        company_name="Test",
        website="https://test.com",
        industry="Tech",
        prompt="Test",
        tier=WorkflowTier.BUDGET
    )
    assert inquiry.max_tokens == 1000
```

**Target:** 100 tests
- Domain models: 30 tests
- Voter logic: 44 tests (existing)
- Validators: 26 tests (21 existing + 5 new)

---

#### Layer 2: Service Tests (15% - 30 tests)

**Philosophy:** Component integration with mocked externals

**What to Test:**
- Workflow engine orchestration
- Component interactions
- Contract validation (API response structures)
- Error handling logic

**Characteristics:**
- Mock external APIs (Claude, Gmail, Sheets, Stripe)
- Real internal components
- Run in <100ms per test
- Validate contracts without API costs

**Example Test:**
```python
# tests/integration/services/test_workflow_engine_integration.py
def test_should_orchestrate_ai_and_voter(mock_ai_provider):
    """Test AI → Voter → Result flow."""
    engine = WorkflowEngine(
        ai_provider=mock_ai_provider,
        voter=ConsensusVoter(),  # Real
        validator=QAValidator()  # Real
    )

    result = engine.process_inquiry(test_inquiry)

    assert result.selected_workflow is not None
    assert result.consensus_score > 0.8
```

**Example Contract Test:**
```python
# tests/integration/contracts/test_claude_contract.py
def test_should_parse_valid_claude_response():
    """Validate Claude response structure parsing."""
    response = {
        "id": "msg_123",
        "content": [{"type": "text", "text": "Workflow"}],
        "model": "claude-sonnet-4-5",
        "usage": {"input_tokens": 100, "output_tokens": 200}
    }

    parsed = claude_adapter._parse_response(response)

    assert parsed.content == "Workflow"
    assert parsed.usage.input_tokens == 100
```

**Target:** 30 tests
- Component integration: 10 tests
- Contract tests: 15 tests (Claude, Gmail, Sheets, Stripe)
- Error handling: 5 tests

---

#### Layer 3: Integration Tests - Real APIs (25% - 50 tests)

**Philosophy:** Validate actual external service behavior

**What to Test:**
- Real Claude API calls
- Real Gmail email sending
- Real Google Sheets logging
- Real Stripe payments (test mode)
- Error scenarios (timeouts, rate limits, failures)
- Retry logic validation

**Characteristics:**
- Real API keys (test environment)
- Real network calls
- Run in 1-5 seconds per test
- Subject to API rate limits

**Example Test:**
```python
# tests/integration/real/test_claude_real.py
@pytest.mark.integration
@pytest.mark.real
def test_should_generate_workflow_with_real_claude():
    """Validate real Claude API integration."""
    claude = ClaudeAdapter(api_key=os.getenv("ANTHROPIC_TEST_API_KEY"))

    response = claude.generate_completion(
        prompt="Test workflow for e-commerce checkout",
        temperature=0.7,
        max_tokens=500  # Keep low for cost
    )

    assert response.content is not None
    assert len(response.content) > 0
    assert response.usage.output_tokens > 0
```

**Example Error Scenario:**
```python
@pytest.mark.integration
@pytest.mark.real
def test_should_retry_on_timeout():
    """Test Claude timeout with retry logic."""
    claude = ClaudeAdapter(timeout=1)  # Aggressive timeout

    # Should retry and eventually succeed or fail gracefully
    result = claude.generate_completion_with_retry(
        prompt="Test",
        max_retries=3
    )

    assert result.retry_count > 0  # Proves retry occurred
```

**Target:** 50 tests
- Claude API: 15 tests (happy path + errors)
- Gmail API: 10 tests (send, attachments, failures)
- Sheets API: 10 tests (logging, reading, errors)
- Stripe API: 10 tests (payments, declines, webhooks)
- Error scenarios: 5 tests (cross-service)

**Cost Management:**
- Minimum token limits (500 max)
- Response caching where possible
- Smoke subset (10 tests) on merge, full suite (50 tests) nightly

---

#### Layer 4: BDD Acceptance Tests (10% - 20 tests)

**Philosophy:** Business-readable acceptance criteria

**What to Test:**
- Critical user workflows (one per tier)
- Payment processing flows
- Email delivery scenarios
- Critical failure recovery

**Characteristics:**
- Written in Gherkin (Given/When/Then)
- Real services end-to-end
- Run in 5-30 seconds per scenario
- Serve as living documentation

**Example Feature:**
```gherkin
# tests/features/workflow_generation.feature
Feature: Workflow Generation
  As a business owner
  I want to receive AI-generated workflows
  So that I can improve my processes

  Scenario: Budget tier complete workflow
    Given I am a business owner at "Test Corp"
    And my industry is "E-commerce"
    When I request a budget tier workflow for "optimize checkout"
    Then I should receive 3 workflow recommendations
    And the consensus score should be above 0.7
    And I should receive an email with the workflows
```

**Step Definitions:**
```python
# tests/step_defs/workflow_steps.py
@when(parsers.parse('I request a budget tier workflow for "{prompt}"'))
def request_budget_workflow(context, workflow_engine, prompt):
    inquiry = WorkflowInquiry(
        company_name=context['company_name'],
        industry=context['industry'],
        prompt=prompt,
        tier=WorkflowTier.BUDGET
    )
    context['result'] = workflow_engine.process_inquiry(inquiry)
```

**Target:** 20 tests
- Budget tier workflow: 3 scenarios
- Standard tier workflow: 3 scenarios
- Premium tier workflow: 3 scenarios
- Payment processing: 4 scenarios
- Email delivery: 3 scenarios
- Error recovery: 4 scenarios

**When to Use BDD:**
- Critical user-facing features
- Acceptance criteria from stakeholders
- Features requiring non-technical review
- Regression prevention for escaped bugs

**When NOT to Use BDD:**
- Internal logic (use unit tests)
- Performance testing
- Load testing
- Exploratory testing

---

## Implementation Roadmap

### Overview

```
Phase 1: Foundation       Week 1-2   (Infrastructure + Unit tests)
Phase 2: Service Tests    Week 3     (Contracts + Mocked integration)
Phase 3: Real Integration Week 4-5   (Real API tests)
Phase 4: BDD Acceptance   Week 6     (Critical scenarios)
Phase 5: Optimization     Week 7     (CI/CD, performance)
```

---

### Phase 1: Foundation (Week 1-2)

**Goal:** Establish test infrastructure and expand unit tests

#### Week 1: Infrastructure

**Day 1-2: Test Environment Setup**
1. Create test Google Cloud project
2. Generate test API keys:
   - Anthropic API (test key)
   - Google Cloud (test service account)
   - Stripe (test mode keys)
3. Create test resources:
   - Test Gmail account for email testing
   - Test spreadsheet for QA logging
   - Test Stripe products

**Day 3-4: Test Structure**
1. Reorganize test directories:
   ```
   tests/
   ├── unit/                    # Layer 1
   │   ├── contexts/
   │   │   ├── workflow/
   │   │   └── qa/
   │   └── domain/
   ├── integration/
   │   ├── contracts/           # Layer 2
   │   ├── services/            # Layer 2
   │   └── real/                # Layer 3
   ├── features/                # Layer 4 (BDD)
   │   └── components/
   ├── step_defs/               # Layer 4 (BDD)
   └── conftest.py
   ```

2. Configure pytest markers in `pytest.ini`:
   ```ini
   [pytest]
   markers =
       unit: Unit tests (fast, isolated)
       service: Service integration tests (mocked externals)
       contract: Contract tests (API structure validation)
       integration: Integration tests (real APIs)
       real: Real service tests (expensive)
       smoke: Smoke tests (subset of integration)
       bdd: BDD acceptance tests (Gherkin scenarios)
       slow: Slow tests (run nightly)
   ```

**Day 5: CI/CD Configuration**
1. Create GitHub Actions workflow:
   ```yaml
   # .github/workflows/tests.yml
   name: Tests

   on: [push, pull_request]

   jobs:
     pr-tests:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Set up Python
           uses: actions/setup-python@v2
           with:
             python-version: 3.9
         - name: Install dependencies
           run: pip install -r workflow_system/requirements.txt
         - name: Run PR tests
           run: cd workflow_system && pytest -m "unit or service" -v

     nightly-tests:
       runs-on: ubuntu-latest
       if: github.event_name == 'schedule'
       steps:
         - name: Run full test suite
           run: cd workflow_system && pytest -v
   ```

**Deliverable:**
- Test environment configured
- Test structure created
- CI/CD pipeline active

#### Week 2: Expand Unit Tests

**Goal:** Achieve 100 unit tests covering all business logic

**Day 1-2: Domain Model Tests**
Create `tests/unit/domain/test_models.py`:
```python
class TestWorkflowInquiry:
    """Tests for WorkflowInquiry domain model."""

    def test_should_create_valid_inquiry(self):
        """Test creating inquiry with valid data."""
        inquiry = WorkflowInquiry(
            company_name="Test Corp",
            website="https://test.com",
            industry="Tech",
            prompt="Test workflow",
            tier=WorkflowTier.STANDARD
        )
        assert inquiry.company_name == "Test Corp"
        assert inquiry.tier == WorkflowTier.STANDARD

    def test_should_validate_website_url(self):
        """Test URL validation."""
        with pytest.raises(ValidationError, match="Invalid URL"):
            WorkflowInquiry(
                company_name="Test",
                website="not-a-url",
                ...
            )

    # ... 28 more domain model tests
```

**Target:** 30 tests for domain models

**Day 3: Tier Calculation Tests**
Create `tests/unit/domain/test_tier_calculations.py`:
```python
class TestTierCalculations:
    """Tests for tier-based business rules."""

    def test_budget_tier_should_generate_3_workflows(self):
        assert WorkflowTier.BUDGET.workflow_count == 3

    def test_budget_tier_should_limit_tokens_to_1000(self):
        assert WorkflowTier.BUDGET.max_tokens == 1000

    # ... more tier tests
```

**Target:** 10 tests for tier logic

**Day 4-5: Validator Tests**
Expand existing validator tests:
- Keep existing 21 tests in `test_scoring.py`
- Add 5 new tests for edge cases

**Verify Existing Tests:**
Keep `test_voter.py` (44 tests) - already excellent

**Week 2 Deliverable:**
- 100 unit tests total:
  - Domain models: 30 tests
  - Tier calculations: 10 tests
  - Validators: 26 tests (21 existing + 5 new)
  - Voter: 44 tests (existing)
- All passing in <30 seconds

---

### Phase 2: Service Tests (Week 3)

**Goal:** Add contract tests and service integration tests

#### Day 1-2: Contract Tests

**Create contract test infrastructure:**

`tests/integration/contracts/fixtures.py`:
```python
"""Fixtures for API contract validation."""

@pytest.fixture
def valid_claude_response():
    """Valid Claude API response structure."""
    return {
        "id": "msg_123abc",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Workflow recommendation"}],
        "model": "claude-sonnet-4-5",
        "usage": {
            "input_tokens": 150,
            "output_tokens": 300
        }
    }

@pytest.fixture
def valid_gmail_response():
    """Valid Gmail API response."""
    return {
        "id": "msg_xyz789",
        "threadId": "thread_abc",
        "labelIds": ["SENT"]
    }

# ... more fixtures
```

**Create contract tests:**

`tests/integration/contracts/test_claude_contract.py`:
```python
@pytest.mark.contract
class TestClaudeAPIContract:
    """Contract tests for Claude API integration."""

    def test_should_parse_valid_response(self, valid_claude_response):
        """Test parsing valid Claude response."""
        adapter = ClaudeAdapter(api_key="test")
        parsed = adapter._parse_response(valid_claude_response)

        assert parsed.content == "Workflow recommendation"
        assert parsed.model == "claude-sonnet-4-5"
        assert parsed.usage.input_tokens == 150

    def test_should_reject_malformed_response(self):
        """Test handling malformed response."""
        adapter = ClaudeAdapter(api_key="test")
        malformed = {"id": "123"}  # Missing required fields

        with pytest.raises(ContractViolationError):
            adapter._parse_response(malformed)

    # ... 3 more contract tests
```

**Target:** 15 contract tests
- Claude: 5 tests
- Gmail: 3 tests
- Sheets: 4 tests
- Stripe: 3 tests

#### Day 3-4: Service Integration Tests

**Create service tests:**

`tests/integration/services/test_workflow_engine_integration.py`:
```python
@pytest.mark.service
class TestWorkflowEngineIntegration:
    """Service integration tests for WorkflowEngine."""

    @pytest.fixture
    def mock_ai_provider(self):
        """Mock AI with realistic responses."""
        return MockAIProvider(responses=[
            WorkflowResponse(content="Workflow A", score=0.9),
            WorkflowResponse(content="Workflow A", score=0.85),
            WorkflowResponse(content="Workflow B", score=0.7),
        ])

    def test_should_integrate_ai_voter_validator(self, mock_ai_provider):
        """Test AI → Voter → Validator flow."""
        engine = WorkflowEngine(
            ai_provider=mock_ai_provider,
            voter=ConsensusVoter(),      # Real
            validator=QAValidator()       # Real
        )

        result = engine.process_inquiry(test_inquiry)

        assert result.selected_workflow.content == "Workflow A"
        assert result.consensus_score > 0.8
        assert result.qa_metrics.overall_score > 0

    # ... 9 more service tests
```

**Target:** 10 service tests

#### Day 5: Verify and Refine

- Run all unit + service tests
- Verify <2 minute execution time
- Fix any failures
- Document test patterns

**Week 3 Deliverable:**
- 30 service tests:
  - Contract tests: 15
  - Service integration: 10
  - Error handling: 5
- All passing in <2 minutes (with unit tests)

---

### Phase 3: Real Integration Tests (Week 4-5)

**Goal:** Comprehensive real API validation

#### Week 4: Core Real API Tests

**Day 1-2: Claude API Real Tests**

`tests/integration/real/test_claude_real.py`:
```python
@pytest.mark.integration
@pytest.mark.real
class TestClaudeRealIntegration:
    """Real Claude API integration tests."""

    @pytest.fixture
    def real_claude(self):
        """Real Claude client."""
        return ClaudeAdapter(api_key=os.getenv("ANTHROPIC_TEST_API_KEY"))

    def test_should_generate_workflow_happy_path(self, real_claude):
        """Test successful workflow generation."""
        response = real_claude.generate_completion(
            prompt="E-commerce checkout optimization workflow",
            temperature=0.7,
            max_tokens=500
        )

        assert response.content is not None
        assert len(response.content) > 100
        assert response.usage.output_tokens > 0

    def test_should_handle_invalid_api_key(self):
        """Test authentication failure."""
        invalid = ClaudeAdapter(api_key="invalid_key")
        with pytest.raises(AuthenticationError):
            invalid.generate_completion("test")

    # ... 13 more Claude tests (timeouts, rate limits, etc.)
```

**Target:** 15 Claude API tests

**Day 3: Gmail API Real Tests**

`tests/integration/real/test_gmail_real.py`:
```python
@pytest.mark.integration
@pytest.mark.real
class TestGmailRealIntegration:
    """Real Gmail API integration tests."""

    @pytest.fixture
    def real_gmail(self):
        """Real Gmail client."""
        return GmailAdapter(
            credentials_path=os.getenv("GMAIL_TEST_CREDENTIALS_PATH")
        )

    @pytest.fixture
    def test_recipient(self):
        """Test email recipient."""
        return "workflow-test@example.com"

    def test_should_send_email_successfully(self, real_gmail, test_recipient):
        """Test email sending."""
        subject = f"Test Email {uuid.uuid4()}"
        body = "Test email from integration tests"

        message_id = real_gmail.send_email(
            to=test_recipient,
            subject=subject,
            body=body
        )

        assert message_id is not None

        # Verify delivery
        time.sleep(5)
        messages = real_gmail.search_messages(f"subject:{subject}")
        assert len(messages) == 1

    # ... 9 more Gmail tests
```

**Target:** 10 Gmail API tests

**Day 4: Sheets + Stripe Real Tests**

`tests/integration/real/test_sheets_real.py` - 10 tests
`tests/integration/real/test_stripe_real.py` - 10 tests

**Day 5: Error Scenario Tests**

Create cross-service error tests:

`tests/integration/real/test_error_scenarios.py`:
```python
@pytest.mark.integration
@pytest.mark.real
class TestErrorScenarios:
    """Real error scenario tests."""

    def test_should_retry_claude_on_timeout(self, real_claude):
        """Test Claude retry logic."""
        # Configure aggressive timeout
        # Verify retry with exponential backoff
        pass

    def test_should_handle_sheets_write_failure(self):
        """Test Sheets failure recovery."""
        # Simulate write failure
        # Verify graceful degradation
        pass

    # ... 3 more error tests
```

**Target:** 5 cross-service error tests

**Week 4 Deliverable:**
- 50 real integration tests:
  - Claude: 15 tests
  - Gmail: 10 tests
  - Sheets: 10 tests
  - Stripe: 10 tests
  - Error scenarios: 5 tests

#### Week 5: Optimization

**Day 1-2: Response Caching**

Implement caching for repeated scenarios:

```python
# tests/integration/real/cache.py
class ResponseCache:
    """Cache for expensive API responses."""

    def __init__(self):
        self.cache = {}

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value

# Use in tests
@pytest.fixture(scope="session")
def response_cache():
    return ResponseCache()

def test_cached_scenario(real_claude, response_cache):
    cache_key = "standard_workflow_prompt"
    cached = response_cache.get(cache_key)

    if cached:
        response = cached
    else:
        response = real_claude.generate_completion(...)
        response_cache.set(cache_key, response)

    # Test with response
```

**Day 3: Smoke Test Subset**

Create smoke test marker for subset execution:

```python
# Mark critical tests as smoke
@pytest.mark.smoke
@pytest.mark.integration
def test_claude_basic_generation():
    """Smoke test: Claude generates workflow."""
    pass

# Run smoke tests on merge
pytest -m smoke
```

**Target:** 10 smoke tests (subset of 50 integration tests)

**Day 4-5: Parallel Execution**

Configure pytest-xdist:

```bash
pip install pytest-xdist
pytest -n auto  # Parallel execution
```

Ensure tests are independent:
- Use unique test data (UUIDs)
- Clean up after each test
- No shared state

**Week 5 Deliverable:**
- Response caching implemented
- 10 smoke tests identified
- Parallel execution working
- Integration suite runs in <5 minutes

---

### Phase 4: BDD Acceptance Tests (Week 6)

**Goal:** Add business-readable acceptance scenarios

#### Day 1: BDD Framework Setup

**Install pytest-bdd:**
```bash
pip install pytest-bdd
```

**Create feature structure:**
```
tests/
├── features/
│   ├── workflow_generation.feature
│   ├── payment_processing.feature
│   └── email_delivery.feature
└── step_defs/
    ├── workflow_steps.py
    ├── payment_steps.py
    └── email_steps.py
```

#### Day 2-3: Write Features

**Create workflow generation feature:**

`tests/features/workflow_generation.feature`:
```gherkin
Feature: Workflow Generation
  As a business owner
  I want to receive AI-generated workflows
  So that I can improve my processes

  Scenario: Budget tier complete workflow
    Given I am a business owner at "Acme Corp"
    And my industry is "E-commerce"
    When I request a budget tier workflow for "optimize checkout"
    Then I should receive 3 workflow recommendations
    And the consensus score should be above 0.7
    And I should receive an email with the workflows

  Scenario: Standard tier with higher quality
    Given I am a business owner at "TechStart"
    When I request a standard tier workflow for "improve onboarding"
    Then I should receive 5 workflow recommendations
    And the workflows should be more detailed than budget

  Scenario: Premium tier with expert analysis
    Given I am a business owner at "Enterprise LLC"
    When I request a premium tier workflow for "automate compliance"
    Then I should receive 7 workflow recommendations
    And I should receive an email with PDF attachment
```

**Target:** 3 scenarios (9 total across 3 files)

#### Day 4: Implement Step Definitions

`tests/step_defs/workflow_steps.py`:
```python
from pytest_bdd import given, when, then, scenarios, parsers

scenarios('../features/workflow_generation.feature')

@given(parsers.parse('I am a business owner at "{company}"'))
def business_owner(context, company):
    context['company_name'] = company

@when(parsers.parse('I request a budget tier workflow for "{prompt}"'))
def request_budget_workflow(context, workflow_engine, prompt):
    inquiry = WorkflowInquiry(
        company_name=context['company_name'],
        industry=context.get('industry', 'General'),
        prompt=prompt,
        tier=WorkflowTier.BUDGET
    )
    context['result'] = workflow_engine.process_inquiry(inquiry)

@then(parsers.parse('I should receive {count:d} workflow recommendations'))
def verify_workflow_count(context, count):
    assert len(context['result'].workflows) == count
```

**Target:** Reusable step definitions for 20 scenarios

#### Day 5: Additional Scenarios

**Payment processing (4 scenarios):**
- Successful payment
- Payment decline
- Payment timeout
- Refund flow

**Email delivery (3 scenarios):**
- Successful email send
- Email failure with download fallback
- PDF attachment for premium

**Error recovery (4 scenarios):**
- Claude API timeout with retry
- Gmail API failure
- Rate limit handling
- Service unavailability

**Week 6 Deliverable:**
- 20 BDD scenarios in Gherkin format
- Reusable step definitions
- All scenarios passing with real services
- Living documentation generated

---

### Phase 5: Optimization & CI/CD (Week 7)

**Goal:** Fast, reliable, cost-effective test execution

#### Day 1-2: CI/CD Pipeline Optimization

**Update GitHub Actions:**

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  pr-tests:
    name: PR Tests (Unit + Service)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r workflow_system/requirements.txt
      - name: Run unit + service tests
        run: |
          cd workflow_system
          pytest -m "unit or service" -v --durations=10
        timeout-minutes: 3

  merge-tests:
    name: Merge Tests (+ Smoke Integration)
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Run unit + service + smoke tests
        run: |
          cd workflow_system
          pytest -m "unit or service or smoke" -v
        env:
          ANTHROPIC_TEST_API_KEY: ${{ secrets.ANTHROPIC_TEST_API_KEY }}
          GMAIL_TEST_CREDENTIALS_PATH: ${{ secrets.GMAIL_TEST_CREDENTIALS }}
        timeout-minutes: 5

  on-demand-full-tests:
    name: On-Demand Full Suite
    runs-on: ubuntu-latest
    # Triggered manually via GitHub Actions UI or workflow_dispatch
    workflow_dispatch:
    steps:
      - name: Run all tests
        run: |
          cd workflow_system
          pytest -v --html=report.html --self-contained-html
        env:
          ANTHROPIC_TEST_API_KEY: ${{ secrets.ANTHROPIC_TEST_API_KEY }}
          GMAIL_TEST_CREDENTIALS_PATH: ${{ secrets.GMAIL_TEST_CREDENTIALS }}
          SHEETS_TEST_CREDENTIALS_PATH: ${{ secrets.SHEETS_TEST_CREDENTIALS }}
          STRIPE_TEST_SECRET_KEY: ${{ secrets.STRIPE_TEST_SECRET_KEY }}
        timeout-minutes: 20
      - name: Upload test report
        uses: actions/upload-artifact@v2
        with:
          name: test-report
          path: workflow_system/report.html

# Note: Can add scheduled nightly runs when moving to production:
# on:
#   schedule:
#     - cron: '0 2 * * *'  # 2 AM daily
```

#### Day 3: Cost Monitoring

**Create cost tracking:**

```python
# tests/utils/cost_tracker.py
class APIUsageTracker:
    """Track API usage and costs."""

    def __init__(self):
        self.usage = {
            "claude": {"tokens": 0, "cost": 0},
            "gmail": {"calls": 0},
            "sheets": {"writes": 0},
            "stripe": {"calls": 0}
        }

    def track_claude(self, input_tokens, output_tokens):
        """Track Claude API usage."""
        self.usage["claude"]["tokens"] += input_tokens + output_tokens
        # Claude pricing: ~$0.003 per 1K input, ~$0.015 per 1K output
        cost = (input_tokens / 1000 * 0.003) + (output_tokens / 1000 * 0.015)
        self.usage["claude"]["cost"] += cost

    def report(self):
        """Generate cost report."""
        print(f"\n=== API Usage Report ===")
        print(f"Claude: {self.usage['claude']['tokens']} tokens, ${self.usage['claude']['cost']:.2f}")
        print(f"Gmail: {self.usage['gmail']['calls']} calls")
        print(f"Sheets: {self.usage['sheets']['writes']} writes")

# Use in conftest.py
@pytest.fixture(scope="session")
def usage_tracker():
    tracker = APIUsageTracker()
    yield tracker
    tracker.report()
```

#### Day 4: Performance Optimization

**Parallel test execution:**

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto -m "unit or service"
```

**Test isolation verification:**

```python
# tests/utils/test_isolation.py
def test_tests_are_isolated():
    """Verify tests don't share state."""
    # Run tests multiple times in different orders
    # Verify consistent results
    pass
```

#### Day 5: Documentation & Training

**Create testing guide:**

`tests/README.md`:
```markdown
# Testing Guide

## Running Tests Locally

# Fast feedback (unit only)
pytest -m unit

# Pre-commit (unit + service)
pytest -m "unit or service"

# Full suite (requires API keys)
pytest

## Test Layers

1. Unit Tests (Layer 1) - 50% coverage
2. Service Tests (Layer 2) - 15% coverage
3. Integration Tests (Layer 3) - 25% coverage
4. BDD Acceptance (Layer 4) - 10% coverage

## Writing Tests

See examples in:
- Unit: `tests/unit/contexts/workflow/test_voter.py`
- Service: `tests/integration/services/test_workflow_engine_integration.py`
- Integration: `tests/integration/real/test_claude_real.py`
- BDD: `tests/features/workflow_generation.feature`
```

**Week 7 Deliverable:**
- Optimized CI/CD pipeline
- Cost tracking implemented
- Parallel execution working
- Testing documentation complete

---

## Success Metrics

### Test Quality Metrics

**Test Validity Score: 9/10** (up from 5/10)

Breakdown:
- Layer 1 (Unit): 100% validity (pure logic)
- Layer 2 (Service): 80% validity (contract + service tests)
- Layer 3 (Integration): 100% validity (real APIs)
- Layer 4 (BDD): 100% validity (real E2E)

Weighted average: (50% × 100%) + (15% × 80%) + (25% × 100%) + (10% × 100%) = 92% = 9/10

**Coverage Metrics:**

| Metric | Target | Current | Improvement |
|--------|--------|---------|-------------|
| Real API Coverage | 100% | 0% | +100% |
| Business Logic Coverage | 90% | ~60% | +30% |
| Error Scenario Coverage | 95% | ~20% | +75% |
| E2E Workflow Coverage | 100% | 0% | +100% |

**Reliability Metrics:**

| Metric | Target | Description |
|--------|--------|-------------|
| Test Flakiness | <1% | <2 flaky tests out of 200 |
| False Positive Rate | <3% | Tests fail only when code is broken |
| False Negative Rate | <1% | Tests catch real bugs |

### Performance Metrics

**Test Execution Times:**

| Stage | Duration | Frequency | Cost |
|-------|----------|-----------|------|
| Local dev (unit only) | <30s | Every save | $0 |
| PR (unit + service) | <2min | Every push | $0 |
| Merge (+ smoke) | <5min | Every merge | ~$1 |
| On-Demand (full suite) | <15min | Manual trigger | ~$4/run |
| Pre-release | <30min | Before deploys | ~$10 |

**Monthly Cost (Pre-Production):** ~$20-40
- On-demand full runs: ~$4/run × 5-10 runs = $20-40
- Merge smoke tests: Included in estimate
- Occasional debugging: Buffer included
- Total: ~$20-40/month during development

**Note:** Can scale to scheduled nightly builds (~$120/month) when in production

### Developer Experience Metrics

**Feedback Loop:**
- Code change → Unit test feedback: **<30 seconds**
- Code change → Full validation: **On-demand** (manual trigger, <15 min)
- Bug detected → Test written → Regression prevented: **<1 day**

**Confidence Level:**
- Developer confidence in tests: **High** (tests validate real behavior)
- Deployment confidence: **High** (all critical paths tested)
- Refactoring confidence: **High** (comprehensive unit tests)

---

## Risk Mitigation

### Risk 1: API Costs Exceed Budget

**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Set hard budget cap in CI ($5/day max)
- Alert on unusual usage patterns
- Response caching for repeated scenarios
- Automatic test pause if budget exceeded
- Token limits on all Claude tests (500 max)

**Monitoring:**
- Daily cost reports
- Per-test cost tracking
- Monthly budget review

---

### Risk 2: Test Flakiness from Real Services

**Likelihood:** Medium
**Impact:** High (slows development)
**Mitigation:**
- Robust retry logic (exponential backoff)
- Dedicated test environments (no interference)
- Idempotent test scenarios (unique UUIDs)
- Cleanup after each test
- Smoke tests isolate flakiness to nightly runs

**Monitoring:**
- Track test failure rates
- Alert on >2% flakiness
- Quarantine flaky tests for investigation

---

### Risk 3: Slow Test Execution Delays Feedback

**Likelihood:** Low (with proper layering)
**Impact:** High
**Mitigation:**
- 50% unit tests run in <30s locally
- Parallel execution (pytest-xdist)
- Selective test running (markers)
- Smart caching
- Integration tests only in CI, not local

**Monitoring:**
- Track test duration per layer
- Alert on PR builds >3 minutes
- Optimize slow tests

---

### Risk 4: Contract Tests Drift from Reality

**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Regular on-demand real API tests validate contracts
- Weekly/bi-weekly manual full test runs during active development
- Quarterly manual contract review
- Alert on contract test failures
- Update contracts when APIs change

**Monitoring:**
- Compare contract tests to real API responses regularly
- Track API version changes
- Document contract update process

---

### Risk 5: BDD Overhead Slows Development

**Likelihood:** Low
**Impact:** Low
**Mitigation:**
- BDD only for critical paths (10% of tests)
- Reusable step definitions
- Regular step definition refactoring
- Most tests still use simple pytest

**Monitoring:**
- Track BDD test maintenance time
- Developer feedback on BDD value
- Adjust BDD coverage if overhead too high

---

### Risk 6: Test Maintenance Burden Grows

**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Clear test structure (layers, markers)
- DRY principles (reusable fixtures)
- Good test names and documentation
- Regular test refactoring
- Delete obsolete tests

**Monitoring:**
- Track test-to-code ratio
- Developer feedback on test maintainability
- Quarterly test suite review

---

## Comparison to Current State

### Current State (5/10 Validity)

**Problems:**
- 86 tests, 60% use mocks inappropriately
- No real Claude/Gmail/Sheets/Stripe testing
- False confidence (tests pass, production might fail)
- No error scenario coverage
- No E2E workflow validation
- Slow, all tests run together

**Test Breakdown:**
- Real tests: 53 (62%)
- Mock tests: 16 (19%)
- Hybrid tests: 17 (19%)

### Proposed State (9/10 Validity)

**Solutions:**
- 200 tests, 90% validate real behavior
- 100% critical path coverage with real APIs
- True confidence (tests validate production behavior)
- 95% error scenario coverage
- 100% E2E workflow coverage
- Fast feedback (layered execution)

**Test Breakdown:**
- Layer 1 (Unit): 100 tests (50%) - Pure logic, perfect validity
- Layer 2 (Service): 30 tests (15%) - Contract + service, high validity
- Layer 3 (Integration): 50 tests (25%) - Real APIs, perfect validity
- Layer 4 (BDD): 20 tests (10%) - Real E2E, perfect validity

### Improvement Summary

| Metric | Current | Proposed | Improvement |
|--------|---------|----------|-------------|
| Total Tests | 86 | 200 | +133% |
| Validity Score | 5/10 | 9/10 | +80% |
| Real API Tests | 0 | 70 | +∞ |
| Error Coverage | ~20% | 95% | +375% |
| E2E Coverage | 0% | 100% | +∞ |
| Local Feedback | >2min | <30s | 4x faster |
| PR Feedback | >2min | <2min | Maintained |
| Cost/Month | $0 | ~$120 | Worth it |

---

## Conclusion

The hybrid testing strategy combines the best elements of all three approaches:

1. **Real APIs for Confidence** (from Integration-First)
   - 25% of tests use real Claude/Gmail/Sheets/Stripe
   - 100% critical path coverage
   - Zero reliance on mocks for validation

2. **Layered Execution for Speed** (from Layered Testing)
   - 50% unit tests run in <30s locally
   - Fast feedback loop maintained
   - Intelligent test scheduling (unit on commit, integration nightly)

3. **BDD for Business Alignment** (from Behavior-Driven)
   - 10% of tests in business-readable Gherkin
   - Living documentation for stakeholders
   - Acceptance criteria validation

**Key Outcomes:**

- **Quality:** Test validity 5/10 → 9/10
- **Speed:** Local feedback <30s, PR feedback <2min
- **Cost:** ~$20-40/month (pre-production, on-demand execution)
- **Coverage:** 100% critical paths, 95% error scenarios
- **Confidence:** True production readiness validation

**Next Steps:**

1. **Approve this plan** - Review and approve the strategy
2. **Phase 1 (Week 1-2):** Set up infrastructure, expand unit tests
3. **Phase 2 (Week 3):** Add service + contract tests
4. **Phase 3 (Week 4-5):** Implement real API integration tests
5. **Phase 4 (Week 6):** Create BDD acceptance scenarios
6. **Phase 5 (Week 7):** Optimize CI/CD, finalize documentation

**Expected Timeline:** 7 weeks from approval to full implementation

**Expected Investment:**
- Development time: ~80 hours (7 weeks × ~12 hours/week)
- API costs (pre-production): ~$20-40/month ongoing
- API costs (production): ~$120/month if scheduled nightly builds added
- Total ROI: **High** (catch bugs before production, faster debugging, true confidence)

---

## Appendices

### Appendix A: Test File Structure

```
workflow_system/tests/
├── conftest.py                          # Global fixtures
├── pytest.ini                           # Pytest configuration
├── README.md                            # Testing guide
│
├── unit/                                # Layer 1: Unit Tests (50%)
│   ├── contexts/
│   │   ├── workflow/
│   │   │   ├── test_models.py          # 30 tests
│   │   │   ├── test_voter.py           # 44 tests (existing)
│   │   │   └── test_prompts.py         # 10 tests
│   │   └── qa/
│   │       ├── test_validators.py      # 26 tests
│   │       └── test_scoring.py         # (existing)
│   └── domain/
│       └── test_tier_calculations.py   # 10 tests
│
├── integration/
│   ├── contracts/                       # Layer 2: Contract Tests
│   │   ├── fixtures.py
│   │   ├── test_claude_contract.py     # 5 tests
│   │   ├── test_gmail_contract.py      # 3 tests
│   │   ├── test_sheets_contract.py     # 4 tests
│   │   └── test_stripe_contract.py     # 3 tests
│   │
│   ├── services/                        # Layer 2: Service Tests
│   │   ├── test_workflow_engine_integration.py  # 10 tests
│   │   └── test_error_handling.py      # 5 tests
│   │
│   └── real/                            # Layer 3: Real API Tests
│       ├── test_claude_real.py         # 15 tests
│       ├── test_gmail_real.py          # 10 tests
│       ├── test_sheets_real.py         # 10 tests
│       ├── test_stripe_real.py         # 10 tests
│       └── test_error_scenarios.py     # 5 tests
│
├── features/                            # Layer 4: BDD Features
│   ├── workflow_generation.feature     # 9 scenarios
│   ├── payment_processing.feature      # 4 scenarios
│   ├── email_delivery.feature          # 3 scenarios
│   └── error_recovery.feature          # 4 scenarios
│
├── step_defs/                           # Layer 4: BDD Steps
│   ├── workflow_steps.py
│   ├── payment_steps.py
│   ├── email_steps.py
│   └── common_steps.py
│
└── utils/
    ├── cost_tracker.py                  # API cost monitoring
    ├── cache.py                         # Response caching
    └── test_data.py                     # Test data generators
```

### Appendix B: pytest.ini Configuration

```ini
[pytest]
# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers
markers =
    unit: Unit tests (fast, isolated, pure logic)
    service: Service integration tests (mocked externals)
    contract: Contract tests (API structure validation)
    integration: Integration tests (real APIs, expensive)
    real: Real service tests (subset of integration)
    smoke: Smoke tests (critical real API subset)
    bdd: BDD acceptance tests (Gherkin scenarios)
    slow: Slow tests (run nightly, not on PR)

# Default test selection
# Run unit + service by default (fast feedback)
addopts =
    -v
    -m "unit or (service and not slow)"
    --strict-markers
    --tb=short
    --durations=10

# Parallel execution (optional, enable with -n flag)
# addopts = -n auto

# Coverage (optional)
# addopts = --cov=workflow_system --cov-report=html

# Logging
log_cli = true
log_cli_level = INFO
log_file = tests.log
log_file_level = DEBUG

# Test paths
testpaths = tests
```

### Appendix C: Running Tests - Quick Reference

```bash
# ============================================
# Local Development
# ============================================

# Fast feedback (unit tests only)
pytest -m unit

# Pre-commit check (unit + service)
pytest -m "unit or service"

# ============================================
# CI/CD
# ============================================

# PR build (unit + service, <2 min)
pytest -m "unit or service" -v

# Merge to main (+ smoke integration, <5 min)
pytest -m "unit or service or smoke" -v

# On-demand full suite (<15 min, manual trigger)
pytest -v

# ============================================
# Specific Layers
# ============================================

# Layer 1: Unit tests only
pytest -m unit

# Layer 2: Service + contract tests
pytest -m "service or contract"

# Layer 3: Real integration tests
pytest -m integration

# Layer 4: BDD acceptance tests
pytest -m bdd

# ============================================
# Specific Features
# ============================================

# Run specific feature file
pytest tests/features/workflow_generation.feature

# Run specific scenario
pytest -k "budget tier workflow"

# Run specific test file
pytest tests/unit/contexts/workflow/test_voter.py

# Run specific test
pytest tests/unit/contexts/workflow/test_voter.py::TestConsensusVoter::test_should_select_majority

# ============================================
# Advanced Options
# ============================================

# Parallel execution (faster)
pytest -n auto -m unit

# With coverage report
pytest --cov=workflow_system --cov-report=html

# Generate HTML report
pytest --html=report.html --self-contained-html

# Verbose with output
pytest -v -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# ============================================
# Cost-Conscious
# ============================================

# Run without expensive tests
pytest -m "not integration and not bdd"

# Run only smoke tests (minimal API cost)
pytest -m smoke

# ============================================
# Debugging
# ============================================

# Run with debugger on failure
pytest --pdb

# Print test durations
pytest --durations=0

# Verbose logging
pytest -v -s --log-cli-level=DEBUG
```

### Appendix D: Cost Estimation Details

**Claude API Pricing (Sonnet 4.5):**
- Input tokens: ~$0.003 per 1K tokens
- Output tokens: ~$0.015 per 1K tokens

**Test Cost Breakdown:**

| Test Type | Count | Avg Tokens | Cost/Test | Total |
|-----------|-------|------------|-----------|-------|
| Claude Integration | 15 | 500 | $0.008 | $0.12 |
| Gmail Integration | 10 | 0 | $0 | $0 |
| Sheets Integration | 10 | 0 | $0 | $0 |
| Stripe Integration | 10 | 0 | $0 | $0 |
| Error Scenarios | 5 | 300 | $0.005 | $0.025 |
| BDD Acceptance | 20 | 800 | $0.012 | $0.24 |
| **Total per run** | **70** | - | - | **$0.385** |

**Monthly Costs (Pre-Production):**

| Build Type | Runs/Month | Cost/Run | Monthly Cost |
|------------|------------|----------|--------------|
| Merge (smoke tests) | ~10-20 | $1.00 | $10-20 |
| On-Demand (full) | 5-10 | $4.00 | $20-40 |
| Pre-release | 0-1 | $10.00 | $0-10 |
| Buffer/Debug | - | - | Included |
| **TOTAL** | - | - | **~$20-40** |

**Note:** Actual costs may vary based on:
- Test execution frequency (on-demand vs scheduled)
- Token usage per test
- API pricing changes
- Debugging/iteration cycles

**Pre-Production Budget: $20-40/month** (on-demand execution)
**Production Budget: ~$120/month** (if scheduled nightly builds added)

---

## Final Recommendations

### Immediate Actions (This Week)

1. **Approve this plan** - Review and sign off on strategy
2. **Set up test environment** - Create test accounts, API keys
3. **Allocate budget** - Approve $20-40/month for on-demand API testing
4. **Schedule kickoff** - Plan 7-week implementation timeline

### Short-term Goals (Month 1-2)

1. **Phase 1-2 complete** - Unit tests + service tests operational
2. **PR builds working** - Fast feedback loop established
3. **Team training** - Developers comfortable with new test structure

### Long-term Success (Month 3+)

1. **Phase 3-5 complete** - Full test suite operational
2. **CI/CD optimized** - Fast, reliable, cost-effective
3. **Quality metrics** - 9/10 test validity, <1% flakiness
4. **Developer satisfaction** - Fast feedback, high confidence

### Success Criteria Checklist

- [ ] 200 tests implemented across 4 layers
- [ ] Test validity score 9/10 or higher
- [ ] Local feedback time <30 seconds (unit tests)
- [ ] PR feedback time <2 minutes
- [ ] Monthly API costs <$150
- [ ] 100% critical path coverage with real APIs
- [ ] 95% error scenario coverage
- [ ] <1% test flakiness
- [ ] Developer satisfaction with test suite

---

**This plan is ready for implementation upon approval.**

Questions? Contact the orchestrator or individual designer teams for clarification.
