# AI Readiness Compass - Implementation Roadmap
## Quick Start Guide for Claude Code Agents

**Document Version**: 1.0.0
**Created**: 2025-12-31
**Purpose**: Actionable implementation guide for refactoring agents

---

## TABLE OF CONTENTS

1. [Overview](#1-overview)
2. [Prerequisites & Setup](#2-prerequisites--setup)
3. [Phase 1: Core Infrastructure (Week 1-2)](#3-phase-1-core-infrastructure-week-1-2)
4. [Phase 2: Payment Integration (Week 2-3)](#4-phase-2-payment-integration-week-2-3)
5. [Phase 3: Customer Communication (Week 3-4)](#5-phase-3-customer-communication-week-3-4)
6. [Phase 4: Background Processing (Week 4-5)](#6-phase-4-background-processing-week-4-5)
7. [Phase 5: Polish & Production (Week 5-6)](#7-phase-5-polish--production-week-5-6)
8. [Testing Strategy](#8-testing-strategy)
9. [Deployment Checklist](#9-deployment-checklist)
10. [Troubleshooting Guide](#10-troubleshooting-guide)

---

## 1. OVERVIEW

### 1.1 What We're Building

Transform the AI Readiness Compass from a working MVP (45% production-ready) into a fully autonomous SaaS product (95% production-ready) by adding:

1. **Payment Processing** (Stripe integration)
2. **Data Persistence** (PostgreSQL database)
3. **Background Job Processing** (Celery + Redis)
4. **Customer Communication** (Email automation)
5. **Order Tracking** (Status API + frontend)
6. **Self-Service Features** (Refunds, re-downloads, user dashboard)

### 1.2 Success Metrics

- ✅ 100% of submissions require payment before processing
- ✅ 100% of orders persist to database (zero data loss)
- ✅ 99.9% of orders complete without human intervention
- ✅ <5% refund rate
- ✅ <2 second API response times
- ✅ 99.5% uptime

### 1.3 Timeline

**Total Duration**: 6 weeks (parallel work across 3-4 agents recommended)

- **Week 1-2**: Database + models + migrations
- **Week 2-3**: Stripe payment integration
- **Week 3-4**: Email automation + order tracking
- **Week 4-5**: Background job processing + async workflows
- **Week 5-6**: Testing, deployment, production launch

---

## 2. PREREQUISITES & SETUP

### 2.1 Required Accounts & API Keys

Before starting, ensure these are set up:

#### 2.1.1 Stripe Account
```bash
# 1. Create Stripe account at https://stripe.com
# 2. Get test keys from https://dashboard.stripe.com/test/apikeys
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx  # Created after webhook setup

# 3. Get live keys (for production)
STRIPE_SECRET_KEY_LIVE=sk_live_xxxxx
STRIPE_PUBLISHABLE_KEY_LIVE=pk_live_xxxxx
```

#### 2.1.2 Production Database (PostgreSQL)
```bash
# Option 1: Railway (Recommended)
# - Visit https://railway.app
# - Create new project → PostgreSQL
# - Copy DATABASE_URL

# Option 2: Supabase
# - Visit https://supabase.com
# - Create new project → Get connection string

# Option 3: Neon
# - Visit https://neon.tech
# - Create new project → Serverless Postgres

DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

#### 2.1.3 Redis (Task Queue)
```bash
# Option 1: Redis Cloud (Recommended)
# - Visit https://redis.com/try-free/
# - Create free database
# - Copy connection URL

# Option 2: Railway Redis addon

REDIS_URL=redis://default:pass@host:port
```

#### 2.1.4 Production Hosting
```bash
# Option 1: Railway (Recommended for simplicity)
# - Visit https://railway.app
# - Connect GitHub repo
# - Auto-deploys on push to main

# Option 2: Render
# - Visit https://render.com
# - Create new Web Service from GitHub

# Option 3: Fly.io (More complex, better control)
```

### 2.2 Development Environment Setup

```bash
# 1. Clone repository
cd C:\Users\PeteG\PycharmProjects\learnClaude

# 2. Create virtual environment
cd workflow_system
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install new dependencies for refactoring
pip install \
    "sqlalchemy[asyncio]>=2.0.0" \
    "alembic>=1.13.0" \
    "asyncpg>=0.29.0" \
    "psycopg2-binary>=2.9.0" \
    "stripe>=7.0.0" \
    "celery[redis]>=5.3.0" \
    "redis>=5.0.0"

# 5. Update requirements.txt
pip freeze > requirements.txt

# 6. Set up environment variables
cp .env.example .env
# Edit .env with actual values

# 7. Initialize database
alembic upgrade head

# 8. Run tests to verify setup
python -m pytest tests/ -v
```

### 2.3 Project Structure After Refactoring

```
workflow_system/
├── models/                    # NEW: Database models (SQLAlchemy)
│   ├── __init__.py
│   ├── base.py
│   ├── customer.py
│   ├── order.py
│   ├── payment.py
│   └── refund.py
├── database/                  # NEW: Database management
│   ├── __init__.py
│   ├── session.py            # Session factory
│   └── migrations/           # Alembic migrations
├── infrastructure/
│   ├── ai/                   # EXISTING: Claude API
│   ├── email/                # EXISTING: Gmail/SMTP
│   ├── storage/              # EXISTING: Google Sheets
│   ├── payment/              # NEW: Stripe adapter
│   │   ├── stripe_adapter.py
│   │   └── models.py
│   └── database/             # NEW: Repositories
│       ├── repository.py
│       ├── customer_repository.py
│       ├── order_repository.py
│       ├── payment_repository.py
│       └── refund_repository.py
├── tasks/                    # NEW: Celery tasks
│   ├── __init__.py
│   ├── celery_app.py        # Celery configuration
│   ├── workflow_processing.py  # Background workflow jobs
│   └── email_tasks.py       # Background email jobs
├── web/
│   ├── api/
│   │   ├── workflows.py     # MODIFIED: Add database persistence
│   │   ├── orders.py        # NEW: Order tracking endpoints
│   │   ├── payment.py       # NEW: Payment endpoints
│   │   └── webhooks.py      # NEW: Stripe webhooks
│   └── ui/
│       ├── templates/
│       │   ├── submit.html   # MODIFIED: Add Stripe Elements
│       │   ├── status.html   # NEW: Order status page
│       │   └── dashboard.html  # NEW: User dashboard
│       └── static/
│           ├── css/
│           │   └── payment.css  # NEW: Payment form styles
│           └── js/
│               ├── payment.js   # NEW: Stripe checkout logic
│               └── status.js    # NEW: Status polling logic
├── contexts/                # EXISTING: Keep as-is (already production-ready)
│   ├── workflow/
│   ├── qa/
│   └── testing/
└── tests/
    ├── unit/
    │   ├── test_models.py    # NEW: Test database models
    │   ├── test_repositories.py  # NEW: Test repositories
    │   └── test_stripe.py    # NEW: Test Stripe integration
    ├── integration/
    │   ├── test_payment_flow.py  # NEW: End-to-end payment tests
    │   └── test_order_tracking.py  # NEW: Order status tests
    └── conftest.py          # MODIFIED: Add database fixtures
```

---

## 3. PHASE 1: CORE INFRASTRUCTURE (WEEK 1-2)

**Goal**: Set up database models, migrations, and repositories

**Priority**: P0 (Blocking)

**Acceptance Criteria**:
- [ ] All database models created and tested
- [ ] Alembic migrations working
- [ ] Repositories implement CRUD operations
- [ ] Unit tests passing for all models
- [ ] Database can be seeded with test data

### 3.1 Task Breakdown

#### Task 1.1: Create Database Models (2 days)
**Assigned to**: Database Agent

```bash
# Files to create:
workflow_system/models/base.py
workflow_system/models/customer.py
workflow_system/models/order.py
workflow_system/models/payment.py
workflow_system/models/refund.py
```

**Implementation Steps**:
1. Create `models/base.py` with SQLAlchemy Base + TimestampMixin
2. Create `models/customer.py` with Customer model (email unique constraint)
3. Create `models/order.py` with Order model (run_id, status, results JSON)
4. Create `models/payment.py` with Payment model (Stripe payment intent ID)
5. Create `models/refund.py` with Refund model (auto-approval logic)
6. Add indexes on frequently queried columns (email, run_id, created_at)
7. Add relationships between models (customer → orders → payment)

**Validation**:
```python
# Test that models can be imported
from models.customer import Customer
from models.order import Order, OrderStatus
from models.payment import Payment, PaymentStatus
from models.refund import Refund, RefundStatus

# Verify enums
assert OrderStatus.PAYMENT_PENDING.value == "payment_pending"
assert PaymentStatus.SUCCEEDED.value == "succeeded"
```

**Reference**: See `REFACTORING_SPECIFICATION.md` Section 6.1.2 for complete model code

---

#### Task 1.2: Set Up Database Session Management (1 day)
**Assigned to**: Database Agent

```bash
# Files to create:
workflow_system/database/__init__.py
workflow_system/database/session.py
```

**Implementation Steps**:
1. Create async engine with connection pooling
2. Create session factory (AsyncSessionLocal)
3. Create `get_session()` dependency for FastAPI
4. Create `session_scope()` context manager for non-FastAPI code
5. Configure pool size, timeout, and retry logic

**Validation**:
```python
# Test async session
from database.session import get_session, session_scope

async def test_session():
    async with session_scope() as session:
        # Should work
        result = await session.execute("SELECT 1")
        assert result.scalar() == 1
```

---

#### Task 1.3: Set Up Alembic Migrations (1 day)
**Assigned to**: Database Agent

```bash
# Commands to run:
cd workflow_system
alembic init database/migrations
alembic revision -m "Initial schema"
alembic upgrade head
```

**Implementation Steps**:
1. Run `alembic init database/migrations`
2. Configure `alembic.ini` with database URL
3. Update `database/migrations/env.py` to import models
4. Create initial migration (001_initial_schema.py)
5. Test upgrade and downgrade
6. Verify all tables created with correct indexes

**Validation**:
```bash
# Should create tables
alembic upgrade head

# Check tables exist
psql $DATABASE_URL -c "\dt"
# Should show: customers, orders, payments, refunds

# Should rollback
alembic downgrade -1

# Should be repeatable
alembic upgrade head
```

---

#### Task 1.4: Create Repository Layer (2 days)
**Assigned to**: Database Agent

```bash
# Files to create:
workflow_system/infrastructure/database/repository.py
workflow_system/infrastructure/database/customer_repository.py
workflow_system/infrastructure/database/order_repository.py
workflow_system/infrastructure/database/payment_repository.py
workflow_system/infrastructure/database/refund_repository.py
```

**Implementation Steps**:
1. Create generic `Repository` base class with CRUD methods
2. Create `CustomerRepository` with email dedup logic
3. Create `OrderRepository` with status transition methods
4. Create `PaymentRepository` with Stripe ID lookups
5. Create `RefundRepository` with auto-approval logic
6. Add business logic methods (e.g., `mark_completed`, `increment_download_count`)

**Validation**:
```python
# Test repositories
from infrastructure.database.order_repository import OrderRepository
from database.session import session_scope

async def test_order_repository():
    async with session_scope() as session:
        repo = OrderRepository(session)

        # Create order
        order = await repo.create(
            run_id="test-123",
            customer_id=1,
            tier="Standard",
            status="payment_pending"
        )

        # Get by run_id
        found = await repo.get_by_run_id("test-123")
        assert found.id == order.id

        # Mark completed
        updated = await repo.mark_completed(
            order.id,
            workflow_result={"test": "data"}
        )
        assert updated.status == "completed"
```

**Reference**: See `REFACTORING_SPECIFICATION.md` Section 6.1.3 for repository pattern code

---

#### Task 1.5: Write Unit Tests for Models & Repositories (2 days)
**Assigned to**: Testing Agent

```bash
# Files to create:
workflow_system/tests/unit/models/test_customer.py
workflow_system/tests/unit/models/test_order.py
workflow_system/tests/unit/models/test_payment.py
workflow_system/tests/unit/models/test_refund.py
workflow_system/tests/unit/repositories/test_customer_repository.py
workflow_system/tests/unit/repositories/test_order_repository.py
workflow_system/tests/unit/repositories/test_payment_repository.py
workflow_system/tests/unit/repositories/test_refund_repository.py
```

**Implementation Steps**:
1. Create pytest fixtures for test database (SQLite in-memory)
2. Test model creation, validation, and relationships
3. Test repository CRUD operations
4. Test business logic methods (status transitions, etc.)
5. Test error handling (duplicate emails, invalid state transitions)
6. Ensure 100% code coverage for models + repositories

**Validation**:
```bash
# Run tests
cd workflow_system
python -m pytest tests/unit/models/ -v
python -m pytest tests/unit/repositories/ -v

# Check coverage
python -m pytest tests/unit/ --cov=models --cov=infrastructure/database --cov-report=html
# Target: 100% coverage
```

---

### 3.2 Phase 1 Acceptance Checklist

Before proceeding to Phase 2, verify:

- [ ] All 4 models created (Customer, Order, Payment, Refund)
- [ ] Database migrations work (upgrade/downgrade)
- [ ] All 4 repositories created with full CRUD
- [ ] Unit tests passing (100% coverage target)
- [ ] Can create/read/update/delete orders in test environment
- [ ] Indexes verified on all foreign keys and query columns
- [ ] No SQL injection vulnerabilities (using parameterized queries)
- [ ] Database session cleanup working (no connection leaks)

---

## 4. PHASE 2: PAYMENT INTEGRATION (WEEK 2-3)

**Goal**: Integrate Stripe payment processing

**Priority**: P0 (Blocking)

**Acceptance Criteria**:
- [ ] Stripe checkout flow working end-to-end
- [ ] Payment success webhook creates order record
- [ ] Payment failure webhook handled gracefully
- [ ] Test mode works with Stripe test cards
- [ ] Production mode ready (keys configured but not active)

### 4.1 Task Breakdown

#### Task 2.1: Create Stripe Adapter (1 day)
**Assigned to**: Payment Agent

```bash
# Files to create:
workflow_system/infrastructure/payment/__init__.py
workflow_system/infrastructure/payment/stripe_adapter.py
workflow_system/infrastructure/payment/models.py
```

**Implementation Steps**:
1. Install `stripe` SDK: `pip install stripe`
2. Create `StripeAdapter` class with methods:
   - `create_payment_intent(amount_cents, metadata)`
   - `get_payment_intent(payment_intent_id)`
   - `create_refund(payment_intent_id, amount_cents)`
   - `verify_webhook_signature(payload, signature, secret)`
3. Add error handling for Stripe API errors
4. Add structured logging for all Stripe calls
5. Add retry logic with exponential backoff

**Validation**:
```python
# Test Stripe adapter
from infrastructure.payment.stripe_adapter import StripeAdapter

adapter = StripeAdapter(api_key="sk_test_xxxxx")

# Create payment intent
intent = await adapter.create_payment_intent(
    amount_cents=14900,  # $149.00
    metadata={"order_id": "123", "tier": "Standard"}
)
assert intent["amount"] == 14900
assert "client_secret" in intent

# Get payment intent
retrieved = await adapter.get_payment_intent(intent["id"])
assert retrieved["id"] == intent["id"]
```

**Reference**: See `REFACTORING_SPECIFICATION.md` Section 6.2.2 for complete adapter code

---

#### Task 2.2: Create Payment API Endpoints (2 days)
**Assigned to**: Backend Agent

```bash
# Files to create:
workflow_system/web/api/payment.py
```

**Implementation Steps**:
1. Create `/api/payment/create-intent` endpoint
2. Validate tier pricing (Starter=$49, Standard=$149, Premium=$399)
3. Create or find customer by email (dedupe logic)
4. Create order record (status='payment_pending')
5. Create Stripe payment intent
6. Create payment record in database
7. Return client_secret to frontend
8. Add comprehensive error handling

**Validation**:
```bash
# Test payment intent creation
curl -X POST http://localhost:8000/api/payment/create-intent \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "Standard",
    "company_name": "Test Corp",
    "email": "test@example.com",
    "contact_name": "Test User",
    "prompt": "Test prompt"
  }'

# Should return:
{
  "client_secret": "pi_xxxxx_secret_xxxxx",
  "amount_cents": 14900,
  "order_id": "abc12345"
}
```

**Reference**: See `REFACTORING_SPECIFICATION.md` Section 6.2.3 for endpoint code

---

#### Task 2.3: Create Stripe Webhook Handler (2 days)
**Assigned to**: Backend Agent

```bash
# Files to create:
workflow_system/web/api/webhooks.py
```

**Implementation Steps**:
1. Create `/api/webhooks/stripe` endpoint
2. Verify webhook signature (security critical!)
3. Handle `payment_intent.succeeded` event:
   - Update payment status to 'succeeded'
   - Send confirmation email
   - Queue background job to process order
4. Handle `payment_intent.payment_failed` event:
   - Update payment status to 'failed'
   - Send failure notification
5. Handle `charge.refunded` event:
   - Update refund status to 'processed'
   - Send refund confirmation
6. Log all events for debugging

**Validation**:
```bash
# Test webhook locally using Stripe CLI
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# Trigger test events
stripe trigger payment_intent.succeeded
stripe trigger payment_intent.payment_failed

# Check logs
tail -f workflow_system.log | grep "stripe_webhook"
```

**Security Note**: ALWAYS verify webhook signatures. Unverified webhooks can be spoofed to fake successful payments.

**Reference**: See `REFACTORING_SPECIFICATION.md` Section 6.2.4 for webhook handler code

---

#### Task 2.4: Update Frontend with Stripe Elements (2 days)
**Assigned to**: Frontend Agent

```bash
# Files to modify:
workflow_system/web/ui/templates/submit.html
workflow_system/web/ui/static/js/payment.js
workflow_system/web/ui/static/css/payment.css
```

**Implementation Steps**:
1. Add Stripe.js script tag to submit.html
2. Create Stripe Elements card input widget
3. Handle form submission:
   - Call `/api/payment/create-intent` to get client_secret
   - Call `stripe.confirmCardPayment(client_secret, card)` to process payment
   - Show loading spinner during payment
4. Handle payment success:
   - Redirect to `/status/{order_id}` page
5. Handle payment failure:
   - Display error message to user
6. Add styling for payment form

**Validation**:
```bash
# Manual testing
1. Start server: uvicorn workflow_system.web.app:app --reload
2. Visit http://localhost:8000/submit
3. Fill out form
4. Use test card: 4242 4242 4242 4242
5. Submit payment
6. Should redirect to status page

# Test failure cases
- Use declined card: 4000 0000 0000 0002 (should show error)
- Use authentication required: 4000 0025 0000 3155 (should trigger 3D Secure)
```

**Reference Stripe Elements**: https://stripe.com/docs/payments/accept-a-payment

---

#### Task 2.5: Write Integration Tests for Payment Flow (1 day)
**Assigned to**: Testing Agent

```bash
# Files to create:
workflow_system/tests/integration/test_payment_flow.py
```

**Implementation Steps**:
1. Test payment intent creation endpoint
2. Test webhook handling (mock Stripe events)
3. Test end-to-end flow:
   - Submit form → Create intent → Webhook success → Order created
4. Test payment failure scenarios
5. Test webhook signature verification
6. Test duplicate payment prevention

**Validation**:
```bash
cd workflow_system
python -m pytest tests/integration/test_payment_flow.py -v
```

---

### 4.2 Phase 2 Acceptance Checklist

Before proceeding to Phase 3, verify:

- [ ] Stripe adapter working (create intent, get intent, refund)
- [ ] Payment API endpoint creates order + payment records
- [ ] Webhook handler verifies signatures correctly
- [ ] Webhook handles payment success (creates order, queues job)
- [ ] Webhook handles payment failure (logs error)
- [ ] Frontend Stripe Elements integration working
- [ ] Test cards work (4242..., 4000...)
- [ ] Integration tests passing
- [ ] No hardcoded API keys (all from environment variables)
- [ ] Webhook endpoint secured (signature verification)

---

## 5. PHASE 3: CUSTOMER COMMUNICATION (WEEK 3-4)

**Goal**: Automated email flow for order lifecycle

**Priority**: P0 (Blocking)

**Acceptance Criteria**:
- [ ] Payment confirmation email sent immediately
- [ ] Processing complete email with report attached
- [ ] Processing failed email with auto-refund notice
- [ ] All emails use professional HTML templates
- [ ] Email delivery tracked in database

### 5.1 Task Breakdown

#### Task 3.1: Create Email Templates (2 days)
**Assigned to**: Frontend Agent

```bash
# Files to create:
workflow_system/web/ui/templates/emails/payment_confirmation.html
workflow_system/web/ui/templates/emails/processing_complete.html
workflow_system/web/ui/templates/emails/processing_failed.html
workflow_system/web/ui/templates/emails/refund_processed.html
```

**Implementation Steps**:
1. Design HTML email template structure (header, body, footer)
2. Create payment confirmation template:
   - Order number, tier, amount, status page link
3. Create processing complete template:
   - Download link, summary stats, CTA to download
4. Create processing failed template:
   - Apology, auto-refund notice, support contact
5. Create refund processed template:
   - Refund amount, timeline (5-10 days)
6. Test email rendering (use Mailtrap or similar)

**Validation**:
```python
# Test template rendering
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("web/ui/templates/emails"))
template = env.get_template("payment_confirmation.html")

html = template.render(
    order_number="ORD-2025-0001",
    tier="Standard",
    amount="$149.00",
    status_url="https://example.com/status/abc123"
)

# Verify rendered HTML
assert "ORD-2025-0001" in html
assert "$149.00" in html
```

---

#### Task 3.2: Implement Email Service Layer (2 days)
**Assigned to**: Backend Agent

```bash
# Files to create:
workflow_system/shared/email_service.py
```

**Implementation Steps**:
1. Create `EmailService` class with methods:
   - `send_payment_confirmation(order)`
   - `send_processing_complete(order, workflow_result)`
   - `send_processing_failed(order, error_message)`
   - `send_refund_processed(order, refund)`
2. Integrate with existing Gmail/SMTP adapter
3. Add template rendering with Jinja2
4. Add attachment support (PDF reports)
5. Add retry logic (3 attempts with exponential backoff)
6. Log all email sends to database (audit trail)

**Validation**:
```python
# Test email service
from shared.email_service import EmailService
from infrastructure.email.smtp_adapter import SMTPAdapter

email_service = EmailService(email_client=SMTPAdapter(...))

# Send confirmation
await email_service.send_payment_confirmation(order)

# Verify email sent
assert order.email_sent_at is not None
```

---

#### Task 3.3: Integrate Email Sending into Workflow (1 day)
**Assigned to**: Backend Agent

**Files to modify**:
- `web/api/webhooks.py` (add email call after payment success)
- `tasks/workflow_processing.py` (add email call after completion)

**Implementation Steps**:
1. After payment success webhook: Send confirmation email
2. After workflow processing complete: Send completion email with report
3. After workflow processing fails: Send failure email + trigger refund
4. After refund processed: Send refund confirmation email
5. Handle email delivery failures gracefully (log but don't block)

**Validation**:
End-to-end test:
1. Submit form with valid payment
2. Webhook triggers → Confirmation email sent
3. Background job processes order
4. Completion email sent with report
5. Verify both emails received

---

### 5.2 Phase 3 Acceptance Checklist

Before proceeding to Phase 4, verify:

- [ ] All 4 email templates created and styled
- [ ] Email service implements all 4 email types
- [ ] Emails rendered correctly (test in Gmail, Outlook)
- [ ] Attachments work (PDF reports sent correctly)
- [ ] Retry logic handles transient failures
- [ ] Email sending doesn't block API responses
- [ ] All email sends logged to database
- [ ] Links in emails point to correct URLs (HTTPS in production)

---

## 6. PHASE 4: BACKGROUND PROCESSING (WEEK 4-5)

**Goal**: Asynchronous order processing with Celery

**Priority**: P1 (Important)

**Acceptance Criteria**:
- [ ] Orders processed in background (non-blocking)
- [ ] Celery workers running reliably
- [ ] Failed jobs retry automatically
- [ ] Job status queryable via API
- [ ] Workers scale horizontally

### 6.1 Task Breakdown

#### Task 4.1: Set Up Celery (1 day)
**Assigned to**: Backend Agent

```bash
# Files to create:
workflow_system/tasks/__init__.py
workflow_system/tasks/celery_app.py
```

**Implementation Steps**:
1. Install Celery: `pip install celery[redis]`
2. Create Celery app configuration
3. Configure Redis as message broker
4. Set up task routing (high/default/low priority queues)
5. Configure retry behavior (max retries, backoff)
6. Add result backend (Redis or database)

**Validation**:
```bash
# Start Celery worker
cd workflow_system
celery -A tasks.celery_app worker --loglevel=info

# Should show:
# - Connected to redis://...
# - Registered tasks
# - Ready to process tasks
```

---

#### Task 4.2: Create Background Tasks (2 days)
**Assigned to**: Backend Agent

```bash
# Files to create:
workflow_system/tasks/workflow_processing.py
workflow_system/tasks/email_tasks.py
```

**Implementation Steps**:
1. Create `process_order_task(order_id)`:
   - Load order from database
   - Call WorkflowEngine.process_inquiry()
   - Save results to database
   - Mark order as completed
   - Queue email sending
2. Create `send_email_task(email_type, order_id)`:
   - Load order from database
   - Render email template
   - Send via SMTP
   - Log delivery
3. Add error handling and retry logic
4. Add task monitoring (log task start, end, duration)

**Validation**:
```python
# Test task execution
from tasks.workflow_processing import process_order_task

# Queue task
task = process_order_task.delay(order_id=123)

# Check status
print(task.state)  # PENDING → STARTED → SUCCESS

# Get result
result = task.get(timeout=60)
print(result)  # Order processing result
```

---

#### Task 4.3: Update Webhook to Queue Tasks (1 day)
**Assigned to**: Backend Agent

**Files to modify**:
- `web/api/webhooks.py`

**Implementation Steps**:
1. After payment success: Queue `process_order_task.delay(order_id)`
2. After payment success: Queue `send_email_task.delay("confirmation", order_id)`
3. Remove synchronous workflow processing from webhook
4. Return webhook response immediately (<500ms)

**Validation**:
```bash
# Test webhook performance
time curl -X POST http://localhost:8000/api/webhooks/stripe \
  -H "Stripe-Signature: ..." \
  -d @test_webhook_event.json

# Should return in <500ms (task queued, not executed)
```

---

### 6.2 Phase 4 Acceptance Checklist

Before proceeding to Phase 5, verify:

- [ ] Celery worker starts without errors
- [ ] Tasks execute successfully in background
- [ ] Failed tasks retry automatically
- [ ] Webhook response time <500ms (tasks queued, not blocking)
- [ ] Order processing completes asynchronously
- [ ] Email sending happens in background
- [ ] Workers can be scaled (multiple workers process tasks)
- [ ] Task monitoring/logging working

---

## 7. PHASE 5: POLISH & PRODUCTION (WEEK 5-6)

**Goal**: Production readiness, testing, deployment

**Priority**: P0 (Blocker for launch)

**Acceptance Criteria**:
- [ ] All tests passing (unit + integration + end-to-end)
- [ ] Security audit complete (OWASP Top 10)
- [ ] Performance testing complete (load testing)
- [ ] Production environment configured
- [ ] Monitoring and alerting set up
- [ ] Documentation complete

### 7.1 Final Implementation Tasks

#### Task 5.1: Order Status API + Frontend (2 days)
**Assigned to**: Full Stack Agent

```bash
# Files to create:
workflow_system/web/api/orders.py
workflow_system/web/ui/templates/status.html
workflow_system/web/ui/static/js/status.js
```

**Implementation Steps**:
1. Create GET `/api/orders/{order_id}/status` endpoint
2. Return order status, progress, estimated completion time
3. Create status page UI with progress bar
4. Implement polling (frontend calls API every 5 seconds)
5. Show download button when status='completed'

---

#### Task 5.2: Self-Service Refund System (2 days)
**Assigned to**: Full Stack Agent

```bash
# Files to create:
workflow_system/web/api/refunds.py
workflow_system/web/ui/templates/refund.html
```

**Implementation Steps**:
1. Create POST `/api/refunds/request` endpoint
2. Implement auto-approval logic:
   - <7 days since purchase AND
   - Report not downloaded AND
   - First refund for customer
   → Auto-approve
3. For complex cases, flag for manual review
4. Process approved refunds via Stripe API
5. Send refund confirmation email

---

#### Task 5.3: Production Security Hardening (1 day)
**Assigned to**: Security Agent

**Implementation Steps**:
1. Enable HTTPS redirect
2. Set security headers (CSP, HSTS, X-Frame-Options)
3. Add rate limiting (5 submissions per IP per hour)
4. Add CAPTCHA to submission form
5. Validate all input (prevent XSS, SQL injection)
6. Rotate API keys
7. Enable database connection encryption

---

#### Task 5.4: Load Testing & Performance Optimization (1 day)
**Assigned to**: Performance Agent

**Implementation Steps**:
1. Run load testing (Locust or k6)
2. Test 100 concurrent users submitting forms
3. Identify bottlenecks (database queries, AI calls, etc.)
4. Optimize slow queries (add indexes, caching)
5. Enable database connection pooling
6. Configure CDN for static assets

**Target Performance**:
- API response time: <500ms (95th percentile)
- Database queries: <100ms (95th percentile)
- Workflow processing: <12 hours (95th percentile)

---

#### Task 5.5: Deployment to Production (2 days)
**Assigned to**: DevOps Agent

**Implementation Steps**:
1. Configure production environment variables
2. Set up PostgreSQL database (managed service)
3. Set up Redis queue (managed service)
4. Deploy FastAPI app to Railway/Render
5. Deploy Celery workers to separate instances
6. Configure domain and SSL certificate
7. Set up Stripe webhook URL (HTTPS required)
8. Enable production mode (Stripe live keys)
9. Test end-to-end flow in production
10. Monitor for errors

**Deployment Checklist**:
- [ ] DATABASE_URL points to production PostgreSQL
- [ ] REDIS_URL points to production Redis
- [ ] STRIPE_SECRET_KEY is live key (sk_live_...)
- [ ] STRIPE_WEBHOOK_SECRET matches production webhook
- [ ] Domain configured with SSL (HTTPS working)
- [ ] Environment variables secured (not in code)
- [ ] Backup strategy configured (daily database backups)
- [ ] Monitoring enabled (Sentry, UptimeRobot)

---

## 8. TESTING STRATEGY

### 8.1 Test Coverage Requirements

**Unit Tests** (Target: 90%+ coverage):
- All database models
- All repositories
- Stripe adapter
- Email service
- Business logic (status transitions, auto-approval, etc.)

**Integration Tests** (Target: Critical paths covered):
- Payment flow (create intent → webhook → order creation)
- Order processing (queue task → process → save results)
- Email sending (template rendering → SMTP)
- Refund flow (request → approve → process → notify)

**End-to-End Tests** (Target: Happy path + critical failures):
- Full user journey: Submit form → Pay → Receive email → Download report
- Payment failure: Submit → Card declined → Error shown
- Refund: Request refund → Auto-approved → Email sent

### 8.2 Test Execution

```bash
# Run all tests
cd workflow_system
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run specific test suites
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v

# Run tests in parallel (faster)
python -m pytest tests/ -n auto

# Run tests with real APIs (EXPENSIVE - use sparingly)
python -m pytest tests/ -m real_api
```

---

## 9. DEPLOYMENT CHECKLIST

### 9.1 Pre-Launch Checklist

**Infrastructure**:
- [ ] PostgreSQL database provisioned
- [ ] Redis queue provisioned
- [ ] Web server deployed
- [ ] Celery workers deployed
- [ ] Domain configured (DNS records)
- [ ] SSL certificate active (HTTPS working)

**Configuration**:
- [ ] All environment variables set
- [ ] Stripe webhooks configured (production URL)
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Static assets deployed to CDN
- [ ] CORS configured correctly

**Security**:
- [ ] HTTPS enforced (HTTP → HTTPS redirect)
- [ ] Security headers set
- [ ] Rate limiting enabled
- [ ] CAPTCHA enabled on forms
- [ ] Secrets rotated (no default/test keys in production)
- [ ] Database encryption enabled

**Monitoring**:
- [ ] Error tracking enabled (Sentry)
- [ ] Uptime monitoring enabled (UptimeRobot)
- [ ] Log aggregation working (structured logs viewable)
- [ ] Alerting configured (email/Slack for critical errors)
- [ ] Dashboard created (Metabase or similar)

**Testing**:
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] End-to-end flow tested in production
- [ ] Test payment completed successfully
- [ ] Test webhook received and processed
- [ ] Test email sent and received

**Legal/Compliance**:
- [ ] Terms of Service published
- [ ] Privacy Policy published
- [ ] Refund Policy published
- [ ] Cookie consent banner (if EU customers)

---

## 10. TROUBLESHOOTING GUIDE

### 10.1 Common Issues & Solutions

#### Issue: Database Connection Errors

**Symptoms**:
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions**:
1. Verify DATABASE_URL is correct
2. Check database server is running
3. Verify firewall/security group allows connections
4. Check connection pool size (increase if needed)
5. Verify SSL mode (some providers require `sslmode=require`)

---

#### Issue: Stripe Webhook Not Receiving Events

**Symptoms**:
- Payment succeeds but order not created
- Webhook logs show no events received

**Solutions**:
1. Verify webhook URL is HTTPS (Stripe requires SSL)
2. Check Stripe dashboard → Webhooks → Event deliveries
3. Verify webhook signature verification code is correct
4. Test locally with Stripe CLI: `stripe listen --forward-to localhost:8000/api/webhooks/stripe`
5. Check firewall allows incoming requests from Stripe IPs

---

#### Issue: Celery Tasks Not Executing

**Symptoms**:
- Tasks queued but never complete
- Worker logs show no activity

**Solutions**:
1. Verify Redis connection: `redis-cli ping`
2. Check worker is running: `celery -A tasks.celery_app inspect active`
3. Verify task routing configuration
4. Check worker logs for errors
5. Increase worker concurrency if CPU-bound

---

#### Issue: High Payment Failure Rate

**Symptoms**:
- >10% of payments failing
- Users reporting card declines

**Solutions**:
1. Check Stripe dashboard for decline reasons
2. Enable 3D Secure (SCA compliance for EU)
3. Add retry logic for network errors
4. Improve error messaging to users
5. Consider alternative payment methods (PayPal, etc.)

---

## CONCLUSION

This implementation roadmap provides a structured approach to refactoring the AI Readiness Compass from MVP to production. By following these phases sequentially, Claude Code agents can systematically build the missing components while maintaining the quality and architecture of the existing system.

**Key Success Factors**:
1. **Complete Phase 1 First**: Database layer is foundation for everything else
2. **Test Continuously**: Write tests as you go, not at the end
3. **Deploy Early**: Test in production-like environment ASAP
4. **Monitor Closely**: Set up monitoring from day 1, not after launch
5. **Communicate Progress**: Update project stakeholders weekly

**Timeline Summary**:
- Week 1-2: Database layer (models, migrations, repositories)
- Week 2-3: Stripe integration (payment processing)
- Week 3-4: Email automation (customer communication)
- Week 4-5: Background jobs (Celery + async processing)
- Week 5-6: Polish, testing, deployment

**Expected Outcome**: A production-ready SaaS application capable of processing 100-500 paid orders per month with 99.9% automation and minimal manual intervention.

---

**Document Version**: 1.0.0
**Last Updated**: 2025-12-31
**Next Review**: After Phase 1 completion
