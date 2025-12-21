# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# Workflow System Development Guide

## Identity
You are the orchestrating agent for a workflow automation system that generates AI-powered business workflow recommendations. You coordinate development of the complete system including backend processing, frontend user interface, payment integration, and delivery mechanisms.

## Current Implementation Status

### ✅ Implemented
- Core workflow engine with consensus voting (multi-temperature)
- QA system with deterministic and probabilistic validators
- Test orchestration framework with 44+ tests
- FastAPI web application with REST endpoints
- Claude API integration with call capture
- Google Sheets integration for QA logging
- Gmail integration for email delivery
- Structured logging with structlog
- Dependency injection container
- Background email polling service

### 🚧 Planned/Future
- Stripe payment processing integration
- Playwright e2e tests
- User submission form with payment flow
- Production deployment configuration

## Architecture Overview

### Key Architectural Patterns

**1. Domain-Driven Design (Contexts)**
- `contexts/workflow/` - Core business logic for workflow generation
- `contexts/qa/` - Quality assurance and validation logic
- `contexts/testing/` - Test orchestration and execution
- Each context is self-contained with its own models and logic

**2. Hexagonal Architecture (Ports & Adapters)**
- `infrastructure/` contains adapters for external services:
  - `ai/` - Claude API client and QA-instrumented wrapper
  - `storage/` - Google Sheets persistence
  - `email/` - Gmail delivery
- Business logic (contexts) depends on interfaces, not implementations
- Dependency injection enables swapping implementations (e.g., MockAIProvider for tests)

**3. Multi-Temperature Consensus Voting**
- Core innovation: Run same prompt at different temperatures (0.4, 0.6, 0.8, 1.0, 1.2)
- Voter (`contexts/workflow/voter.py`) analyzes outputs for consensus
- Improves reliability by detecting hallucinations and inconsistencies
- Configurable via `SC_TEMPERATURES` and `SC_MIN_CONSENSUS_VOTES` env vars

**4. QA Capture & Validation Pipeline**
- `CapturingAIAdapter` wraps `ClaudeAdapter` to intercept all AI calls
- Captured data flows through validation pipeline:
  - Deterministic validators (response time, token count, format)
  - Probabilistic validators (semantic quality using AI)
  - Auditor assigns final quality score (1-10)
- Results logged to Google Sheets for analysis
- Enable with `--qa` flag on test runners

**5. Dependency Injection**
- `config/dependency_injection.py` provides central service container
- Enables testing with mock services (see `tests/conftest.py`)
- Services lazy-loaded on first access

## Project Overview
This system allows users to:
1. Enter business information via web form
2. Submit prompts for AI workflow analysis
3. Pay for premium analysis tiers
4. Receive results via email or direct download

## Tech Stack
**Backend**: Python 3.11+ (pyproject.toml requirement; currently 3.9+ compatible), FastAPI, Pydantic, structlog, pytest
**Frontend**: HTML5, CSS3, JavaScript ES6+, Jinja2 templates
**AI**: Claude API (Anthropic), multi-temperature consensus voting
**Storage**: Google Sheets API for logging and results
**Payments**: Stripe API for payment processing (planned/future)
**Email**: Gmail API for delivery
**Testing**: pytest (unit/integration), Playwright (e2e, planned)

## Project Structure
```
learnClaude/
├── CLAUDE.md                    # This file - development guide
├── main.py                      # PyCharm template (not used)
└── workflow_system/             # Main application directory
    ├── .env                     # Environment variables (git-ignored)
    ├── .env.example             # Environment template
    ├── pyproject.toml           # Project config, pytest, mypy, ruff settings
    ├── requirements.txt         # Python dependencies
    ├── main.py                  # Application entry point
    ├── run_test.py              # CLI test runner
    ├── run_qa_test.py           # QA-enabled test runner
    ├── authorize_sheets.py      # Google Sheets OAuth setup
    ├── config/
    │   ├── settings.py          # Environment configuration
    │   └── dependency_injection.py  # Service container
    ├── contexts/
    │   ├── workflow/            # Core workflow engine
    │   │   ├── engine.py        # Main orchestrator
    │   │   ├── models.py        # Domain models
    │   │   ├── prompts.py       # AI prompt templates
    │   │   └── voter.py         # Consensus voting
    │   ├── qa/                  # Quality assurance
    │   │   ├── auditor.py       # Semantic QA
    │   │   ├── call_capture.py  # AI call instrumentation
    │   │   ├── scoring.py       # Validation pipeline
    │   │   ├── sheets_logger.py # Log QA results to Sheets
    │   │   └── validators/      # Deterministic & probabilistic
    │   └── testing/             # Test orchestration
    │       ├── orchestrator.py  # Test runner
    │       ├── test_cases.py    # Test data
    │       └── models.py        # Test domain models
    ├── infrastructure/
    │   ├── ai/
    │   │   ├── claude_adapter.py      # Claude API client
    │   │   └── capturing_adapter.py   # QA instrumentation wrapper
    │   ├── email/
    │   │   └── gmail_adapter.py       # Gmail integration
    │   └── storage/
    │       └── sheets_adapter.py      # Google Sheets client
    ├── background/
    │   └── email_poller.py      # Background email polling service
    ├── shared/
    │   └── utils.py             # Common utility functions
    ├── data/
    │   └── test_cases/          # Test case storage
    ├── web/
    │   ├── app.py               # FastAPI application
    │   ├── api/                 # REST endpoints
    │   │   ├── health.py        # Health check endpoints
    │   │   ├── workflows.py     # Workflow execution endpoints
    │   │   └── tests.py         # Test runner endpoints
    │   └── ui/
    │       ├── templates/       # Jinja2 HTML templates
    │       └── static/          # CSS, JS, images
    └── tests/
        ├── conftest.py          # Pytest fixtures, MockAIProvider
        ├── unit/                # Unit tests
        │   └── contexts/        # Context-specific unit tests
        └── integration/         # Integration tests
            └── test_api.py      # API integration tests
```

## MCP Server Configuration

### Required MCP Servers
**Note**: The `.mcp.json` file does not currently exist. Create it in the project root when needed:
```json
{
  "mcpServers": {
    "puppeteer": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-puppeteer@latest"],
      "description": "Browser automation for visual UI validation"
    },
    "stripe": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-stripe@latest"],
      "env": {
        "STRIPE_SECRET_KEY": "${STRIPE_SECRET_KEY}"
      },
      "description": "Payment processing integration"
    },
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "description": "Up-to-date library documentation"
    }
  }
}
```

### MCP Usage Patterns

#### Puppeteer - Visual UI Validation
Use for iterative frontend development:
```
"Navigate to http://localhost:8000 and take a screenshot"
"Click the submit button and screenshot the result"
"Fill the email field with 'test@example.com' and screenshot"
"Take a full-page screenshot showing the payment form"
```

**Visual Iteration Loop:**
1. Implement UI component
2. Start server: `uvicorn workflow_system.web.app:app --reload`
3. Screenshot the page
4. Evaluate against requirements
5. Fix issues and screenshot again
6. Repeat until visual matches expectations

#### Stripe - Payment Integration (Future/Planned)
**Note**: Stripe integration is not yet implemented. When implemented, use for:
```
"Create a Stripe checkout session for $29.99 premium tier"
"List recent payments for customer email"
"Create a payment intent for the standard tier"
"Verify webhook signature for payment confirmation"
```

## Test-Driven Development (TDD) Protocol

### The TDD Cycle
```
┌─────────────────────────────────────────────────────────┐
│  RED → GREEN → REFACTOR → VERIFY → COMMIT              │
│                                                         │
│  1. RED:      Write a failing test first               │
│  2. GREEN:    Write minimal code to pass the test      │
│  3. REFACTOR: Clean up without changing behavior       │
│  4. VERIFY:   Run full test suite                      │
│  5. COMMIT:   Atomic commit with descriptive message   │
└─────────────────────────────────────────────────────────┘
```

### TDD Rules
1. **Never write production code without a failing test**
2. **Write only enough test code to fail** (compilation failures count)
3. **Write only enough production code to pass the failing test**
4. **Refactor only when tests are green**

### Test Structure
```python
# tests/unit/contexts/test_feature.py
import pytest
from contexts.feature import FeatureClass

class TestFeatureClass:
    """Tests for FeatureClass."""

    @pytest.fixture
    def feature(self):
        """Create feature instance for testing."""
        return FeatureClass()

    def test_should_do_expected_behavior(self, feature):
        """Descriptive test name explaining expected behavior."""
        # Arrange
        input_data = {"key": "value"}

        # Act
        result = feature.process(input_data)

        # Assert
        assert result.success is True
        assert result.output == "expected"

    def test_should_handle_edge_case(self, feature):
        """Test edge cases and error conditions."""
        with pytest.raises(ValueError, match="Invalid input"):
            feature.process(None)
```

### Test Commands
**Note**: All test commands should be run from the `workflow_system/` directory.

```bash
# Navigate to workflow_system directory first
cd workflow_system

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/unit/contexts/test_workflow_engine.py -v

# Run specific test
python -m pytest tests/unit/contexts/test_workflow_engine.py::TestWorkflowEngine::test_process_inquiry -v

# Run with coverage
python -m pytest tests/ --cov=contexts --cov-report=html

# Run tests matching pattern
python -m pytest tests/ -k "test_payment" -v

# Run integration tests only
python -m pytest tests/integration/ -v

# Run with QA capture (uses CLI test runner)
python run_test.py --qa --tier standard --count 1

# Run QA tests with mock AI provider (no API calls)
python run_test.py --qa --mock --tier standard
```

## Production Readiness Checklist

### Level 1: Functional (MVP)
- [ ] All happy path tests pass
- [ ] Basic error handling exists
- [ ] Environment variables configured
- [ ] Can process a request end-to-end

### Level 2: Reliable
- [ ] Edge cases tested and handled
- [ ] Input validation on all endpoints
- [ ] Proper error messages returned to users
- [ ] Logging captures key events
- [ ] No hardcoded secrets or credentials

### Level 3: Observable
- [ ] Structured logging (structlog) throughout
- [ ] Request tracing with run_id
- [ ] Performance metrics captured
- [ ] Error rates trackable
- [ ] QA scores logged to Google Sheets

### Level 4: Resilient
- [ ] Retry logic for external APIs (Claude, Stripe, Gmail)
- [ ] Circuit breakers for failing services
- [ ] Graceful degradation when services unavailable
- [ ] Rate limiting on public endpoints
- [ ] Timeout handling

### Level 5: Secure
- [ ] HTTPS enforced
- [ ] CORS configured properly
- [ ] Input sanitization (XSS, injection prevention)
- [ ] Authentication on protected endpoints
- [ ] Stripe webhook signature verification
- [ ] Secrets in environment variables only
- [ ] Security headers set

### Level 6: Scalable
- [ ] Stateless request handling
- [ ] Database connection pooling (if applicable)
- [ ] Async operations where beneficial
- [ ] Caching strategy implemented
- [ ] Load tested under expected traffic

## Iterative Improvement Protocol

### When Building New Features
```
Phase 1: Spike (if needed)
─────────────────────────
- Prototype to validate approach
- Throwaway code, no tests needed
- Time-boxed: max 30 minutes
- Outcome: Confirmed approach or pivot

Phase 2: Foundation (TDD)
─────────────────────────
- Write failing tests for core functionality
- Implement minimal passing code
- Cover happy path only
- Outcome: Working feature, basic tests

Phase 3: Hardening
──────────────────
- Add edge case tests
- Add error handling tests
- Implement validation
- Add logging
- Outcome: Reliable feature

Phase 4: Polish
───────────────
- Performance optimization
- User experience refinement
- Visual validation with Puppeteer
- Documentation
- Outcome: Production-ready feature
```

### Visual Iteration Example (Frontend)
```
1. Write test for form submission endpoint
2. Implement basic HTML form
3. Screenshot: "Navigate to http://localhost:8000/submit and screenshot"
4. Evaluate: "Form renders but lacks styling and validation"
5. Add CSS styling
6. Screenshot again
7. Evaluate: "Form styled, but missing error states"
8. Add client-side validation with error display
9. Screenshot with invalid input
10. Evaluate: "Error states display correctly"
11. Test payment integration
12. Screenshot checkout flow
13. Iterate until production-ready
```

## Frontend Development Guide

**Note**: The payment integration described below is planned for future implementation.

### User Submission Form Requirements
The form must collect:
1. **Business Information**
   - Company name
   - Website URL
   - Industry/sector
   - Company size

2. **Analysis Request**
   - Prompt/description of needs
   - Tier selection (Budget/Standard/Premium)

3. **Payment**
   - Stripe Elements integration
   - Price display based on tier

4. **Delivery Options**
   - Email address (required)
   - Optional: Download immediately

### Form Implementation Pattern
```html
<!-- templates/submit.html -->
<form id="workflow-form" action="/api/v1/workflows/submit" method="POST">
  <!-- Business Info Section -->
  <section class="form-section">
    <h2>Business Information</h2>
    <input type="text" name="company_name" required>
    <input type="url" name="website_url" required>
    <!-- ... -->
  </section>

  <!-- Tier Selection -->
  <section class="form-section">
    <h2>Analysis Tier</h2>
    <div class="tier-cards">
      <label class="tier-card">
        <input type="radio" name="tier" value="budget">
        <span class="tier-name">Budget</span>
        <span class="tier-price">$9.99</span>
      </label>
      <!-- ... -->
    </div>
  </section>

  <!-- Stripe Payment -->
  <section class="form-section">
    <h2>Payment</h2>
    <div id="stripe-elements"></div>
  </section>

  <!-- Delivery -->
  <section class="form-section">
    <h2>Delivery</h2>
    <input type="email" name="email" required>
    <label>
      <input type="checkbox" name="download_immediately">
      Also download results immediately
    </label>
  </section>

  <button type="submit">Submit & Pay</button>
</form>
```

### Stripe Integration Pattern
```javascript
// static/js/payment.js
const stripe = Stripe('pk_test_...');
const elements = stripe.elements();
const card = elements.create('card');
card.mount('#stripe-elements');

async function handleSubmit(event) {
  event.preventDefault();

  // Create payment intent on backend
  const response = await fetch('/api/v1/payments/create-intent', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({tier: selectedTier})
  });
  const {clientSecret} = await response.json();

  // Confirm payment with Stripe
  const {error, paymentIntent} = await stripe.confirmCardPayment(
    clientSecret,
    {payment_method: {card: card}}
  );

  if (error) {
    showError(error.message);
  } else if (paymentIntent.status === 'succeeded') {
    submitWorkflowRequest(paymentIntent.id);
  }
}
```

## Commands Reference

**Note**: All commands below should be run from the `workflow_system/` directory unless otherwise specified.

### Development
```bash
# Navigate to workflow_system directory
cd workflow_system

# Start development server (from workflow_system/)
uvicorn web.app:app --reload --host 0.0.0.0 --port 8000

# Run all tests (from workflow_system/)
python -m pytest tests/ -v

# Run with QA capture (from workflow_system/)
python run_test.py --qa --tier standard

# Format code (from project root: learnClaude/)
cd ..
python -m black workflow_system/

# Or format from workflow_system/
python -m black .

# Type checking (from workflow_system/)
python -m mypy contexts/ infrastructure/ web/

# Set up Google Sheets OAuth (one-time setup)
python authorize_sheets.py
```

### Production
```bash
# Start production server (from workflow_system/)
uvicorn web.app:app --host 0.0.0.0 --port 8000 --workers 4

# Run with gunicorn (from workflow_system/)
gunicorn web.app:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Environment Variables
Required in `workflow_system/.env` (see `.env.example` for full template):

```bash
# AI Provider (Required)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx

# Google Credentials (Required for Sheets/Gmail)
GOOGLE_CREDENTIALS_FILE=config/google_credentials.json
GMAIL_USER_EMAIL=your-email@gmail.com
GOOGLE_SHEETS_QA_LOG_ID=your-spreadsheet-id
GOOGLE_SHEETS_CONFIG_ID=your-config-spreadsheet-id

# Application Settings
APP_ENV=development
APP_DEBUG=true
APP_HOST=127.0.0.1
APP_PORT=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///data/workflow_system.db

# Workflow Settings (Self-Consistency Engine)
SC_TEMPERATURES=0.4,0.6,0.8,1.0,1.2
SC_MIN_CONSENSUS_VOTES=2
SC_MODEL=claude-sonnet-4-20250514

# QA Auditor Settings
QA_MODEL=claude-sonnet-4-20250514
QA_MIN_PASS_SCORE=7

# Stripe (Future/Planned - Not yet implemented)
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_PUBLISHABLE_KEY=pk_test_...
# STRIPE_WEBHOOK_SECRET=whsec_...
```

## Quality Gates

### Before ANY Commit
- [ ] All tests pass: `cd workflow_system && python -m pytest tests/ -v`
- [ ] Code formatted: `python -m black --check workflow_system/`
- [ ] No secrets in code
- [ ] Descriptive commit message

### Before Merging to Main
- [ ] All quality gates above
- [ ] Integration tests pass
- [ ] Visual validation complete (for UI changes)
- [ ] Production readiness level maintained or improved

## Git & GitHub Workflow

### Repository
- **Remote**: https://github.com/pgallogumlog/pgllogumlog
- **Default Branch**: main
- **Clone**: `git clone https://github.com/pgallogumlog/pgllogumlog.git`

### Branching Strategy
```
main              # Production-ready code only
├── feature/*     # New features (feature/add-payment-form)
├── fix/*         # Bug fixes (fix/stripe-webhook-error)
├── refactor/*    # Code improvements (refactor/extract-validation)
└── docs/*        # Documentation updates (docs/api-endpoints)
```

### Branch Workflow
```bash
# Start new feature
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Work on feature (commit frequently)
git add -A
git commit -m "feat(scope): description"

# Push and create PR
git push -u origin feature/your-feature-name
# Then create PR on GitHub or use gh cli
```

### Commit Message Convention
Format: `type(scope): description`

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding or updating tests
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `chore`: Maintenance tasks

**Examples:**
```
feat(payment): add Stripe checkout integration
fix(workflow): handle empty response from Claude API
refactor(qa): extract validation logic to separate module
test(api): add integration tests for workflow endpoint
docs(readme): update installation instructions
```

### Pull Request Process
1. **Create branch** from latest main
2. **Implement** with TDD (tests first)
3. **Verify** all tests pass locally
4. **Push** branch to origin
5. **Create PR** with description:
   - Summary of changes
   - Test plan
   - Screenshots (for UI changes)
6. **Review** - address any feedback
7. **Merge** to main when approved
8. **Delete** feature branch after merge

### GitHub CLI Commands
```bash
# Check status
git status
git log --oneline -10

# Create PR
gh pr create --title "feat: add payment form" --body "## Summary\n- Added Stripe integration\n- Created payment form UI"

# View PRs
gh pr list
gh pr view 123

# Merge PR
gh pr merge 123 --squash

# View issues
gh issue list
gh issue create --title "Bug: payment fails" --body "Description..."
```

### Protected Files (Never Commit)
These are in `.gitignore` - verify they stay excluded:
```
.env                           # Environment variables
config/google_credentials.json # Google API credentials
*credentials*.json             # Any credential files
*.pem                          # SSL certificates
.claude/                       # Claude Code cache
```

### Pre-Commit Checklist
Before every commit (run from project root: `learnClaude/`):
```bash
# 1. Check what's staged
git status
git diff --staged

# 2. Verify no secrets
git diff --staged | grep -i "api_key\|secret\|password\|credential"

# 3. Run tests (from workflow_system/)
cd workflow_system
python -m pytest tests/ -v
cd ..

# 4. Format code (from project root)
python -m black workflow_system/

# 5. Commit with good message
git commit -m "type(scope): description"
```

### Syncing with Remote
```bash
# Get latest changes
git fetch origin
git pull origin main

# If on feature branch, rebase onto main
git checkout feature/your-branch
git rebase main

# Push with force after rebase (only on YOUR branch)
git push --force-with-lease
```

### Undoing Mistakes
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard all local changes
git checkout -- .

# Discard changes to specific file
git checkout -- path/to/file

# Amend last commit message
git commit --amend -m "new message"
```

## Error Recovery Protocol

When stuck or tests fail:
1. **Stop** - Don't keep trying the same approach
2. **Diagnose** - Read the full error message and stack trace
3. **Isolate** - Create minimal reproduction
4. **Research** - Check docs via Context7 MCP if needed
5. **Fix** - Apply targeted fix
6. **Verify** - Run tests to confirm fix
7. **Report** - If blocked after 3 attempts, pause and explain the issue

## Forbidden Actions
- Skipping tests to "save time"
- Committing with failing tests
- Hardcoding API keys or secrets
- Modifying unrelated files
- Large refactors without test coverage
- Ignoring error handling
- Pushing directly to main without verification
