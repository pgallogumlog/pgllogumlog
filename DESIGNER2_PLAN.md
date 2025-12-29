# Layered Testing Strategy Plan
**Designer 2: Layered Testing Strategist**

## Executive Philosophy

The test pyramid exists for a reason: fast feedback from unit tests, confidence from integration tests, and validation from E2E tests. Balance speed with coverage through intelligent layering and contract testing.

## Core Principles

1. **Test Pyramid First** - 70% unit, 20% integration, 10% E2E
2. **Fast Feedback Loops** - Developers run tests in <30 seconds locally
3. **Contract Testing** - Validate API contracts without expensive real calls
4. **Strategic Mocking** - Use mocks for speed, real services for validation
5. **Continuous Validation** - Different test layers run at different cadences

## Test Architecture

### Standard Test Pyramid

```
            ╱╲
           ╱  ╲
          ╱ E2E╲           10% - Full workflows, real services
         ╱      ╲          Run: Nightly, Pre-release
        ╱────────╲
       ╱          ╲
      ╱ Integration╲       20% - Contract tests, service tests
     ╱              ╲      Run: On merge to main
    ╱────────────────╲
   ╱                  ╲
  ╱   Unit Tests       ╲   70% - Pure logic, fast execution
 ╱                      ╲  Run: Every commit, local dev
╱────────────────────────╲
```

### Test Distribution Target

- **70% Unit Tests** (~140 tests) - Fast, isolated, deterministic
- **20% Integration Tests** (~40 tests) - Contract validation, service tests
- **10% E2E Tests** (~20 tests) - Real workflows, all services
- **Total: ~200 tests** (expanding from current 86)

## Layer 1: Unit Tests (70%)

### Philosophy
Test **business logic** in isolation. No external dependencies. Pure functions, domain models, calculations. These should run in milliseconds.

### What to Unit Test

1. **Domain Models** (`workflow/models.py`)
   - Validation logic
   - Data transformations
   - Business rules

2. **Pure Functions** (`workflow/voter.py`)
   - Consensus voting algorithms
   - Scoring calculations
   - Data aggregation

3. **Validators** (`qa/validators/`)
   - Deterministic validation rules
   - Scoring logic
   - Threshold checks

### Example: Domain Model Tests

**Location:** `tests/unit/contexts/workflow/test_models.py`

```python
class TestWorkflowInquiry:
    """Unit tests for WorkflowInquiry model."""

    def test_should_create_valid_inquiry(self):
        """Test creating inquiry with valid data."""
        # Arrange & Act
        inquiry = WorkflowInquiry(
            company_name="Test Corp",
            website="https://test.com",
            industry="Tech",
            prompt="Optimize workflow",
            tier=WorkflowTier.STANDARD
        )

        # Assert
        assert inquiry.company_name == "Test Corp"
        assert inquiry.tier == WorkflowTier.STANDARD

    def test_should_validate_website_url(self):
        """Test URL validation logic."""
        with pytest.raises(ValidationError, match="Invalid URL"):
            WorkflowInquiry(
                company_name="Test",
                website="not-a-url",
                industry="Tech",
                prompt="Test",
                tier=WorkflowTier.BUDGET
            )

    def test_should_reject_empty_prompt(self):
        """Test prompt validation."""
        with pytest.raises(ValidationError, match="Prompt cannot be empty"):
            WorkflowInquiry(
                company_name="Test",
                website="https://test.com",
                industry="Tech",
                prompt="",
                tier=WorkflowTier.BUDGET
            )

    def test_should_calculate_max_tokens_for_tier(self):
        """Test tier-based token calculation."""
        budget = WorkflowInquiry(..., tier=WorkflowTier.BUDGET)
        standard = WorkflowInquiry(..., tier=WorkflowTier.STANDARD)
        premium = WorkflowInquiry(..., tier=WorkflowTier.PREMIUM)

        assert budget.max_tokens == 1000
        assert standard.max_tokens == 2000
        assert premium.max_tokens == 4000
```

### Example: Pure Function Tests (Keep Current test_voter.py)

**Location:** `tests/unit/contexts/workflow/test_voter.py` (44 existing tests)

```python
# Already excellent - these are the model to follow
class TestConsensusVoter:
    """Tests for consensus voting logic."""

    def test_should_select_majority_response(self):
        """Test majority selection logic."""
        responses = [
            WorkflowResponse(content="Option A", score=0.9),
            WorkflowResponse(content="Option A", score=0.85),
            WorkflowResponse(content="Option B", score=0.7),
        ]

        result = ConsensusVoter.select_best(responses)

        assert result.content == "Option A"
        assert result.confidence > 0.8
```

### Unit Test Strategy

**Characteristics:**
- No network calls
- No file I/O
- No database
- No real external dependencies
- Run in <10ms per test
- 100% deterministic

**What to Mock:**
- Nothing (pure functions don't need mocks)
- If you need a mock, it's not a unit test

**Target:** 140 unit tests covering all business logic

## Layer 2: Integration Tests (20%)

### Philosophy
Validate **contracts with external services** and **component interactions**. Use a mix of contract tests (fast) and real service tests (comprehensive).

### Contract Testing Approach

**What is Contract Testing?**
Validate that our code correctly handles the **expected structure** of external API responses without making real calls. Uses recorded responses or schema validation.

### Contract Test Implementation

**Location:** `tests/integration/contracts/`

```python
# tests/integration/contracts/test_claude_contract.py
class TestClaudeAPIContract:
    """Contract tests for Claude API integration."""

    @pytest.fixture
    def claude_adapter(self):
        """Claude adapter with contract validation."""
        return ClaudeAdapter(api_key="test_key")

    @pytest.fixture
    def mock_claude_response(self):
        """Valid Claude API response structure."""
        return {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Workflow response"}],
            "model": "claude-sonnet-4-5",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 200
            }
        }

    def test_should_parse_valid_claude_response(self, claude_adapter, mock_claude_response):
        """Test parsing valid Claude response structure."""
        # Act
        parsed = claude_adapter._parse_response(mock_claude_response)

        # Assert
        assert parsed.content == "Workflow response"
        assert parsed.model == "claude-sonnet-4-5"
        assert parsed.usage.input_tokens == 100
        assert parsed.usage.output_tokens == 200

    def test_should_reject_malformed_response(self, claude_adapter):
        """Test handling of malformed response."""
        malformed = {"id": "123"}  # Missing required fields

        with pytest.raises(ContractViolationError):
            claude_adapter._parse_response(malformed)

    def test_should_handle_missing_usage_field(self, claude_adapter):
        """Test graceful handling of optional fields."""
        response = {
            "id": "msg_123",
            "content": [{"type": "text", "text": "Response"}],
            # Missing 'usage' field
        }

        parsed = claude_adapter._parse_response(response)
        assert parsed.usage is None  # Graceful degradation
```

### Service Tests (Component Integration)

**Location:** `tests/integration/services/`

Test how components work together without external dependencies.

```python
# tests/integration/services/test_workflow_engine_integration.py
class TestWorkflowEngineIntegration:
    """Integration tests for WorkflowEngine components."""

    @pytest.fixture
    def mock_ai_provider(self):
        """Mock AI provider with realistic responses."""
        return MockAIProvider(
            responses=[
                WorkflowResponse(content="Workflow A", score=0.9),
                WorkflowResponse(content="Workflow A", score=0.85),
                WorkflowResponse(content="Workflow B", score=0.7),
            ]
        )

    @pytest.fixture
    def workflow_engine(self, mock_ai_provider):
        """Workflow engine with mocked AI but real voter."""
        return WorkflowEngine(
            ai_provider=mock_ai_provider,
            voter=ConsensusVoter(),  # Real
            validator=QAValidator()   # Real
        )

    def test_should_integrate_ai_and_voter(self, workflow_engine):
        """Test AI provider → Voter → Result flow."""
        # Arrange
        inquiry = WorkflowInquiry(
            company_name="Test",
            website="https://test.com",
            industry="Tech",
            prompt="Test workflow",
            tier=WorkflowTier.STANDARD
        )

        # Act
        result = workflow_engine.process_inquiry(inquiry)

        # Assert
        assert result.selected_workflow.content == "Workflow A"
        assert result.consensus_score > 0.8
        assert len(result.all_responses) == 3
```

### Real Service Integration Tests (Subset)

**When to Use Real Services:**
- Daily/Nightly builds (not every commit)
- Pre-release validation
- Quarterly contract verification

**Location:** `tests/integration/real/`

```python
# tests/integration/real/test_claude_real.py
@pytest.mark.integration
@pytest.mark.slow
class TestClaudeRealIntegration:
    """Real Claude API tests (run nightly)."""

    def test_should_generate_real_workflow(self):
        """Smoke test with real Claude API."""
        # Minimal real API call to validate integration
        # Keep tokens low to minimize cost
        pass
```

### Integration Test Distribution

- **Contract Tests:** 25 tests (fast, run on every commit)
- **Service Tests:** 10 tests (component integration)
- **Real Service Tests:** 5 tests (smoke tests, run nightly)
- **Total:** 40 integration tests

## Layer 3: E2E Tests (10%)

### Philosophy
Validate **complete user workflows** with real services. These are expensive (time and money) so be selective.

### E2E Test Selection Criteria

Only create E2E tests for:
1. **Critical happy paths** (one per tier)
2. **Critical failure scenarios** (payment failure, email failure)
3. **Regression scenarios** (bugs that escaped to production)

### E2E Test Implementation

**Location:** `tests/e2e/`

```python
# tests/e2e/test_critical_workflows.py
@pytest.mark.e2e
@pytest.mark.slow
class TestCriticalWorkflows:
    """E2E tests for critical user workflows."""

    @pytest.fixture
    def real_workflow_engine(self):
        """Fully configured engine with real services."""
        return WorkflowEngine(
            ai_provider=ClaudeAdapter(),
            email_provider=GmailAdapter(),
            storage_provider=SheetsAdapter()
        )

    def test_standard_tier_happy_path(self, real_workflow_engine):
        """E2E test: Standard tier from inquiry to email delivery."""
        # Arrange
        inquiry = WorkflowInquiry(
            company_name="E2E Test Corp",
            website="https://e2etest.com",
            industry="E-commerce",
            prompt="Optimize checkout flow",
            tier=WorkflowTier.STANDARD
        )

        # Act
        result = real_workflow_engine.process_inquiry(inquiry)

        # Assert
        assert result.workflows is not None
        assert result.consensus_score > 0.7
        assert result.email_sent is True

        # Verify email delivery (check test inbox)
        # Verify QA logged to Sheets
```

### E2E Test Distribution

- **Happy Paths:** 6 tests (2 per tier)
- **Critical Failures:** 4 tests (payment, email, API timeout)
- **Regression:** 10 tests (bugs that escaped)
- **Total:** 20 E2E tests

## Test Execution Strategy

### Different Tests, Different Cadences

```
┌─────────────────────────────────────────────────────────┐
│  DEVELOPER LOCAL (Every save)                          │
│  - Unit tests only (140 tests)                         │
│  - Duration: <30 seconds                               │
│  - Purpose: Instant feedback                           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PR / COMMIT (Every commit)                            │
│  - Unit tests (140 tests)                              │
│  - Contract tests (25 tests)                           │
│  - Service tests (10 tests)                            │
│  - Duration: <2 minutes                                │
│  - Purpose: Pre-merge validation                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  MERGE TO MAIN (Every merge)                           │
│  - All unit tests (140 tests)                          │
│  - All integration tests (40 tests)                    │
│  - Smoke E2E (5 critical tests)                        │
│  - Duration: <5 minutes                                │
│  - Purpose: Main branch protection                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  NIGHTLY (Once per day)                                │
│  - All tests (200 tests)                               │
│  - Real service integration tests                      │
│  - Full E2E suite                                      │
│  - Duration: ~15 minutes                               │
│  - Purpose: Comprehensive validation                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PRE-RELEASE (Before deployment)                       │
│  - All tests (200 tests)                               │
│  - Extended E2E scenarios                              │
│  - Performance tests                                   │
│  - Load tests                                          │
│  - Duration: ~30 minutes                               │
│  - Purpose: Production readiness gate                  │
└─────────────────────────────────────────────────────────┘
```

### pytest Configuration

**File:** `pytest.ini`

```ini
[pytest]
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (contracts, services)
    contract: Contract tests (validate API structures)
    service: Service tests (component integration)
    real: Real service integration tests (slow, expensive)
    e2e: End-to-end tests (full workflows)
    slow: Slow tests (run nightly)

# Default: Run unit + contract + service tests
addopts = -v -m "unit or (integration and not real) or (not slow)"

# Parallel execution for speed
# addopts = -v -n auto
```

### Running Different Test Suites

```bash
# Local development (fast)
pytest -m unit

# Pre-commit (unit + contract + service)
pytest -m "unit or (integration and not real)"

# Full suite (including real services)
pytest

# Only E2E tests
pytest -m e2e

# Only contract tests
pytest -m contract

# Nightly (everything)
pytest --run-slow
```

## Implementation Roadmap

### Phase 1: Expand Unit Tests (Week 1)
**Goal:** Achieve 70% unit test coverage

1. **Expand domain model tests**
   - `test_models.py`: 30 tests
   - `test_prompts.py`: 20 tests
   - Add validation tests for all models

2. **Keep existing good tests**
   - `test_voter.py`: 44 tests (already excellent)

3. **Add validator unit tests**
   - `test_deterministic_validators.py`: 25 tests
   - `test_scoring.py`: 21 tests

**Deliverable:** 140 unit tests, all passing in <30 seconds

### Phase 2: Create Contract Tests (Week 2)
**Goal:** Validate external API contracts

1. **Create contract test infrastructure**
   - `tests/integration/contracts/` directory
   - Recorded response fixtures
   - Contract validation helpers

2. **Implement contract tests**
   - `test_claude_contract.py`: 10 tests
   - `test_gmail_contract.py`: 5 tests
   - `test_sheets_contract.py`: 5 tests
   - `test_stripe_contract.py`: 5 tests

**Deliverable:** 25 contract tests, fast execution (<1 min)

### Phase 3: Add Service Tests (Week 3)
**Goal:** Test component integration

1. **Create service test suite**
   - `test_workflow_engine_integration.py`: 5 tests
   - `test_qa_pipeline_integration.py`: 5 tests

**Deliverable:** 10 service tests validating component interactions

### Phase 4: Selective Real Service Tests (Week 3)
**Goal:** Smoke tests with real APIs

1. **Create real service test infrastructure**
   - Test credentials setup
   - Test environment configuration

2. **Implement minimal real tests**
   - `test_claude_real.py`: 2 smoke tests
   - `test_gmail_real.py`: 1 smoke test
   - `test_sheets_real.py`: 1 smoke test
   - `test_stripe_real.py`: 1 smoke test

**Deliverable:** 5 real service smoke tests (run nightly)

### Phase 5: Critical E2E Tests (Week 4)
**Goal:** Validate critical user workflows

1. **Implement happy path E2E**
   - Budget tier: 2 tests
   - Standard tier: 2 tests
   - Premium tier: 2 tests

2. **Implement failure scenario E2E**
   - Payment failure: 2 tests
   - Email failure: 2 tests

3. **Add regression E2E**
   - Historical bugs: 10 tests

**Deliverable:** 20 E2E tests covering critical paths

### Phase 6: Optimize Execution (Week 5)
**Goal:** Fast feedback, efficient CI/CD

1. **Configure test markers**
   - pytest.ini configuration
   - CI/CD pipeline stages

2. **Implement parallel execution**
   - pytest-xdist setup
   - Optimize test independence

3. **Add caching**
   - Cache contract test fixtures
   - Cache expensive setup

**Deliverable:** <2 min PR builds, <5 min main builds

## Cost Management

### API Cost Analysis

**Unit Tests:** $0 (no API calls)
**Contract Tests:** $0 (recorded responses)
**Service Tests:** $0 (mocked external services)
**Real Service Tests:** ~$0.50/run (minimal smoke tests)
**E2E Tests:** ~$2/run (20 real workflow tests)

**Daily Costs:**
- Local dev: $0
- PR builds (10/day): $0
- Main merges (5/day): $2.50 (5 smoke tests × $0.50)
- Nightly (1/day): $2.50 (full E2E suite)

**Total: ~$5/day or $150/month**

### Cost vs Integration-First Approach

- **Integration-First:** $90/month (higher API usage)
- **Layered Strategy:** $150/month (more comprehensive E2E)
- **Trade-off:** Spend extra $60/month for faster feedback loops

## Success Metrics

### Test Quality Metrics

1. **Test Validity Score:** 8.5/10 (up from 5/10)
   - 70% pure unit tests (perfect validity)
   - 20% contract + service tests (high validity)
   - 10% E2E tests (perfect validity)

2. **Test Speed:**
   - Unit tests: <30 seconds
   - PR builds: <2 minutes
   - Main builds: <5 minutes
   - Nightly: <15 minutes

3. **Coverage:**
   - Unit test coverage: 90%+ (business logic)
   - Integration coverage: 100% (all external contracts)
   - E2E coverage: Critical paths only

### Developer Experience Metrics

1. **Local Feedback:** <30 seconds (unit tests only)
2. **PR Feedback:** <2 minutes (unit + contract + service)
3. **Merge Confidence:** High (smoke tests validate integration)
4. **Nightly Validation:** Comprehensive (catches edge cases)

### Reliability Metrics

1. **Test Flakiness:** <0.5% (deterministic unit/contract tests)
2. **False Positive Rate:** <2% (contract tests validate structure)
3. **False Negative Rate:** <1% (E2E catches integration issues)

## Risk Mitigation

### Risk 1: Slow Feedback Loop
**Mitigation:**
- 70% unit tests run instantly (<30s)
- Contract tests run fast (<1min)
- Real tests only on nightly/pre-release

### Risk 2: Contract Drift
**Mitigation:**
- Nightly real service tests validate contracts
- Quarterly manual contract review
- Alert on contract test failures

### Risk 3: Insufficient E2E Coverage
**Mitigation:**
- Critical path coverage mandatory
- Regression tests for escaped bugs
- Quarterly review of E2E test adequacy

### Risk 4: Test Maintenance Burden
**Mitigation:**
- Unit tests are simple (pure functions)
- Contract tests use recorded fixtures (stable)
- E2E tests limited to critical paths only

## Comparison to Current State

### Current (5/10 Validity)
- 86 tests, mixed quality
- 60% use mocks inappropriately
- Slow feedback (all tests run together)
- No layering strategy

### Proposed (8.5/10 Validity)
- 200 tests, well-organized layers
- 70% pure unit tests (fast, valid)
- 20% contract tests (fast, validates structure)
- 10% E2E tests (slow, validates behavior)
- Fast feedback (<30s local, <2min PR)
- Comprehensive nightly validation

## Conclusion

The layered testing strategy balances **speed and confidence** through intelligent test distribution. Developers get instant feedback from unit tests, contracts prevent API breakage, and E2E tests validate critical workflows. This approach is sustainable, scalable, and provides high confidence without sacrificing velocity.

**Key Principle:** Different tests, different purposes, different cadences.
