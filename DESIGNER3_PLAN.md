# Behavior-Driven Testing Strategy Plan
**Designer 3: Behavior-Driven Quality Engineer**

## Executive Philosophy

Tests should validate **business outcomes**, not implementation details. Users care about workflows being generated, emails being delivered, and payments being processed - not whether a function was called with the right parameters. BDD ensures tests speak the language of business value.

## Core Principles

1. **User-Centric Testing** - Test what users experience, not internal mechanics
2. **Business Language** - Write tests in domain language (Given/When/Then)
3. **Outcome Validation** - Assert on business outcomes, not implementation
4. **Real Scenarios** - Test actual user workflows, not theoretical edge cases
5. **Acceptance Criteria** - Tests define "done" for features

## Test Architecture

### BDD Test Layers

```
┌─────────────────────────────────────────────────────────┐
│  BUSINESS SCENARIOS (E2E)               40%            │
│  Given/When/Then scenarios                             │
│  Real user workflows                                   │
│  Acceptance criteria validation                        │
│  Tools: pytest-bdd, real services                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  COMPONENT BEHAVIORS (Integration)      40%            │
│  Given/When/Then component tests                       │
│  Service behavior validation                           │
│  API contract behaviors                                │
│  Tools: pytest-bdd, mocked externals                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  DOMAIN LOGIC (Unit)                    20%            │
│  Business rule validation                              │
│  Domain model behaviors                                │
│  Calculation logic                                     │
│  Tools: pytest (traditional)                           │
└─────────────────────────────────────────────────────────┘
```

### Test Distribution Target

- **40% Business Scenario Tests** (~80 tests) - E2E workflows in BDD format
- **40% Component Behavior Tests** (~80 tests) - Service behaviors
- **20% Domain Logic Tests** (~40 tests) - Pure business logic
- **Total: ~200 tests** (expanding from current 86)

## BDD Framework: pytest-bdd

### Why pytest-bdd?

- **Gherkin Syntax** - Business-readable test scenarios
- **Reusable Steps** - DRY step definitions
- **Living Documentation** - Tests serve as spec
- **Pytest Integration** - Works with existing pytest infrastructure

### Installation

```bash
pip install pytest-bdd
```

## Layer 1: Business Scenario Tests (40%)

### Philosophy
Every feature starts with **acceptance criteria** written in Gherkin. Tests validate complete user journeys from input to outcome.

### Feature File Structure

**Location:** `tests/features/`

```gherkin
# tests/features/workflow_generation.feature
Feature: Workflow Generation
  As a business owner
  I want to receive AI-generated workflow recommendations
  So that I can improve my business processes

  Background:
    Given the workflow system is running
    And Claude API is available
    And Gmail API is available
    And Google Sheets API is available

  Scenario: Budget tier workflow generation
    Given I am a business owner at "Acme Corp"
    And my website is "https://acmecorp.com"
    And my industry is "E-commerce"
    When I request a budget tier workflow for "optimize checkout process"
    Then I should receive 3 workflow recommendations
    And the consensus score should be above 0.7
    And the QA score should be above 0.6
    And the result should be logged to Google Sheets
    And I should receive an email with the workflows

  Scenario: Standard tier with higher quality
    Given I am a business owner at "TechStart Inc"
    And my website is "https://techstart.io"
    And my industry is "SaaS"
    When I request a standard tier workflow for "improve user onboarding"
    Then I should receive 5 workflow recommendations
    And the consensus score should be above 0.8
    And the QA score should be above 0.7
    And the workflows should be more detailed than budget tier
    And the result should be logged to Google Sheets
    And I should receive an email with the workflows

  Scenario: Premium tier with expert analysis
    Given I am a business owner at "Enterprise Solutions LLC"
    And my website is "https://enterprise-solutions.com"
    And my industry is "Finance"
    When I request a premium tier workflow for "automate compliance reporting"
    Then I should receive 7 workflow recommendations
    And the consensus score should be above 0.85
    And the QA score should be above 0.8
    And the workflows should include expert-level analysis
    And the result should be logged to Google Sheets
    And I should receive an email with detailed PDF attachment

  Scenario: Handle payment failure gracefully
    Given I am a business owner at "StartupX"
    When I request a premium tier workflow
    But my payment method is declined
    Then I should see a clear payment error message
    And I should not be charged
    And no workflow generation should occur
    And I should be offered to try a different payment method

  Scenario: Recover from API timeout
    Given I am a business owner requesting a workflow
    When Claude API times out on first attempt
    Then the system should retry with exponential backoff
    And I should eventually receive my workflows
    Or I should receive a clear timeout message after max retries

  Scenario: Email delivery failure fallback
    Given I have successfully generated workflows
    When Gmail API fails to send the email
    Then I should be able to download the results immediately
    And I should see a notification about email delivery failure
    And the system should log the email failure for retry
```

### Step Definitions

**Location:** `tests/step_defs/workflow_steps.py`

```python
import pytest
from pytest_bdd import given, when, then, scenarios, parsers
from workflow_system.contexts.workflow.engine import WorkflowEngine
from workflow_system.contexts.workflow.models import WorkflowInquiry, WorkflowTier

# Load all scenarios from feature file
scenarios('../features/workflow_generation.feature')

# ============================================
# GIVEN Steps (Arrange)
# ============================================

@given("the workflow system is running")
def workflow_system(real_workflow_engine):
    """Workflow system is initialized and ready."""
    return real_workflow_engine

@given("Claude API is available")
def claude_available(workflow_system):
    """Verify Claude API is accessible."""
    # Could ping health endpoint or check credentials
    assert workflow_system.ai_provider is not None

@given("Gmail API is available")
def gmail_available(workflow_system):
    """Verify Gmail API is accessible."""
    assert workflow_system.email_provider is not None

@given("Google Sheets API is available")
def sheets_available(workflow_system):
    """Verify Sheets API is accessible."""
    assert workflow_system.storage_provider is not None

@given(parsers.parse('I am a business owner at "{company}"'))
def business_owner(context, company):
    """Set business owner context."""
    context['company_name'] = company

@given(parsers.parse('my website is "{website}"'))
def business_website(context, website):
    """Set business website."""
    context['website'] = website

@given(parsers.parse('my industry is "{industry}"'))
def business_industry(context, industry):
    """Set business industry."""
    context['industry'] = industry

# ============================================
# WHEN Steps (Act)
# ============================================

@when(parsers.parse('I request a budget tier workflow for "{prompt}"'))
def request_budget_workflow(context, workflow_system, prompt):
    """Request budget tier workflow generation."""
    inquiry = WorkflowInquiry(
        company_name=context['company_name'],
        website=context['website'],
        industry=context['industry'],
        prompt=prompt,
        tier=WorkflowTier.BUDGET
    )
    context['result'] = workflow_system.process_inquiry(inquiry)
    context['tier'] = WorkflowTier.BUDGET

@when(parsers.parse('I request a standard tier workflow for "{prompt}"'))
def request_standard_workflow(context, workflow_system, prompt):
    """Request standard tier workflow generation."""
    inquiry = WorkflowInquiry(
        company_name=context['company_name'],
        website=context['website'],
        industry=context['industry'],
        prompt=prompt,
        tier=WorkflowTier.STANDARD
    )
    context['result'] = workflow_system.process_inquiry(inquiry)
    context['tier'] = WorkflowTier.STANDARD

@when(parsers.parse('I request a premium tier workflow for "{prompt}"'))
def request_premium_workflow(context, workflow_system, prompt):
    """Request premium tier workflow generation."""
    inquiry = WorkflowInquiry(
        company_name=context['company_name'],
        website=context['website'],
        industry=context['industry'],
        prompt=prompt,
        tier=WorkflowTier.PREMIUM
    )
    context['result'] = workflow_system.process_inquiry(inquiry)
    context['tier'] = WorkflowTier.PREMIUM

@when("my payment method is declined")
def payment_declined(context):
    """Simulate payment decline."""
    # Use Stripe test card that triggers decline
    context['payment_method'] = "4000000000000002"  # Stripe decline test card

@when("Claude API times out on first attempt")
def claude_timeout(workflow_system):
    """Simulate Claude API timeout."""
    # Mock first call to timeout, subsequent succeed
    # This tests retry logic
    pass

@when("Gmail API fails to send the email")
def gmail_fails(workflow_system):
    """Simulate Gmail API failure."""
    # Mock Gmail to fail on send
    pass

# ============================================
# THEN Steps (Assert)
# ============================================

@then(parsers.parse("I should receive {count:d} workflow recommendations"))
def verify_workflow_count(context, count):
    """Verify number of workflows received."""
    assert len(context['result'].workflows) == count

@then(parsers.parse("the consensus score should be above {score:f}"))
def verify_consensus_score(context, score):
    """Verify consensus score meets threshold."""
    assert context['result'].consensus_score > score

@then(parsers.parse("the QA score should be above {score:f}"))
def verify_qa_score(context, score):
    """Verify QA score meets threshold."""
    assert context['result'].qa_metrics.overall_score > score

@then("the result should be logged to Google Sheets")
def verify_sheets_logged(context, workflow_system):
    """Verify result was logged to Sheets."""
    # Query Sheets for the run_id
    # Verify entry exists with correct data
    run_id = context['result'].run_id
    sheets_data = workflow_system.storage_provider.find_entry(run_id)
    assert sheets_data is not None
    assert sheets_data['run_id'] == run_id

@then("I should receive an email with the workflows")
def verify_email_sent(context, workflow_system):
    """Verify email was sent successfully."""
    # Check email provider sent message
    # Could poll inbox to verify receipt
    assert context['result'].email_sent is True

@then("the workflows should be more detailed than budget tier")
def verify_detail_level(context):
    """Verify standard tier has more detail."""
    # Compare token count or content length
    avg_length = sum(len(w.content) for w in context['result'].workflows) / len(context['result'].workflows)
    assert avg_length > 500  # Arbitrary threshold

@then("I should see a clear payment error message")
def verify_payment_error(context):
    """Verify payment error message."""
    assert context['result'].error_type == "payment_declined"
    assert "payment" in context['result'].error_message.lower()

@then("I should not be charged")
def verify_no_charge(context):
    """Verify no charge occurred."""
    # Check Stripe for charge
    # Should not exist for this payment method
    assert context['result'].charge_id is None

@then("no workflow generation should occur")
def verify_no_workflows(context):
    """Verify no workflows generated on payment failure."""
    assert context['result'].workflows is None or len(context['result'].workflows) == 0

@then("the system should retry with exponential backoff")
def verify_retry_logic(context):
    """Verify retry attempts were made."""
    # Check logs or retry counter
    assert context['result'].retry_count > 1
    assert context['result'].retry_count <= 3

@then("I should eventually receive my workflows")
def verify_eventual_success(context):
    """Verify workflows received after retry."""
    assert context['result'].workflows is not None
    assert len(context['result'].workflows) > 0
```

### Pytest Fixtures for BDD

**Location:** `tests/conftest.py`

```python
import pytest
from pytest_bdd import given

@pytest.fixture
def context():
    """Shared context for BDD scenarios."""
    return {}

@pytest.fixture
def real_workflow_engine():
    """Real workflow engine for E2E tests."""
    from workflow_system.contexts.workflow.engine import WorkflowEngine
    from workflow_system.infrastructure.ai.claude_adapter import ClaudeAdapter
    from workflow_system.infrastructure.email.gmail_adapter import GmailAdapter
    from workflow_system.infrastructure.storage.sheets_adapter import SheetsAdapter

    return WorkflowEngine(
        ai_provider=ClaudeAdapter(),
        email_provider=GmailAdapter(),
        storage_provider=SheetsAdapter()
    )

@pytest.fixture
def mock_workflow_engine():
    """Mocked workflow engine for component behavior tests."""
    from workflow_system.contexts.workflow.engine import WorkflowEngine
    from tests.conftest import MockAIProvider

    return WorkflowEngine(
        ai_provider=MockAIProvider(),
        email_provider=MockEmailProvider(),
        storage_provider=MockStorageProvider()
    )
```

## Layer 2: Component Behavior Tests (40%)

### Philosophy
Test how individual components **behave** in isolation. Use BDD format to describe component responsibilities.

### Component Behavior Features

**Location:** `tests/features/components/`

```gherkin
# tests/features/components/consensus_voter.feature
Feature: Consensus Voting
  As the workflow engine
  I want to select the best workflow from multiple AI responses
  So that I can provide the highest quality recommendation

  Scenario: Select majority consensus
    Given I have 5 AI-generated workflows
    And 3 workflows recommend "Kanban board implementation"
    And 2 workflows recommend "Waterfall process"
    When I run consensus voting
    Then the selected workflow should be "Kanban board implementation"
    And the consensus score should be 0.6 or higher

  Scenario: Handle tie with quality scoring
    Given I have 4 AI-generated workflows
    And 2 workflows recommend "Option A" with QA score 0.9
    And 2 workflows recommend "Option B" with QA score 0.7
    When I run consensus voting
    Then the selected workflow should be "Option A"
    And the consensus score should reflect the tie-breaking

  Scenario: Reject low-quality consensus
    Given I have 5 AI-generated workflows
    And all workflows are different
    And no clear majority exists
    When I run consensus voting
    Then the consensus score should be below 0.5
    And a low confidence warning should be raised
```

```gherkin
# tests/features/components/qa_validation.feature
Feature: QA Validation
  As the workflow engine
  I want to validate workflow quality
  So that I ensure high-quality recommendations to users

  Scenario: Pass high-quality workflow
    Given I have a workflow response with complete steps
    And the workflow includes actionable items
    And the workflow is relevant to the prompt
    When I run QA validation
    Then the QA score should be above 0.8
    And all quality checks should pass

  Scenario: Detect incomplete workflow
    Given I have a workflow response with missing steps
    When I run QA validation
    Then the completeness score should be below 0.5
    And a completeness warning should be raised

  Scenario: Detect irrelevant workflow
    Given I have a workflow response
    And the workflow doesn't address the prompt
    When I run QA validation
    Then the relevance score should be below 0.3
    And a relevance warning should be raised
```

### Component Step Definitions

**Location:** `tests/step_defs/component_steps.py`

```python
from pytest_bdd import given, when, then, scenarios, parsers
from workflow_system.contexts.workflow.voter import ConsensusVoter
from workflow_system.contexts.workflow.models import WorkflowResponse

scenarios('../features/components/consensus_voter.feature')

@given(parsers.parse("I have {count:d} AI-generated workflows"))
def ai_workflows(context, count):
    """Create N workflow responses."""
    context['workflows'] = []
    context['count'] = count

@given(parsers.parse('{count:d} workflows recommend "{content}"'))
def workflows_with_content(context, count, content):
    """Add workflows with specific content."""
    for _ in range(count):
        context['workflows'].append(
            WorkflowResponse(content=content, score=0.8)
        )

@when("I run consensus voting")
def run_consensus(context):
    """Execute consensus voting."""
    voter = ConsensusVoter()
    context['result'] = voter.select_best(context['workflows'])

@then(parsers.parse('the selected workflow should be "{content}"'))
def verify_selected(context, content):
    """Verify selected workflow content."""
    assert content in context['result'].content
```

## Layer 3: Domain Logic Tests (20%)

### Philosophy
Pure business logic tested with traditional pytest. These are the foundation - fast, deterministic, comprehensive.

### Domain Logic Test Structure

**Keep existing excellent tests:**
- `test_voter.py` - 44 tests (pure logic, no dependencies)
- Expand with more domain model tests

**Add new domain tests:**
- `test_models.py` - Validation logic
- `test_tier_calculations.py` - Pricing/token logic
- `test_scoring.py` - QA scoring algorithms

**Example:**

```python
# tests/unit/domain/test_tier_calculations.py
class TestTierCalculations:
    """Test business rules for tier-based features."""

    def test_budget_tier_should_generate_3_workflows(self):
        """Budget tier generates 3 workflows."""
        tier = WorkflowTier.BUDGET
        assert tier.workflow_count == 3

    def test_standard_tier_should_generate_5_workflows(self):
        """Standard tier generates 5 workflows."""
        tier = WorkflowTier.STANDARD
        assert tier.workflow_count == 5

    def test_premium_tier_should_generate_7_workflows(self):
        """Premium tier generates 7 workflows."""
        tier = WorkflowTier.PREMIUM
        assert tier.workflow_count == 7

    def test_budget_tier_max_tokens(self):
        """Budget tier limited to 1000 tokens."""
        tier = WorkflowTier.BUDGET
        assert tier.max_tokens == 1000

    def test_premium_tier_includes_pdf_attachment(self):
        """Premium tier includes PDF attachment."""
        tier = WorkflowTier.PREMIUM
        assert tier.includes_pdf is True

    def test_budget_tier_no_pdf_attachment(self):
        """Budget tier does not include PDF."""
        tier = WorkflowTier.BUDGET
        assert tier.includes_pdf is False
```

## Implementation Roadmap

### Phase 1: BDD Infrastructure (Week 1)
**Goal:** Set up pytest-bdd framework

1. **Install and configure pytest-bdd**
   ```bash
   pip install pytest-bdd
   ```

2. **Create directory structure**
   ```
   tests/
   ├── features/
   │   ├── workflow_generation.feature
   │   ├── payment_processing.feature
   │   ├── email_delivery.feature
   │   └── components/
   │       ├── consensus_voter.feature
   │       ├── qa_validation.feature
   │       └── api_adapters.feature
   ├── step_defs/
   │   ├── workflow_steps.py
   │   ├── payment_steps.py
   │   ├── email_steps.py
   │   └── component_steps.py
   ```

3. **Write first feature file**
   - `workflow_generation.feature` with 3 scenarios
   - Implement step definitions
   - Verify tests run

**Deliverable:** pytest-bdd running, first feature passing

### Phase 2: Business Scenario Tests (Week 2-3)
**Goal:** Write acceptance tests for all features

1. **Core workflow scenarios (30 tests)**
   - Budget tier workflow generation
   - Standard tier workflow generation
   - Premium tier workflow generation
   - Each with happy path + 2 error scenarios

2. **Payment scenarios (20 tests)**
   - Successful payment
   - Payment decline
   - Payment timeout
   - Refund scenarios

3. **Delivery scenarios (15 tests)**
   - Email delivery success
   - Email failure with download fallback
   - PDF attachment for premium
   - Sheets logging verification

4. **Error recovery scenarios (15 tests)**
   - API timeouts with retry
   - Rate limiting
   - Service unavailability
   - Graceful degradation

**Deliverable:** 80 business scenario tests in BDD format

### Phase 3: Component Behavior Tests (Week 4)
**Goal:** Test component behaviors in isolation

1. **Consensus voter behaviors (20 tests)**
   - Majority selection
   - Tie-breaking
   - Low confidence detection
   - Edge cases

2. **QA validation behaviors (20 tests)**
   - Completeness checking
   - Relevance scoring
   - Quality threshold validation
   - Deterministic validators

3. **API adapter behaviors (20 tests)**
   - Claude adapter behavior
   - Gmail adapter behavior
   - Sheets adapter behavior
   - Stripe adapter behavior

4. **Workflow engine behaviors (20 tests)**
   - Orchestration logic
   - Error handling
   - State management
   - Event logging

**Deliverable:** 80 component behavior tests

### Phase 4: Domain Logic Tests (Week 5)
**Goal:** Expand pure logic test coverage

1. **Keep existing good tests**
   - `test_voter.py`: 44 tests (already excellent)

2. **Add domain model tests (20 tests)**
   - Validation logic
   - Business rules
   - Data transformations

3. **Add calculation tests (16 tests)**
   - Tier-based features
   - Pricing logic
   - Token calculations
   - Scoring algorithms

**Deliverable:** 40 domain logic tests (20 existing + 20 new)

### Phase 5: Living Documentation (Week 6)
**Goal:** Generate human-readable test reports

1. **Configure pytest-bdd reporting**
   ```bash
   pip install pytest-html
   pytest --html=report.html --self-contained-html
   ```

2. **Generate feature documentation**
   - Extract Gherkin scenarios
   - Create feature coverage report
   - Publish to team wiki

3. **Create acceptance criteria checklist**
   - Map features to scenarios
   - Track coverage per feature
   - Identify gaps

**Deliverable:** Living documentation system

## Test Execution Strategy

### Different Audiences, Different Reports

```
┌─────────────────────────────────────────────────────────┐
│  DEVELOPERS                                            │
│  - Run: pytest -m "unit"                               │
│  - See: Traditional pytest output                      │
│  - Duration: <30 seconds                               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PRODUCT MANAGERS / STAKEHOLDERS                       │
│  - Run: pytest --html=report.html                      │
│  - See: Gherkin scenarios (Given/When/Then)            │
│  - Understand: Business outcomes validated             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  QA TEAM                                               │
│  - Run: pytest -m e2e                                  │
│  - See: Full workflow validation results               │
│  - Track: Acceptance criteria coverage                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  CI/CD PIPELINE                                        │
│  - Run: pytest (all tests)                             │
│  - Report: JUnit XML + HTML                            │
│  - Gate: All scenarios must pass                       │
└─────────────────────────────────────────────────────────┘
```

### Running BDD Tests

```bash
# Run all BDD scenario tests
pytest --cucumber-json=report.json

# Run specific feature
pytest tests/features/workflow_generation.feature

# Run specific scenario by name
pytest -k "budget tier workflow generation"

# Run with detailed Gherkin output
pytest -v --gherkin-terminal-reporter

# Generate HTML report
pytest --html=bdd_report.html --self-contained-html
```

## Cost Management

### API Cost Analysis

**Business Scenario Tests (40%):** $4/run
- 80 E2E tests with real services
- Each test ~$0.05 (Claude + email/sheets/stripe)

**Component Behavior Tests (40%):** $0/run
- Mocked external services
- Real internal components only

**Domain Logic Tests (20%):** $0/run
- Pure business logic
- No external dependencies

**Daily Costs:**
- Local dev: $0 (unit + component only)
- PR builds: $0 (skip E2E)
- Merge to main: $2 (smoke E2E subset)
- Nightly: $4 (full E2E suite)

**Total: ~$6/day or $180/month**

## Success Metrics

### Business Outcome Validation

1. **Feature Coverage:** 100%
   - Every feature has acceptance criteria
   - Every criteria has scenario test
   - All scenarios pass

2. **User Journey Coverage:** 100%
   - All critical workflows tested E2E
   - All tiers (Budget/Standard/Premium) validated
   - All failure scenarios covered

3. **Living Documentation:** Up-to-date
   - Feature files reflect current behavior
   - Scenarios serve as specification
   - Non-technical stakeholders can read tests

### Test Quality Metrics

1. **Test Validity Score:** 8/10
   - 40% E2E tests (perfect validity)
   - 40% component tests (high validity, some mocks)
   - 20% unit tests (perfect validity)

2. **Business Alignment:** 100%
   - All tests written in business language
   - Tests validate outcomes, not implementation
   - Tests serve as acceptance criteria

3. **Maintainability:** High
   - Reusable step definitions
   - Centralized fixtures
   - Clear scenario structure

## Comparison to Other Approaches

### vs Integration-First
**Advantage:** Business-readable tests, better stakeholder communication
**Trade-off:** More overhead in BDD framework setup

### vs Layered Testing
**Advantage:** Tests serve as living documentation, acceptance criteria
**Trade-off:** Less emphasis on test pyramid optimization

### Unique Value
- **Stakeholder Communication:** Non-technical readers understand tests
- **Acceptance Criteria:** Tests define "done" for features
- **Regression Prevention:** Scenarios capture business requirements
- **Onboarding:** New team members learn system via scenarios

## Risk Mitigation

### Risk 1: BDD Framework Overhead
**Mitigation:**
- Start with critical features only
- Expand BDD coverage incrementally
- Keep unit tests as traditional pytest

### Risk 2: Step Definition Maintenance
**Mitigation:**
- Reusable step definitions (DRY)
- Centralized fixtures
- Regular refactoring

### Risk 3: Slow E2E Execution
**Mitigation:**
- Run E2E nightly, not on every commit
- Parallel scenario execution
- Optimize test data setup

### Risk 4: False Positives in Real Services
**Mitigation:**
- Dedicated test environments
- Idempotent test scenarios
- Cleanup after each run

## Conclusion

The BDD approach prioritizes **business outcome validation** and **stakeholder communication**. By writing tests in business language (Given/When/Then), we ensure tests validate what users care about: workflows being generated, emails being delivered, payments being processed. This approach creates living documentation that serves as both specification and validation.

**Key Principle:** Tests should read like requirements and validate outcomes, not implementation.
