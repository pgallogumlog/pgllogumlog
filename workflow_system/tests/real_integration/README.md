# Real API Integration Tests

**NO MOCKS** - These tests use REAL external APIs:
- Claude API (Anthropic)
- Gmail API (Google)
- Google Sheets API

## Quick Start

### Prerequisites

1. **API Keys configured in `.env`:**
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
GOOGLE_CREDENTIALS_FILE=config/google_credentials.json
GMAIL_USER_EMAIL=your-email@gmail.com
GOOGLE_SHEETS_QA_LOG_ID=your-spreadsheet-id

# Optional for Sheets tests
TEST_SPREADSHEET_ID=test-only-spreadsheet-id
TEST_EMAIL_RECIPIENT=test@example.com
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### Run All Real API Tests

```bash
cd workflow_system
pytest tests/real_integration/ -v -m real_api
```

### Run Specific Test File

```bash
# Priority 1: Core workflow tests
pytest tests/real_integration/test_real_core_workflow.py -v

# Priority 2: End-to-end tests
pytest tests/real_integration/test_real_end_to_end.py -v

# Priority 4: QA capture tests
pytest tests/real_integration/test_real_qa_capture.py -v
```

### Run Single Test

```bash
pytest tests/real_integration/test_real_core_workflow.py::TestRealWorkflowEngine::test_should_process_inquiry_with_real_claude_api -v
```

---

## Test Structure

### Test Files (Priority Order)

1. **test_real_core_workflow.py** - Core workflow with real Claude API
   - Basic workflow processing
   - Tier handling (Budget, Standard, Premium)
   - Identity extraction
   - Consensus formation

2. **test_real_end_to_end.py** - Complete user flows
   - Full workflow from inquiry to proposal
   - Google Sheets logging (optional)
   - Multi-tier testing

3. **test_real_qa_capture.py** - QA validation pipeline
   - Call capture validation
   - Deterministic validators
   - Context tracking
   - Quality scoring

---

## Cost Estimates

### Per Test Costs (Claude API)
- **Budget Tier Test:** ~$0.25-0.30 per run
- **Standard Tier Test:** ~$0.30-0.35 per run
- **Premium Tier Test:** ~$0.35-0.40 per run
- **Multi-Tier Test:** ~$0.90 per run (3 tiers)

### Full Suite Cost
- **All tests (single run):** ~$2-3
- **Daily CI run:** ~$3/day = ~$90/month
- **Per PR run (critical tests only):** ~$1

### Other APIs
- Gmail API: FREE
- Google Sheets API: FREE (within quotas)

---

## Test Assertions

### Flexible Assertions (Account for AI Non-Determinism)

```python
# ✓ Good - Flexible
assert len(result.consensus.all_workflows) == 3
assert result.consensus.confidence_percent >= 0

# ✗ Bad - Too rigid
assert result.consensus.final_answer == "Email Automation"
assert result.consensus.votes_for_winner == 5
```

### Structure-Based Assertions

```python
# Validate structure, not exact content
assert all(wf.name for wf in workflows), "All workflows should have names"
assert isinstance(result.proposal.phases, list)
assert len(result.proposal.phases) > 0
```

---

## Test Isolation

### Each Test Should:
- ✓ Use fresh fixtures
- ✓ Not depend on other tests
- ✓ Clean up after itself
- ✓ Be runnable individually
- ✓ Be runnable in any order

### Fixtures Provide:
- `real_ai_provider` - Fresh Claude API client
- `real_capturing_ai_provider` - Claude client with QA capture
- `real_email_client` - Gmail API client
- `real_sheets_client` - Google Sheets client
- `sample_test_inquiry` - Minimal test prompt (cost-effective)

---

## Debugging Tests

### View Detailed Output

```bash
pytest tests/real_integration/ -v -s
```

The `-s` flag shows print statements, which include detailed test results.

### Run Single Test with Maximum Detail

```bash
pytest tests/real_integration/test_real_core_workflow.py::TestRealWorkflowEngine::test_should_process_inquiry_with_real_claude_api -v -s --tb=long
```

### Skip Slow Tests

```bash
pytest tests/real_integration/ -v -m "real_api and not slow"
```

---

## Environment-Specific Configuration

### Local Development
```bash
# Use real APIs, minimal tests
pytest tests/real_integration/test_real_core_workflow.py -v
```

### Pull Request CI
```bash
# Run critical real API tests only
pytest tests/real_integration/test_real_core_workflow.py tests/real_integration/test_real_end_to_end.py::TestRealEndToEndWorkflow::test_should_complete_full_workflow_with_real_apis -v
```

### Daily CI Build
```bash
# Run full suite
pytest tests/real_integration/ -v -m real_api
```

---

## Handling Flaky Tests

### Retry Failed Tests

```bash
# Install pytest-rerunfailures
pip install pytest-rerunfailures

# Retry failed tests up to 3 times
pytest tests/real_integration/ -v --reruns 3 --reruns-delay 2
```

### Timeout Protection

All tests have implicit timeouts from pytest-timeout (if installed).

---

## Test Markers

```python
@pytest.mark.real_api        # Uses real APIs (slower, costs money)
@pytest.mark.asyncio         # Async test
@pytest.mark.slow            # Slow test (skip with -m 'not slow')
@pytest.mark.sheets          # Requires Google Sheets access
```

### Run Tests by Marker

```bash
# Only real API tests
pytest -m real_api -v

# Exclude slow tests
pytest -m "real_api and not slow" -v

# Only Sheets tests (requires TEST_SPREADSHEET_ID)
pytest -m sheets -v --run-sheets-tests
```

---

## Troubleshooting

### API Key Issues

**Error:** `AuthenticationError: Invalid API key`

**Fix:** Check `.env` file has valid `ANTHROPIC_API_KEY`

### Rate Limit Errors

**Error:** `RateLimitError: Rate limit exceeded`

**Fix:** Tests include retry logic. If persistent, reduce parallel tests or add delays.

### Sheets Access Issues

**Error:** `TEST_SPREADSHEET_ID not set`

**Fix:** Set in `.env` or skip Sheets tests

### Timeout Errors

**Error:** Test times out

**Fix:** Increase timeout or check API connectivity

---

## Best Practices

### 1. Keep Prompts Minimal
```python
# ✓ Good - Cost-effective
body = "Recommend 3 workflows for a coffee shop."

# ✗ Bad - Expensive
body = """Analyze this 50-page business plan and recommend
          25 comprehensive automation workflows..."""
```

### 2. Use Budget Tier for Most Tests
```python
# ✓ Good - Cheaper, faster
result, _ = await engine.process_inquiry(inquiry, tier="Budget")

# ✗ Use Premium only when testing Premium-specific features
```

### 3. Validate Structure, Not Content
```python
# ✓ Good
assert len(result.consensus.all_workflows) == 3
assert all(wf.name for wf in result.consensus.all_workflows)

# ✗ Bad
assert result.consensus.all_workflows[0].name == "Email Bot"
```

### 4. Print Detailed Results
```python
print(f"Run ID: {result.run_id}")
print(f"Consensus: {result.consensus.final_answer}")
print(f"Workflows: {len(result.consensus.all_workflows)}")
```

---

## Next Steps

### Implement Additional Tests

1. **Error Recovery Tests** - Rate limits, retries, timeouts
2. **Performance Tests** - Latency benchmarks
3. **Gmail Integration Tests** - Email delivery validation
4. **Concurrent Processing Tests** - Parallel workflow handling

### Optimize Costs

1. Cache API responses for deterministic tests
2. Use smaller test prompts
3. Run expensive tests only on main branch

### Add CI/CD Integration

1. GitHub Actions workflow for daily runs
2. PR checks with critical tests only
3. Cost tracking and alerts

---

## Support

For questions or issues:
1. Check CODEBASE_ANALYSIS.md for architecture details
2. Check TDD_TEST_ARCHITECTURE.md for design patterns
3. Review existing test examples
4. Run with `-v -s` for detailed output
