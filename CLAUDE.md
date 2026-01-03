# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# AI Readiness Compass Development Guide

## Identity
You are the orchestrating agent for the AI Readiness Compass - a premium $497 AI-powered strategic assessment product. You coordinate development of the complete system including backend processing, frontend user interface, payment integration, and email delivery.

## Current Implementation Status

### ✅ Implemented
- AI Readiness Compass engine (two-call architecture)
- Research agents (Company, Industry, White Paper) running in parallel
- Self-assessment scoring with hybrid AI research scoring
- Priority analyzer with anti-recommendations and 90-day roadmap
- HTML report generator with Jinja2 templates
- Compass-specific QA validators (Call 1, Call 2, Cross-call)
- Stripe payment integration (manual capture flow)
- FastAPI web application with REST endpoints
- Claude API integration with call capture
- Gmail integration for report delivery
- Compass test orchestrator with 15 test cases
- Structured logging with structlog
- Dependency injection container

### 🚧 Planned/Future
- Playwright e2e tests
- Production deployment configuration
- Web research integration (Tavily/SerpAPI)

## Architecture Overview

### Key Architectural Patterns

**1. Domain-Driven Design (Contexts)**
- `contexts/compass/` - Core Compass engine, agents, scoring, report generation
- `contexts/qa/` - Quality assurance and validation logic
- `contexts/testing/` - Compass test orchestration
- Each context is self-contained with its own models and logic

**2. Hexagonal Architecture (Ports & Adapters)**
- `infrastructure/` contains adapters for external services:
  - `ai/` - Claude API client and QA-instrumented wrapper
  - `payments/` - Stripe payment processing
  - `storage/` - Google Sheets persistence
  - `email/` - Gmail delivery
- Business logic (contexts) depends on interfaces, not implementations
- Dependency injection enables swapping implementations (e.g., MockAIProvider for tests)

**3. Two-Call Compass Architecture**
- **Call 1 (Research)**: Three parallel agents gather company, industry, and white paper insights
- **Call 2 (Synthesis)**: Priority analyzer creates recommendations, anti-recommendations, and roadmap
- Hybrid scoring: 30% self-assessment + 70% AI research score

**4. QA Capture & Validation Pipeline**
- `CapturingAIAdapter` wraps `ClaudeAdapter` to intercept all AI calls
- Compass-specific validators:
  - Call 1 Validator: Research relevance and depth
  - Call 2 Validator: Synthesis quality and citations
  - Cross-call Validator: Research utilization in synthesis
- Results logged for analysis

**5. Dependency Injection**
- `config/dependency_injection.py` provides central service container
- Enables testing with mock services (see `tests/conftest.py`)
- Services lazy-loaded on first access

## Project Overview
The AI Readiness Compass allows users to:
1. Complete a self-assessment questionnaire (data maturity, automation experience, change readiness)
2. Provide business information and pain points
3. Pay $497 via Stripe (manual capture - authorize first, capture after QA)
4. Receive a premium 8-10 page strategic report via email

## Tech Stack
**Backend**: Python 3.11+ (pyproject.toml requirement; currently 3.9+ compatible), FastAPI, Pydantic, structlog, pytest
**Frontend**: HTML5, CSS3, JavaScript ES6+, Jinja2 templates
**AI**: Claude API (Anthropic)
**Storage**: Google Sheets API for logging
**Payments**: Stripe API with manual capture flow
**Email**: Gmail API for report delivery
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
    ├── authorize_sheets.py      # Google Sheets OAuth setup
    ├── config/
    │   ├── settings.py          # Environment configuration
    │   └── dependency_injection.py  # Service container
    ├── contexts/
    │   ├── compass/             # AI Readiness Compass engine
    │   │   ├── models.py        # Domain models (CompassRequest, CompassReport, etc.)
    │   │   ├── scoring.py       # Self-assessment scorer
    │   │   ├── two_call_engine.py  # Main orchestrator
    │   │   ├── generator.py     # HTML report generator
    │   │   ├── analyzer.py      # Priority analyzer
    │   │   ├── agents/          # Research agents
    │   │   │   ├── company_agent.py
    │   │   │   ├── industry_agent.py
    │   │   │   ├── whitepaper_agent.py
    │   │   │   └── orchestrator.py
    │   │   ├── templates/       # Jinja2 report templates
    │   │   └── validators/      # Compass-specific QA validators
    │   ├── qa/                  # Quality assurance
    │   │   ├── call_capture.py  # AI call instrumentation
    │   │   ├── models.py        # QA models
    │   │   ├── scoring.py       # Validation pipeline
    │   │   └── validators/      # Deterministic validators
    │   └── testing/             # Test orchestration
    │       ├── compass_orchestrator.py  # Compass test runner
    │       └── compass_test_cases.py    # Test data
    ├── infrastructure/
    │   ├── ai/
    │   │   ├── claude_adapter.py      # Claude API client
    │   │   └── capturing_adapter.py   # QA instrumentation wrapper
    │   ├── payments/
    │   │   └── stripe_adapter.py      # Stripe integration
    │   ├── email/
    │   │   └── gmail_adapter.py       # Gmail integration
    │   └── storage/
    │       └── sheets_adapter.py      # Google Sheets client
    ├── shared/
    │   └── utils.py             # Common utility functions
    ├── web/
    │   ├── app.py               # FastAPI application
    │   ├── api/                 # REST endpoints
    │   │   ├── health.py        # Health check endpoints
    │   │   ├── compass.py       # Compass submission endpoints
    │   │   └── tests.py         # Test runner endpoints
    │   └── ui/
    │       ├── templates/       # Jinja2 HTML templates
    │       └── static/          # CSS, JS, images
    └── tests/
        ├── conftest.py          # Pytest fixtures, MockAIProvider
        ├── unit/                # Unit tests
        │   ├── contexts/
        │   │   └── compass/     # Compass unit tests
        │   ├── infrastructure/  # Infrastructure unit tests
        │   └── web/             # Web layer unit tests
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

#### Stripe - Payment Integration
Use for payment testing:
```
"Create a Stripe payment intent for $497"
"List recent payments for customer email"
"Capture the payment intent after QA passes"
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
# tests/unit/contexts/compass/test_feature.py
import pytest
from contexts.compass.feature import FeatureClass

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

# Run Compass tests only
python -m pytest tests/unit/contexts/compass/ -v

# Run specific test file
python -m pytest tests/unit/contexts/compass/test_engine.py -v

# Run with coverage
python -m pytest tests/ --cov=contexts --cov-report=html

# Run tests matching pattern
python -m pytest tests/ -k "test_compass" -v

# Run integration tests only
python -m pytest tests/integration/ -v
```

## Production Readiness Checklist

### Level 1: Functional (MVP)
- [ ] All happy path tests pass
- [ ] Basic error handling exists
- [ ] Environment variables configured
- [ ] Can process a Compass request end-to-end

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
- [ ] QA scores logged

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
3. Screenshot: "Navigate to http://localhost:8000/compass and screenshot"
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

### AI Readiness Compass Form Requirements
The form must collect:
1. **Business Information**
   - Company name
   - Website URL (optional)
   - Industry/sector
   - Company size

2. **AI Readiness Self-Assessment**
   - Data maturity (1-5)
   - Automation experience (1-5)
   - Change readiness (1-5)

3. **Your Challenge**
   - Pain point description
   - Additional context

4. **Payment**
   - Stripe Elements integration
   - $497 price display

5. **Delivery**
   - Email address (required)
   - Contact name

### Form Implementation Pattern
```html
<!-- templates/compass.html -->
<form id="compass-form" action="/api/compass/submit" method="POST">
  <!-- Business Info Section -->
  <section class="form-section">
    <h2>Business Information</h2>
    <input type="text" name="company_name" required>
    <input type="url" name="website">
    <select name="industry" required>...</select>
    <select name="company_size" required>...</select>
  </section>

  <!-- Self-Assessment Section -->
  <section class="form-section">
    <h2>AI Readiness Self-Assessment</h2>
    <div class="slider-group">
      <label>Data Maturity</label>
      <input type="range" name="data_maturity" min="1" max="5" required>
    </div>
    <div class="slider-group">
      <label>Automation Experience</label>
      <input type="range" name="automation_experience" min="1" max="5" required>
    </div>
    <div class="slider-group">
      <label>Change Readiness</label>
      <input type="range" name="change_readiness" min="1" max="5" required>
    </div>
  </section>

  <!-- Pain Point Section -->
  <section class="form-section">
    <h2>Your Challenge</h2>
    <textarea name="pain_point" required></textarea>
    <textarea name="description"></textarea>
  </section>

  <!-- Stripe Payment -->
  <section class="form-section">
    <h2>Payment - $497</h2>
    <div id="stripe-elements"></div>
  </section>

  <!-- Delivery -->
  <section class="form-section">
    <h2>Delivery</h2>
    <input type="text" name="contact_name" required>
    <input type="email" name="email" required>
  </section>

  <button type="submit">Get Your AI Readiness Compass</button>
</form>
```

### Stripe Integration Pattern
```javascript
// static/js/compass-payment.js
const stripe = Stripe('pk_test_...');
const elements = stripe.elements();
const card = elements.create('card');
card.mount('#stripe-elements');

async function handleSubmit(event) {
  event.preventDefault();

  // Create payment intent on backend (manual capture)
  const response = await fetch('/api/compass/create-payment-intent', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email: formData.email})
  });
  const {clientSecret, paymentIntentId} = await response.json();

  // Confirm payment with Stripe (authorizes but doesn't capture)
  const {error, paymentIntent} = await stripe.confirmCardPayment(
    clientSecret,
    {payment_method: {card: card}}
  );

  if (error) {
    showError(error.message);
  } else if (paymentIntent.status === 'requires_capture') {
    // Payment authorized - submit Compass request
    submitCompassRequest(paymentIntentId);
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

# Run Compass tests only
python -m pytest tests/unit/contexts/compass/ -v

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

# Application Settings
APP_ENV=development
APP_DEBUG=true
APP_HOST=127.0.0.1
APP_PORT=8000

# Stripe Payment (Required for payments)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
COMPASS_PRICE_CENTS=49700
COMPASS_TEST_MODE=true

# QA Settings
QA_MODEL=claude-sonnet-4-20250514
QA_MIN_PASS_SCORE=7

# Web Research (Optional)
TAVILY_API_KEY=your-tavily-key
ENABLE_WEB_RESEARCH=true
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
├── feature/*     # New features (feature/add-compass-webhook)
├── fix/*         # Bug fixes (fix/stripe-capture-error)
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
feat(compass): add research agent parallel execution
fix(compass): handle empty company website gracefully
refactor(qa): extract validation logic to separate module
test(compass): add integration tests for report generation
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
gh pr create --title "feat: add compass webhook" --body "## Summary\n- Added Stripe webhook handling\n- Implemented payment capture after QA"

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
