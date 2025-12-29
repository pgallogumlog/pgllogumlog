# Integration-First Testing Architecture Plan
**Designer 1: Integration-First Architect**

## Executive Philosophy

Real systems fail at integration boundaries. Mocks give false confidence. We must test with actual services to validate real behavior, contracts, and error conditions.

## Core Principles

1. **Integration tests are the foundation** - They catch real bugs that unit tests miss
2. **Minimize mocks** - Use real services in CI/CD with test credentials
3. **Fail fast on broken contracts** - If external APIs change, we know immediately
4. **Cost is an investment** - Paying for API calls in tests prevents production incidents

## Test Architecture

### Primary Test Layers (Inverted Pyramid)

```
┌─────────────────────────────────────────┐
│  E2E Tests (20%)                        │  Full workflow validation
│  - Real Claude, Gmail, Sheets, Stripe  │
│  - User scenarios end-to-end            │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  Integration Tests (60%)                │  Service contract validation
│  - Real API calls                       │
│  - Error scenario testing               │
│  - Performance validation               │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  Unit Tests (20%)                       │  Pure logic only
│  - Domain models                        │
│  - Calculations (voter.py model)        │
│  - No external dependencies             │
└─────────────────────────────────────────┘
```

### Test Distribution Target

- **60% Integration Tests** (~120 tests) - Real API validation
- **20% E2E Tests** (~40 tests) - Full workflow scenarios
- **20% Unit Tests** (~40 tests) - Pure logic (like test_voter.py)
- **Total: ~200 tests** (expanding from current 86)

## Integration Test Strategy

### 1. Real Claude API Integration Tests

**Location:** `tests/integration/infrastructure/test_claude_real.py`

```python
# Example structure
class TestClaudeRealIntegration:
    """Real Claude API integration tests."""

    @pytest.fixture
    def real_claude(self):
        """Real Claude client with test API key."""
        return ClaudeAdapter(api_key=os.getenv("ANTHROPIC_TEST_API_KEY"))

    def test_should_generate_workflow_with_real_api(self, real_claude):
        """Validate real Claude API generates valid workflow."""
        # Arrange
        prompt = "Simple test workflow for e-commerce checkout"

        # Act
        response = real_claude.generate_completion(
            prompt=prompt,
            temperature=0.7,
            max_tokens=500
        )

        # Assert
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model == "claude-sonnet-4-5"
        assert response.usage.input_tokens > 0
        assert response.usage.output_tokens > 0

    def test_should_handle_rate_limit_with_retry(self, real_claude):
        """Test rate limit handling and retry logic."""
        # Make rapid requests to trigger rate limit
        # Validate exponential backoff works
        pass

    def test_should_fail_on_invalid_api_key(self):
        """Test authentication failure handling."""
        invalid_client = ClaudeAdapter(api_key="invalid_key")
        with pytest.raises(AuthenticationError):
            invalid_client.generate_completion("test")

    def test_should_timeout_on_long_request(self, real_claude):
        """Test timeout handling for slow responses."""
        # Set aggressive timeout
        # Validate timeout exception raised
        pass
```

**Cost Management:**
- Use minimum token limits in tests (500 max_tokens)
- Cache responses for repeated scenarios
- Run full suite nightly, subset on PR
- Budget: ~$5/day for continuous testing

### 2. Real Gmail Integration Tests

**Location:** `tests/integration/infrastructure/test_gmail_real.py`

```python
class TestGmailRealIntegration:
    """Real Gmail API integration tests."""

    @pytest.fixture
    def real_gmail(self):
        """Real Gmail client with test account."""
        return GmailAdapter(
            credentials_path=os.getenv("GMAIL_TEST_CREDENTIALS_PATH")
        )

    @pytest.fixture
    def test_email_recipient(self):
        """Test email address (test Gmail account)."""
        return "workflow-test@example.com"

    def test_should_send_email_with_real_api(self, real_gmail, test_email_recipient):
        """Validate real email sending."""
        # Arrange
        subject = f"Test Email {uuid.uuid4()}"
        body = "This is a test email from integration tests"

        # Act
        message_id = real_gmail.send_email(
            to=test_email_recipient,
            subject=subject,
            body=body
        )

        # Assert
        assert message_id is not None

        # Verify email received (poll inbox)
        time.sleep(5)  # Allow delivery time
        received = real_gmail.search_messages(
            query=f"subject:{subject}"
        )
        assert len(received) == 1
        assert received[0].id == message_id

    def test_should_send_email_with_attachment(self, real_gmail):
        """Test email with PDF attachment."""
        # Create test PDF
        # Send via Gmail
        # Verify attachment received correctly
        pass

    def test_should_handle_invalid_recipient(self, real_gmail):
        """Test error handling for invalid email addresses."""
        with pytest.raises(InvalidRecipientError):
            real_gmail.send_email(
                to="invalid@",
                subject="test",
                body="test"
            )
```

**Reliability Strategy:**
- Use dedicated test Gmail account
- Clean up test emails after each run
- Verify delivery via API polling

### 3. Real Google Sheets Integration Tests

**Location:** `tests/integration/infrastructure/test_sheets_real.py`

```python
class TestSheetsRealIntegration:
    """Real Google Sheets API integration tests."""

    @pytest.fixture
    def real_sheets(self):
        """Real Sheets client with test credentials."""
        return SheetsAdapter(
            credentials_path=os.getenv("SHEETS_TEST_CREDENTIALS_PATH")
        )

    @pytest.fixture
    def test_spreadsheet_id(self):
        """Dedicated test spreadsheet ID."""
        return os.getenv("SHEETS_TEST_SPREADSHEET_ID")

    def test_should_write_qa_log_entry(self, real_sheets, test_spreadsheet_id):
        """Validate writing QA log entries."""
        # Arrange
        qa_entry = {
            "run_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "tier": "standard",
            "score": 0.95,
            "prompt_tokens": 1234,
            "completion_tokens": 567
        }

        # Act
        row_number = real_sheets.append_row(
            spreadsheet_id=test_spreadsheet_id,
            range="QA_Log!A:G",
            values=[qa_entry.values()]
        )

        # Assert
        assert row_number > 0

        # Verify data written correctly
        read_back = real_sheets.read_row(
            spreadsheet_id=test_spreadsheet_id,
            range=f"QA_Log!A{row_number}:G{row_number}"
        )
        assert read_back[0][0] == qa_entry["run_id"]
```

### 4. Real Stripe Integration Tests

**Location:** `tests/integration/infrastructure/test_stripe_real.py`

```python
class TestStripeRealIntegration:
    """Real Stripe API integration tests (test mode)."""

    @pytest.fixture
    def real_stripe(self):
        """Real Stripe client in test mode."""
        return stripe.api_key = os.getenv("STRIPE_TEST_SECRET_KEY")

    def test_should_create_payment_intent(self, real_stripe):
        """Validate payment intent creation."""
        # Arrange
        amount = 2999  # $29.99

        # Act
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            metadata={"tier": "premium"}
        )

        # Assert
        assert intent.id.startswith("pi_")
        assert intent.amount == amount
        assert intent.status == "requires_payment_method"

    def test_should_confirm_payment_with_test_card(self):
        """Test successful payment with test card."""
        # Use Stripe test card 4242424242424242
        # Create and confirm payment intent
        # Validate success status
        pass

    def test_should_handle_card_decline(self):
        """Test declined card handling."""
        # Use Stripe test card 4000000000000002 (decline)
        # Validate proper error handling
        pass
```

**Test Mode Strategy:**
- Always use Stripe test mode API keys
- Use Stripe test cards for scenarios
- No real money charged

## Error Scenario Coverage

### Critical Error Tests to Add

1. **Network Failures**
   - Timeout errors (slow Claude API response)
   - Connection refused (service down)
   - DNS resolution failures

2. **API Rate Limits**
   - Claude API rate limit (429 responses)
   - Gmail API quota exceeded
   - Sheets API write limit

3. **Authentication Failures**
   - Expired API keys
   - Invalid credentials
   - Revoked access tokens

4. **Malformed Responses**
   - Invalid JSON from Claude
   - Missing required fields
   - Unexpected data types

5. **Business Logic Errors**
   - Empty workflow responses
   - Consensus voting failures
   - Invalid tier selections

### Error Test Implementation

**Location:** `tests/integration/error_scenarios/`

```python
class TestClaudeErrorScenarios:
    """Test Claude API error handling."""

    def test_should_retry_on_timeout(self, real_claude):
        """Test retry logic for timeouts."""
        with patch.object(real_claude.client, '_request', side_effect=TimeoutError):
            # Validate retry with exponential backoff
            # Max 3 retries, then raise
            pass

    def test_should_handle_rate_limit_429(self, real_claude):
        """Test rate limit handling."""
        # Make rapid requests to trigger 429
        # Validate backoff and retry
        # Eventually succeed
        pass

    def test_should_fail_gracefully_on_malformed_json(self, real_claude):
        """Test handling of invalid JSON responses."""
        with patch.object(real_claude.client, '_request') as mock:
            mock.return_value = "invalid json{{"
            with pytest.raises(JSONDecodeError):
                real_claude.generate_completion("test")
```

## E2E Test Strategy

### Full Workflow Tests

**Location:** `tests/e2e/test_complete_workflows.py`

```python
class TestCompleteWorkflowE2E:
    """End-to-end workflow tests with real services."""

    @pytest.fixture
    def workflow_engine(self):
        """Real workflow engine with all dependencies."""
        return WorkflowEngine(
            ai_provider=ClaudeAdapter(),  # Real
            email_provider=GmailAdapter(),  # Real
            storage_provider=SheetsAdapter()  # Real
        )

    def test_budget_tier_complete_workflow(self, workflow_engine):
        """Test complete budget tier workflow end-to-end."""
        # Arrange
        inquiry = WorkflowInquiry(
            company_name="Test Corp",
            website="https://testcorp.com",
            industry="E-commerce",
            prompt="Optimize checkout process",
            tier=WorkflowTier.BUDGET
        )

        # Act
        result = workflow_engine.process_inquiry(inquiry)

        # Assert - Validate complete result
        assert result.workflows is not None
        assert len(result.workflows) > 0
        assert result.consensus_score > 0.7
        assert result.qa_metrics.overall_score > 0.6

        # Verify QA logged to Sheets
        # Verify could be emailed (or actually email to test account)

    def test_premium_tier_with_email_delivery(self, workflow_engine):
        """Test premium tier with real email delivery."""
        # Full workflow including email send
        # Verify email received with correct content
        pass
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Goal:** Establish real integration test infrastructure

1. Set up test environment:
   - Create test Google Cloud project
   - Generate test API keys (Claude, Gmail, Sheets, Stripe test mode)
   - Create test Gmail account for email testing
   - Create test spreadsheet for QA logging

2. Create integration test structure:
   - `tests/integration/infrastructure/` directory
   - Fixtures for real service clients
   - Environment variable configuration

3. Implement first real integration tests:
   - `test_claude_real.py` - 10 tests (happy path + errors)
   - `test_gmail_real.py` - 8 tests
   - `test_sheets_real.py` - 8 tests
   - `test_stripe_real.py` - 6 tests

**Success Criteria:**
- 32 new integration tests passing
- All tests use real APIs (zero mocks)
- Tests run reliably in CI/CD

### Phase 2: Error Scenarios (Week 3)
**Goal:** Comprehensive error coverage

1. Create error scenario tests:
   - Network failures (timeouts, connection errors)
   - Rate limits (429 responses)
   - Authentication failures
   - Malformed responses

2. Implement retry logic:
   - Exponential backoff for transient failures
   - Circuit breaker for persistent failures
   - Graceful degradation

3. Add 30 error scenario tests

**Success Criteria:**
- All error paths tested with real APIs
- Retry logic validated
- No unhandled exceptions in production scenarios

### Phase 3: E2E Workflows (Week 4)
**Goal:** Full workflow validation

1. Create E2E test suite:
   - Budget tier complete workflow
   - Standard tier with email delivery
   - Premium tier with all features
   - Multi-user concurrent scenarios

2. Add 20 E2E tests

**Success Criteria:**
- Complete workflows tested end-to-end
- Email delivery verified
- QA logging validated
- All tiers tested

### Phase 4: Performance & Cost Optimization (Week 5)
**Goal:** Optimize test suite speed and cost

1. Implement test optimization:
   - Response caching for repeated scenarios
   - Parallel test execution
   - Smart test selection (run subset on PR, full on merge)

2. Add cost monitoring:
   - Track API usage per test run
   - Alert on budget overruns
   - Optimize expensive tests

**Success Criteria:**
- Test suite runs in <5 minutes
- API cost <$10/day
- 95% test reliability

## Cost Management Strategy

### Budget Allocation

- **Claude API:** $3/day (~$90/month)
  - 200 tests × 500 tokens avg = 100K tokens/run
  - ~$0.30 per full suite run
  - 10 runs/day = $3/day

- **Gmail API:** Free (within quotas)
  - Send limit: 100/day (tests use ~20)

- **Sheets API:** Free (within quotas)
  - Write limit: 500/minute (tests use ~50)

- **Stripe API:** Free (test mode)

**Total: ~$3/day or $90/month**

### Cost Optimization Techniques

1. **Caching:**
   - Cache Claude responses for deterministic inputs
   - Reuse cached responses across test runs
   - Invalidate cache on prompt changes

2. **Selective Running:**
   - PR builds: Run 25% of integration tests (random sample)
   - Merge to main: Run 100% of tests
   - Nightly: Run full suite + performance tests

3. **Token Minimization:**
   - Use smallest prompt that validates behavior
   - Limit max_tokens to minimum needed
   - Use faster models where appropriate

## Success Metrics

### Test Quality Metrics

1. **Test Validity Score:** 9/10 (up from 5/10)
   - 90% of tests validate real behavior
   - 10% unit tests for pure logic

2. **Real API Coverage:** 100%
   - All external service integrations tested with real APIs
   - Zero critical paths rely on mocks

3. **Error Coverage:** 95%
   - All expected error scenarios tested
   - All retry/fallback logic validated

4. **E2E Coverage:** 100%
   - All user workflows tested end-to-end
   - All tiers (Budget/Standard/Premium) validated

### Reliability Metrics

1. **Test Flakiness:** <1%
   - Tests pass consistently
   - Retry logic handles transient failures

2. **False Positive Rate:** <5%
   - Tests fail only when code is broken
   - No spurious failures from mocks

3. **Mean Time to Detect (MTTD):** <5 minutes
   - Broken code detected immediately in CI
   - Fast feedback loop

### Performance Metrics

1. **Test Suite Duration:** <5 minutes
   - Fast enough for CI/CD
   - Parallel execution optimized

2. **API Cost:** <$10/day
   - Sustainable for continuous testing
   - Monitored and optimized

## Risk Mitigation

### Risk 1: API Costs Spiral
**Mitigation:**
- Set hard budget limits in CI ($5/day max)
- Alert on unusual usage patterns
- Automatic test suite pause if budget exceeded

### Risk 2: Test Reliability Issues
**Mitigation:**
- Implement robust retry logic
- Use dedicated test accounts (no interference)
- Clean up test data after each run

### Risk 3: Slow Test Execution
**Mitigation:**
- Parallel test execution (pytest-xdist)
- Selective test running (pytest markers)
- Cache expensive operations

### Risk 4: External Service Downtime
**Mitigation:**
- Skip integration tests if service unavailable (pytest.mark.skipif)
- Nightly reruns catch intermittent issues
- Alert team to persistent failures

## Comparison to Current State

### Current (5/10 Validity)
- 86 tests total
- 60% use mocks
- No real Claude/Gmail/Sheets/Stripe tests
- False confidence

### Proposed (9/10 Validity)
- ~200 tests total
- 80% use real APIs
- 100% critical path coverage
- True confidence

## Conclusion

This integration-first approach prioritizes **real behavior validation** over speed. By testing with actual external services, we gain true confidence that the system works in production. The cost is manageable (~$90/month), and the reliability improvements are worth the investment.

**Key Principle:** If it's not tested with real services, it's not truly tested.
