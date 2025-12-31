# AI Readiness Compass - Complete Refactoring Specification
## From MVP to Production SaaS Platform

**Document Version**: 1.0.0
**Created**: 2025-12-31
**Author**: Product Engineering Team
**Target Audience**: Claude Code Agents for Implementation

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [High-Level Goals & Product Vision](#2-high-level-goals--product-vision)
3. [Current System Analysis](#3-current-system-analysis)
4. [Business Requirements](#4-business-requirements)
5. [Technical Architecture Specifications](#5-technical-architecture-specifications)
6. [Component-by-Component Refactoring Plan](#6-component-by-component-refactoring-plan)
7. [Data Models & Database Schema](#7-data-models--database-schema)
8. [API Specifications](#8-api-specifications)
9. [Frontend Specifications](#9-frontend-specifications)
10. [Quality Assurance & Testing](#10-quality-assurance--testing)
11. [Security & Compliance](#11-security--compliance)
12. [Deployment & Operations](#12-deployment--operations)
13. [Monitoring & Analytics](#13-monitoring--analytics)
14. [Migration Strategy](#14-migration-strategy)
15. [Success Metrics & KPIs](#15-success-metrics--kpis)
16. [Implementation Roadmap](#16-implementation-roadmap)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project Overview

**Project Name**: AI Readiness Compass - Production Refactoring
**Type**: Complete system refactoring from MVP to production SaaS
**Timeline**: 6-8 weeks
**Investment**: High (complete architectural overhaul)
**Expected ROI**: Transform free MVP into revenue-generating SaaS ($15K-$30K MRR potential)

### 1.2 Current State Assessment

**Readiness Score**: 45/100 (see PRODUCTION_READINESS_AUDIT.md)

**Strengths** (85% complete):
- ✅ Core workflow engine is production-quality with sophisticated self-consistency voting
- ✅ QA validation system with deterministic and probabilistic validators
- ✅ 179+ tests passing (unit + integration)
- ✅ Clean architecture with dependency injection
- ✅ Professional UI/UX with submission form
- ✅ Email delivery working (Gmail/SMTP)
- ✅ Google Sheets integration for analytics
- ✅ Structured logging with structlog

**Critical Gaps** (55% incomplete):
- ❌ Zero payment integration (Stripe planned but not implemented)
- ❌ No database persistence (models don't exist, data is ephemeral)
- ❌ No user authentication (cannot track customers)
- ❌ No order tracking (TODO stub only)
- ❌ No customer communication flow (order confirmations, status updates)
- ❌ No refund automation
- ❌ No production deployment configuration
- ❌ No legal documentation (TOS, Privacy Policy)

### 1.3 Refactoring Objectives

**Primary Goal**: Transform the AI Readiness Compass from a working MVP into a fully autonomous, revenue-generating SaaS product capable of processing 100-500 paid orders per month with <0.1% manual intervention.

**Success Criteria**:
1. **Revenue Capture**: 100% of submissions are charged via Stripe before processing
2. **Automation**: 99.9% of orders complete without human intervention
3. **Persistence**: 100% of orders, customers, and payments stored in database
4. **Communication**: Automated email flow for every order state transition
5. **Self-Service**: Customers can view order status, download results, request refunds
6. **Quality**: Maintain current 85%+ QA pass rate while scaling to 500+ orders/month
7. **Reliability**: 99.5% uptime, <5 second response times, graceful error handling

### 1.4 Business Model

**Product**: AI Readiness Compass - AI-powered business workflow recommendations

**Pricing Tiers**:
- **Starter**: $49/report (3 workflows, basic tools, 24hr delivery)
- **Standard**: $149/report (5 workflows, advanced tools, 12hr delivery, QA guarantee)
- **Premium**: $399/report (8 workflows, custom integrations, 6hr delivery, revision guarantee)

**Target Market**: SMBs (10-500 employees) in service industries looking to implement AI automation

**Revenue Goal**: $15K-$30K MRR (100-200 orders/month) within 6 months of launch

---

## 2. HIGH-LEVEL GOALS & PRODUCT VISION

### 2.1 Product Vision Statement

> "AI Readiness Compass is the fastest way for SMBs to discover their top AI automation opportunities. Submit your business details, pay once, and receive a custom roadmap of implementable AI workflows within 24 hours—no meetings, no consultants, no complexity."

### 2.2 User Experience Goals

#### 2.2.1 For First-Time Customers

**Current Journey** (MVP - Manual):
1. User visits website → Fills out form → Submits
2. **GAP**: No payment collected
3. System processes (4-24 hours) → Email sent
4. **GAP**: No status updates during processing
5. User receives email with results
6. **GAP**: Cannot re-download if email is lost
7. **GAP**: No support channel if issues occur

**Target Journey** (Production - Automated):
1. User visits website → Fills out form
2. User selects tier ($49, $149, $399)
3. User enters payment info via Stripe Checkout → Pays
4. System sends confirmation email immediately ("Payment received, processing started")
5. System processes in background (4-24 hours)
   - Optional: Send "Still processing" update at 12 hours
6. System sends completion email with download link
7. User clicks link → Views report in browser AND receives PDF attachment
8. User can re-download anytime from `/orders/{order_id}/download`
9. User can request refund via `/orders/{order_id}/refund`
10. **Fallback**: If processing fails, automatic refund email sent

#### 2.2.2 For Returning Customers

**Target Journey** (Not currently possible):
1. User visits website → Recognizes email → Logs in via magic link
2. User sees dashboard with past orders
3. User can re-download any previous report
4. User can submit new order (prefilled company info)
5. User can refer friends for discount

### 2.3 Business Operation Goals

#### 2.3.1 99.9% Automation Target

**Manual Processes to Eliminate**:
- ❌ Payment reconciliation (currently impossible - no payments)
- ❌ Order status inquiries ("Where's my report?")
- ❌ Re-send requests (email delivery failures)
- ❌ Refund processing (manual Stripe dashboard)
- ❌ Quality issue handling (persistent QA failures)

**Automation Solutions**:
- ✅ Stripe webhooks handle payment success/failure automatically
- ✅ Status tracking API + frontend allows self-service status checks
- ✅ Email retry logic with exponential backoff (3 attempts over 24 hours)
- ✅ Self-service refund request form → Auto-approved if <7 days + no download
- ✅ QA auditor auto-retries on failure (up to 3 attempts) + auto-refunds if all fail

**Remaining Manual Touchpoints** (<0.1%):
- Complex refund disputes (fraud, chargebacks)
- Severe technical failures (infrastructure outages)
- Feature requests and product feedback

#### 2.3.2 Financial Operations

**Revenue Tracking**:
- Stripe webhook logs all successful payments to database
- Daily revenue reports automated (email to admin@)
- Monthly revenue dashboard (Metabase or similar)

**Refund Management**:
- Auto-approved refunds: <7 days + no download + first refund
- Manual review required: Multiple refunds, downloaded reports, >7 days
- Refund rate target: <5% of orders

**Tax & Compliance**:
- Stripe Tax handles sales tax calculation (if enabled)
- Receipts auto-generated and emailed
- Annual 1099 forms for contractors (if applicable)

---

## 3. CURRENT SYSTEM ANALYSIS

### 3.1 Architecture Overview

**Pattern**: Hexagonal Architecture (Ports & Adapters) with Domain-Driven Design

```
┌─────────────────────────────────────────────────────────────┐
│                      WEB LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   FastAPI    │  │   Jinja2     │  │   Static     │      │
│  │   Routes     │  │  Templates   │  │   Assets     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                   CONTEXTS (Domain Logic)                   │
│  ┌────────────────────────────────────────────────┐         │
│  │  WORKFLOW CONTEXT                              │         │
│  │  - WorkflowEngine (orchestrator)               │         │
│  │  - Voter (consensus logic)                     │         │
│  │  - Selector (hybrid workflow selection)        │         │
│  │  - Models (WorkflowResult, Consensus, etc.)    │         │
│  └────────────────────────────────────────────────┘         │
│  ┌────────────────────────────────────────────────┐         │
│  │  QA CONTEXT                                    │         │
│  │  - QAAuditor (semantic analysis)               │         │
│  │  - ValidationPipeline (orchestrator)           │         │
│  │  - Validators (deterministic + probabilistic)  │         │
│  │  - CallCapture (AI call instrumentation)       │         │
│  └────────────────────────────────────────────────┘         │
│  ┌────────────────────────────────────────────────┐         │
│  │  TESTING CONTEXT                               │         │
│  │  - TestOrchestrator                            │         │
│  │  - TestCases                                   │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│              INFRASTRUCTURE (Adapters)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  ClaudeAPI   │  │  Gmail/SMTP  │  │Google Sheets │      │
│  │  Adapter     │  │   Adapter    │  │   Adapter    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  MISSING:    │  │  MISSING:    │                        │
│  │  Database    │  │  Stripe API  │                        │
│  │  Adapter     │  │  Adapter     │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                CONFIGURATION & DI                           │
│  - Settings (pydantic)                                      │
│  - Container (dependency injection)                         │
│  - Protocols (AIProvider, EmailClient, SheetsClient)        │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Core Workflow Engine Analysis

**File**: `contexts/workflow/engine.py`
**Status**: Production-ready (95% complete)
**LOC**: ~650 lines

**Responsibilities**:
1. Orchestrates the full workflow generation pipeline
2. Manages 5 AI phases: Input Rewrite → Research → Self-Consistency → Grouper → Proposal
3. Integrates QA capture when enabled
4. Handles retry logic for invalid responses

**Key Algorithm** (Self-Consistency Voting):
```python
# Multi-temperature consensus voting
temperatures = [0.3, 0.5, 0.7, 0.85, 1.0]  # 5 parallel calls

# Each call generates 25 workflows (125 total workflows)
responses = await ai_provider.generate_parallel(
    prompt=normalized_prompt,
    temperatures=temperatures,
    max_tokens=16384
)

# Voter counts which workflow name appears most frequently
# Requires 3+ votes (60% of 5) for consensus
consensus = count_votes(responses, min_consensus_votes=3)

if consensus.had_consensus:
    # Strong agreement (3-5 responses agree)
    final_answer = consensus.final_answer
    confidence = 75-100%
else:
    # Fallback: Score all 125 workflows by feasibility + semantic relevance
    final_answer, workflows = rank_workflows_by_score(
        all_responses,
        normalized_prompt=user_question
    )
    confidence = 60-85% (based on score)

# NEW (added 2025-12-28): Hybrid workflow selector
# Selects top 5 from all 125 workflows using:
#   - Semantic relevance (TF-IDF keyword matching with user prompt)
#   - Domain diversity (minimum 3 different functional domains)
#   - Tier-appropriate feasibility (Budget=simple, Premium=advanced)
#   - Metrics impact scoring
selected_top_5 = selector.select_top_5(
    workflows=all_125_workflows,
    tier=tier,
    user_prompt=user_question,
    consensus_strength=consensus.consensus_strength
)
```

**Strengths**:
- ✅ Highly reliable consensus algorithm (reduces hallucinations)
- ✅ Automatic retry on invalid responses (up to 2 retries per temperature)
- ✅ Comprehensive logging for observability
- ✅ QA capture integration (optional)
- ✅ Hybrid selector ensures diverse, relevant workflows

**Weaknesses to Address in Refactoring**:
- ⚠️ No timeout handling (Claude API calls can hang indefinitely)
- ⚠️ No circuit breaker pattern (if Claude API is down, all requests fail)
- ⚠️ No request queuing (all submissions processed immediately → rate limit risk)
- ⚠️ No cost control (5 parallel calls × 16K tokens = expensive for low-tier customers)

### 3.3 QA System Analysis

**Files**:
- `contexts/qa/auditor.py` (semantic analysis)
- `contexts/qa/scoring.py` (validation pipeline)
- `contexts/qa/call_capture.py` (instrumentation)
- `contexts/qa/validators/*.py` (validators)

**Status**: Production-ready (90% complete)
**LOC**: ~1200 lines total

**Architecture**:
```python
# QA Capture wraps AI provider
ai_provider = ClaudeAdapter(api_key=ANTHROPIC_API_KEY)
capturing_provider = CapturingAIAdapter(
    wrapped=ai_provider,
    run_id=run_id,
    validation_pipeline=ValidationPipeline(
        ai_provider=ai_provider,
        run_probabilistic=True,
        probabilistic_sample_rate=1.0
    )
)

# All AI calls automatically captured
response = await capturing_provider.generate(prompt)

# Validations run immediately after each call:
# - Deterministic: JSON validity, truncation, token limits (fast, no API calls)
# - Probabilistic: Semantic relevance, hallucination detection (requires AI calls)

# At end of workflow:
call_store = capturing_provider.call_store  # All captured calls
qa_result = await qa_auditor.audit(workflow_result)  # Semantic analysis

# Aggregate scoring:
workflow_score = WorkflowScorer().score(call_store, qa_result)
# Score: 1-10 (10 = perfect, 7+ = pass, <7 = fail)
```

**Strengths**:
- ✅ Comprehensive validation (9+ validators)
- ✅ Semantic analysis catches workflow mismatches
- ✅ Google Sheets logging for post-mortem analysis
- ✅ Configurable sampling (can run probabilistic checks on subset to save costs)

**Weaknesses to Address**:
- ⚠️ QA calls add latency (extra AI calls for validation)
- ⚠️ No async background processing (blocks user response)
- ⚠️ Google Sheets logging can fail silently (no retries)
- ⚠️ No alerting when QA scores trend downward

### 3.4 Data Flow Analysis

**Current Data Flow** (Ephemeral - No Persistence):
```
┌──────────────┐
│ User submits │
│     form     │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ FastAPI endpoint    │
│ /api/workflows/     │
│      submit         │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────────┐
│ WorkflowEngine.process  │
│ (in-memory processing)  │
│ - Input Rewrite         │
│ - Research Engine       │
│ - Self-Consistency (5x) │
│ - Hybrid Selector       │
│ - Grouper               │
│ - Proposal Generator    │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Email Delivery          │
│ (Gmail/SMTP)            │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ ❌ DATA LOST            │
│ (not saved to database) │
└─────────────────────────┘
```

**Problems**:
1. **No Order Tracking**: Cannot answer "Where's my order?"
2. **No Re-Downloads**: User loses email → Cannot get report again
3. **No Analytics**: Cannot answer "How many customers this month?"
4. **No Refunds**: No payment record to refund
5. **No User History**: Returning customers start from scratch

**Target Data Flow** (Persistent - Database-Backed):
```
┌──────────────┐
│ User submits │
│     form     │
└──────┬───────┘
       │
       ▼
┌────────────────────────┐
│ Stripe Checkout        │
│ (collect payment)      │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│ Stripe Webhook:        │
│ payment_succeeded      │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│ Create Order record    │
│ status='pending'       │
│ (write to DB)          │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│ Send confirmation email│
│ "Processing started"   │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│ Queue background job   │
│ process_order(order_id)│
└──────┬─────────────────┘
       │
       ▼
┌─────────────────────────┐
│ WorkflowEngine.process  │
│ (async background job)  │
└──────┬──────────────────┘
       │
       ▼
┌────────────────────────┐
│ Update Order:          │
│ status='processing'    │
│ result_json={...}      │
│ (write to DB)          │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│ Email Delivery         │
│ + Update Order:        │
│ status='completed'     │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│ ✅ DATA PERSISTED      │
│ (stored in database)   │
│ - Order record         │
│ - Customer record      │
│ - Payment record       │
│ - Result JSON          │
│ - QA logs              │
└────────────────────────┘
```

---

## 4. BUSINESS REQUIREMENTS

### 4.1 Functional Requirements

#### FR-1: Payment Processing
**Priority**: P0 (Blocker)
**Status**: Not Implemented (0%)

**Requirements**:
1. User must pay before workflow processing begins
2. Support credit/debit cards via Stripe Checkout (hosted)
3. Pricing tiers: $49 (Starter), $149 (Standard), $399 (Premium)
4. Generate Stripe Payment Intent with metadata (order_id, tier, company_name)
5. Handle payment success webhook → Create order
6. Handle payment failure webhook → Log and notify user
7. Generate and email receipt immediately after payment
8. Support test mode (Stripe test keys) for development
9. Support production mode (Stripe live keys) for launch

**Acceptance Criteria**:
- [ ] User can complete checkout flow without errors
- [ ] Payment success creates Order record in database
- [ ] Payment failure shows user-friendly error message
- [ ] Test cards work in test mode (4242 4242 4242 4242)
- [ ] Receipts are emailed automatically
- [ ] No processing begins until payment confirmed

#### FR-2: Order Persistence
**Priority**: P0 (Blocker)
**Status**: Not Implemented (0%)

**Requirements**:
1. Store all orders in PostgreSQL database
2. Store all customers (email, name, company) with deduplication
3. Store all payments (Stripe payment intent ID, amount, status)
4. Store workflow results as JSON (proposal, consensus, QA scores)
5. Support order status tracking: pending → processing → completed → failed
6. Support order retrieval by run_id or order_id
7. Support customer history queries (all orders for email)
8. Cascade deletes (customer → orders → payments)
9. Timestamps for created_at, updated_at, completed_at

**Acceptance Criteria**:
- [ ] All orders are persisted to database
- [ ] No data loss on server restart
- [ ] Orders can be queried by run_id or customer email
- [ ] Database migrations work (Alembic)
- [ ] Indexes on frequently queried fields (email, run_id, created_at)

#### FR-3: Order Status Tracking
**Priority**: P0 (Blocker)
**Status**: Stub Only (5%)

**Requirements**:
1. GET `/api/orders/{order_id}/status` returns current status
2. Status values: `payment_pending`, `processing`, `completed`, `failed`, `refunded`
3. Response includes: order_id, status, created_at, estimated_completion_time, progress_percent
4. Status page UI at `/status/{order_id}` shows visual progress
5. Polling endpoint (frontend calls every 5 seconds until completed)
6. Status transitions logged to database
7. Email link includes status page URL

**Acceptance Criteria**:
- [ ] User can check order status without contacting support
- [ ] Status page loads in <1 second
- [ ] Status updates in real-time (within 5 seconds of change)
- [ ] Progress bar shows realistic completion percentage
- [ ] Mobile-responsive status page

#### FR-4: Customer Communication Flow
**Priority**: P0 (Blocker)
**Status**: Partial (40% - only final email exists)

**Requirements**:
1. **Email 1 - Payment Confirmation** (sent immediately after payment):
   - Subject: "Payment received - Your AI Readiness Compass is being prepared"
   - Body: Order ID, tier, company name, status page link
   - Receipt attached as PDF

2. **Email 2 - Processing Complete** (sent when status='completed'):
   - Subject: "Your AI Readiness Compass is ready"
   - Body: Download link, summary stats, tier info
   - Report attached as PDF + HTML inline

3. **Email 3 - Processing Failed** (sent when status='failed'):
   - Subject: "Issue with your AI Readiness Compass order"
   - Body: Apology, automatic refund notice, support contact
   - No attachments

4. **Email 4 - Refund Processed** (sent when refund issued):
   - Subject: "Refund processed for your AI Readiness Compass order"
   - Body: Refund amount, reason, processing time (5-10 days)

**Acceptance Criteria**:
- [ ] All 4 email types implemented and tested
- [ ] Emails use professional HTML templates (not plain text)
- [ ] Links are HTTPS and point to production domain
- [ ] Attachments work correctly (not blocked by spam filters)
- [ ] All emails logged to database for audit trail

#### FR-5: Self-Service Refund System
**Priority**: P1 (Important)
**Status**: Not Implemented (0%)

**Requirements**:
1. Refund request form at `/orders/{order_id}/refund`
2. Auto-approve if: <7 days since purchase AND report not downloaded AND first refund
3. Manual review required if: >7 days OR downloaded OR multiple refunds
4. Process refund via Stripe API (full refund only, no partial)
5. Update order status to 'refunded'
6. Send refund confirmation email
7. Prevent re-download after refund
8. Admin dashboard to review pending refund requests

**Acceptance Criteria**:
- [ ] Eligible refunds processed within 1 minute (automated)
- [ ] Complex refunds flagged for admin review
- [ ] Refund rate tracked (target <5%)
- [ ] User receives confirmation email with expected timeline
- [ ] Stripe refund and database update are atomic (both succeed or both fail)

#### FR-6: User Authentication (Optional but Recommended)
**Priority**: P1 (Important)
**Status**: Not Implemented (0%)

**Requirements**:
1. Magic link authentication (email-only, no passwords)
2. User dashboard at `/dashboard` shows order history
3. Re-download past reports from dashboard
4. Prefill company info for repeat orders
5. Session management (JWT or session cookies)
6. Logout functionality
7. Account settings page (update email, company info)

**Acceptance Criteria**:
- [ ] User can log in via magic link sent to email
- [ ] Dashboard loads in <2 seconds with order history
- [ ] Re-download links work (serve from database)
- [ ] Sessions expire after 7 days of inactivity
- [ ] Mobile-responsive dashboard

### 4.2 Non-Functional Requirements

#### NFR-1: Performance
**Priority**: P0

**Requirements**:
- API response time: <500ms for non-processing endpoints
- Workflow processing time: <24 hours (target <12 hours)
- Status API response time: <200ms
- Frontend page load: <2 seconds
- Database query time: <100ms
- Email delivery time: <5 seconds

**Acceptance Criteria**:
- [ ] Load testing shows 95th percentile <500ms for API calls
- [ ] Average workflow processing time <8 hours
- [ ] No timeout errors under normal load (100 concurrent users)

#### NFR-2: Reliability
**Priority**: P0

**Requirements**:
- Uptime: 99.5% (max 3.6 hours downtime/month)
- Error rate: <1% of requests
- Payment success rate: >95% (excluding user card issues)
- Email delivery rate: >98%
- Data integrity: 0% data loss
- Automatic retry on transient failures (AI API, email, database)

**Acceptance Criteria**:
- [ ] Uptime monitored via UptimeRobot or Pingdom
- [ ] Error rate tracked via logging + alerting
- [ ] Database backups run daily
- [ ] Retry logic tested for all external dependencies

#### NFR-3: Scalability
**Priority**: P1

**Requirements**:
- Support 500 orders/month initially (target 2000/month within 12 months)
- Auto-scale web tier (horizontal scaling)
- Background job processing (Celery or similar)
- Database connection pooling
- CDN for static assets
- Rate limiting to prevent abuse

**Acceptance Criteria**:
- [ ] Load testing shows system handles 50 concurrent submissions
- [ ] Background jobs process orders asynchronously
- [ ] Database supports 10K orders without performance degradation
- [ ] Rate limiting prevents single IP from submitting >5 orders/hour

#### NFR-4: Security
**Priority**: P0

**Requirements**:
- HTTPS enforced (redirect HTTP → HTTPS)
- Stripe webhook signature verification
- SQL injection prevention (parameterized queries)
- XSS prevention (escaped output)
- CSRF protection on forms
- API key rotation policy
- Secrets stored in environment variables (never in code)
- PCI compliance (Stripe handles card data)

**Acceptance Criteria**:
- [ ] Security audit passes (OWASP Top 10 checks)
- [ ] SSL certificate valid and auto-renewing
- [ ] Webhook signature verification tested
- [ ] No secrets committed to git
- [ ] Database credentials encrypted at rest

#### NFR-5: Observability
**Priority**: P1

**Requirements**:
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Request tracing (run_id propagated through all logs)
- Error tracking (Sentry or similar)
- Performance monitoring (response times, AI call latency)
- Business metrics (orders, revenue, refunds)
- Uptime monitoring (external service)

**Acceptance Criteria**:
- [ ] All API calls logged with run_id
- [ ] Errors trigger alerts (email or Slack)
- [ ] Dashboard shows real-time metrics
- [ ] Log retention: 30 days
- [ ] Logs searchable by run_id, email, or date range

---

## 5. TECHNICAL ARCHITECTURE SPECIFICATIONS

### 5.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT TIER                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │  Browser   │  │   Mobile   │  │  Stripe    │  │   Gmail    │   │
│  │   (User)   │  │   (User)   │  │  Checkout  │  │  (Email)   │   │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘   │
└────────┼───────────────┼───────────────┼───────────────┼───────────┘
         │               │               │               │
         │ HTTPS         │ HTTPS         │ HTTPS         │ SMTP
         │               │               │               │
┌────────┼───────────────┼───────────────┼───────────────┼───────────┐
│        ▼               ▼               ▼               ▼           │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              LOAD BALANCER (Nginx/Cloudflare)              │  │
│  │  - SSL Termination                                          │  │
│  │  - Rate Limiting                                            │  │
│  │  - DDoS Protection                                          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │         WEB TIER (FastAPI Application Servers)             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │  │
│  │  │   Instance 1 │  │   Instance 2 │  │   Instance N │      │  │
│  │  │  (Stateless) │  │  (Stateless) │  │  (Stateless) │      │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │  │
│  │  - REST API Endpoints                                       │  │
│  │  - Webhook Handlers (Stripe)                                │  │
│  │  - Static File Serving (via CDN)                            │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │         TASK QUEUE (Redis + Celery Workers)                │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Redis Queue: High priority (payment processing)     │  │  │
│  │  │  Redis Queue: Default (workflow processing)          │  │  │
│  │  │  Redis Queue: Low priority (email sending, QA logs)  │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │  │
│  │  │  Worker 1    │  │  Worker 2    │  │  Worker N    │      │  │
│  │  │ (Stateless)  │  │ (Stateless)  │  │ (Stateless)  │      │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              DATA TIER (PostgreSQL)                        │  │
│  │  ┌────────────────────────────────────────────────────┐    │  │
│  │  │  Primary Database (Read/Write)                     │    │  │
│  │  │  - Orders, Customers, Payments                      │    │  │
│  │  │  - Workflow Results (JSON)                          │    │  │
│  │  │  - QA Logs                                          │    │  │
│  │  └────────────────────────────────────────────────────┘    │  │
│  │  ┌────────────────────────────────────────────────────┐    │  │
│  │  │  Replica Database (Read-Only)                      │    │  │
│  │  │  - Analytics Queries                                │    │  │
│  │  │  - Reporting                                        │    │  │
│  │  └────────────────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
└──────────────────────────────┼─────────────────────────────────────┘
                               │
┌──────────────────────────────┼─────────────────────────────────────┐
│                              ▼                                     │
│              EXTERNAL SERVICES (Adapters)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Anthropic    │  │   Stripe     │  │   Gmail      │             │
│  │   Claude     │  │     API      │  │ SMTP/API     │             │
│  │     API      │  │              │  │              │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Google      │  │   Sentry     │  │  Cloudflare  │             │
│  │   Sheets     │  │ Error Track  │  │     CDN      │             │
│  │     API      │  │              │  │              │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Technology Stack

#### 5.2.1 Backend
- **Language**: Python 3.11+
- **Web Framework**: FastAPI 0.109+
- **ORM**: SQLAlchemy 2.0+ (async)
- **Database**: PostgreSQL 15+ (production), SQLite (development)
- **Task Queue**: Celery 5+ with Redis broker
- **Migrations**: Alembic 1.13+
- **Validation**: Pydantic 2.5+
- **HTTP Client**: httpx (async)
- **Logging**: structlog
- **Testing**: pytest, pytest-asyncio

#### 5.2.2 Frontend
- **Templating**: Jinja2
- **Styling**: CSS3 (custom, no framework)
- **JavaScript**: Vanilla ES6+ (no heavy frameworks)
- **UI Components**: Custom (maintain existing design)
- **Payment**: Stripe Elements (official widget)

#### 5.2.3 Infrastructure
- **Hosting**: Railway, Render, or Fly.io (recommendation: Railway for simplicity)
- **Database Hosting**: Managed PostgreSQL (Railway, Supabase, or Neon)
- **Task Queue**: Redis Cloud (free tier sufficient for MVP)
- **Email**: Gmail SMTP (current) or SendGrid (future)
- **CDN**: Cloudflare (free tier)
- **Monitoring**: Sentry (error tracking), UptimeRobot (uptime)
- **Analytics**: Plausible or Google Analytics

#### 5.2.4 External APIs
- **AI Provider**: Anthropic Claude API (claude-sonnet-4-20250514)
- **Payments**: Stripe API v2024.11
- **Email**: Gmail API + SMTP (current)
- **Logging**: Google Sheets API (optional)

### 5.3 Deployment Architecture

#### 5.3.1 Environment Strategy
```
Development (Local)
├── Database: SQLite (local file)
├── Task Queue: Redis (Docker container)
├── AI Provider: Mock (tests) or Anthropic (manual testing)
├── Payment: Stripe Test Mode
└── Email: Console output or Mailtrap

Staging (Railway/Render)
├── Database: PostgreSQL (managed)
├── Task Queue: Redis (managed)
├── AI Provider: Anthropic (test keys)
├── Payment: Stripe Test Mode
└── Email: Gmail SMTP (test account)

Production (Railway/Render)
├── Database: PostgreSQL (managed, with replica)
├── Task Queue: Redis (managed)
├── AI Provider: Anthropic (production keys)
├── Payment: Stripe Live Mode
└── Email: Gmail SMTP or SendGrid
```

#### 5.3.2 Scaling Strategy

**Phase 1** (0-100 orders/month):
- Single web instance (1 GB RAM)
- Single Celery worker (2 GB RAM)
- Small PostgreSQL (1 GB RAM)
- Redis free tier

**Phase 2** (100-500 orders/month):
- 2 web instances (auto-scale)
- 3 Celery workers (dedicated queues)
- Medium PostgreSQL (2 GB RAM)
- Redis standard tier

**Phase 3** (500-2000 orders/month):
- 5 web instances (auto-scale)
- 10 Celery workers (queue-based scaling)
- Large PostgreSQL with read replica
- Redis premium tier
- CDN for all static assets

---

## 6. COMPONENT-BY-COMPONENT REFACTORING PLAN

### 6.1 New Component: Database Layer

**Status**: Does not exist (0%)
**Priority**: P0
**Estimated Effort**: 1 week

#### 6.1.1 File Structure
```
workflow_system/
├── models/                        # NEW DIRECTORY
│   ├── __init__.py
│   ├── base.py                   # Base model with common fields
│   ├── customer.py               # Customer model
│   ├── order.py                  # Order model
│   ├── payment.py                # Payment model
│   └── refund.py                 # Refund model
├── database/                      # NEW DIRECTORY
│   ├── __init__.py
│   ├── session.py                # Database session management
│   └── migrations/               # Alembic migrations
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
│           └── 001_initial_schema.py
└── infrastructure/
    └── database/                  # NEW DIRECTORY
        ├── __init__.py
        ├── repository.py          # Generic repository pattern
        ├── customer_repository.py
        ├── order_repository.py
        └── payment_repository.py
```

#### 6.1.2 Database Models Specification

**models/base.py**:
```python
"""Base model with common fields for all tables."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

**models/customer.py**:
```python
"""Customer model."""
from sqlalchemy import Column, String, Index
from sqlalchemy.orm import relationship, Mapped
from models.base import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    """Customer table (deduped by email)."""
    __tablename__ = "customers"
    __table_args__ = (
        Index("idx_customer_email", "email"),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=True)
    company_website: Mapped[str] = mapped_column(String(500), nullable=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    company_size: Mapped[str] = mapped_column(String(50), nullable=True)

    # Relationships
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer(email={self.email}, company={self.company_name})>"
```

**models/order.py**:
```python
"""Order model."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from models.base import Base, TimestampMixin


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PAYMENT_PENDING = "payment_pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(Base, TimestampMixin):
    """Order table."""
    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_order_run_id", "run_id"),
        Index("idx_order_customer_id", "customer_id"),
        Index("idx_order_status", "status"),
        Index("idx_order_created_at", "created_at"),
    )

    # Unique identifiers
    run_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g., "ORD-2025-0001"

    # Foreign keys
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)

    # Order details
    tier: Mapped[str] = mapped_column(String(50), nullable=False)  # "Starter", "Standard", "Premium"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=OrderStatus.PAYMENT_PENDING.value)

    # Business context (from submission form)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    pain_point: Mapped[str] = mapped_column(Text, nullable=True)

    # Processing metadata
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    processing_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)

    # Results (JSON columns)
    workflow_result: Mapped[dict] = mapped_column(JSON, nullable=True)  # Full WorkflowResult.to_dict()
    qa_result: Mapped[dict] = mapped_column(JSON, nullable=True)  # QA scores

    # Delivery
    email_sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_downloaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Error tracking
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")
    refund = relationship("Refund", back_populates="order", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(run_id={self.run_id}, status={self.status}, tier={self.tier})>"
```

**models/payment.py**:
```python
"""Payment model."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from models.base import Base, TimestampMixin


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class Payment(Base, TimestampMixin):
    """Payment table."""
    __tablename__ = "payments"
    __table_args__ = (
        Index("idx_payment_stripe_id", "stripe_payment_intent_id"),
        Index("idx_payment_order_id", "order_id"),
    )

    # Stripe identifiers
    stripe_payment_intent_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=True)

    # Foreign keys
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)

    # Payment details
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)  # Store as cents (4900, 14900, 39900)
    currency: Mapped[str] = mapped_column(String(3), default="usd", nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=PaymentStatus.PENDING.value)

    # Metadata
    paid_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[str] = mapped_column(String(500), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="payment")

    @property
    def amount_dollars(self) -> float:
        """Convert cents to dollars."""
        return self.amount_cents / 100.0

    def __repr__(self):
        return f"<Payment(stripe_id={self.stripe_payment_intent_id}, amount=${self.amount_dollars}, status={self.status})>"
```

**models/refund.py**:
```python
"""Refund model."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from models.base import Base, TimestampMixin


class RefundStatus(str, Enum):
    """Refund status enumeration."""
    REQUESTED = "requested"
    APPROVED = "approved"
    DENIED = "denied"
    PROCESSED = "processed"


class Refund(Base, TimestampMixin):
    """Refund table."""
    __tablename__ = "refunds"
    __table_args__ = (
        Index("idx_refund_order_id", "order_id"),
        Index("idx_refund_status", "status"),
    )

    # Foreign keys
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)

    # Refund details
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=RefundStatus.REQUESTED.value)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)

    # Approval
    auto_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    denied_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    denial_reason: Mapped[str] = mapped_column(Text, nullable=True)

    # Stripe
    stripe_refund_id: Mapped[str] = mapped_column(String(255), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="refund")

    @property
    def amount_dollars(self) -> float:
        """Convert cents to dollars."""
        return self.amount_cents / 100.0

    def __repr__(self):
        return f"<Refund(order_id={self.order_id}, amount=${self.amount_dollars}, status={self.status})>"
```

#### 6.1.3 Repository Pattern

**infrastructure/database/repository.py**:
```python
"""Generic repository pattern for database operations."""
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class Repository(Generic[ModelType]):
    """Generic repository for CRUD operations."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get record by primary key."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()

    async def get_by(self, **filters) -> Optional[ModelType]:
        """Get single record matching filters."""
        stmt = select(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list(self, **filters) -> List[ModelType]:
        """List all records matching filters."""
        stmt = select(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """Update a record by ID."""
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().first()

    async def delete(self, id: int) -> bool:
        """Delete a record by ID."""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
```

**infrastructure/database/order_repository.py**:
```python
"""Order repository with business logic."""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.database.repository import Repository
from models.order import Order, OrderStatus


class OrderRepository(Repository[Order]):
    """Repository for Order operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Order, session)

    async def get_by_run_id(self, run_id: str) -> Optional[Order]:
        """Get order by run_id."""
        return await self.get_by(run_id=run_id)

    async def get_by_order_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number."""
        return await self.get_by(order_number=order_number)

    async def list_by_customer_email(self, email: str) -> List[Order]:
        """List all orders for a customer email."""
        stmt = (
            select(Order)
            .join(Order.customer)
            .where(Customer.email == email)
            .order_by(Order.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_pending(self, older_than_minutes: int = 5) -> List[Order]:
        """List orders stuck in pending status (for error recovery)."""
        cutoff = datetime.utcnow() - timedelta(minutes=older_than_minutes)
        stmt = (
            select(Order)
            .where(Order.status == OrderStatus.PAYMENT_PENDING.value)
            .where(Order.created_at < cutoff)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_processing(self, order_id: int) -> Optional[Order]:
        """Mark order as processing."""
        return await self.update(
            order_id,
            status=OrderStatus.PROCESSING.value,
            started_at=datetime.utcnow()
        )

    async def mark_completed(
        self,
        order_id: int,
        workflow_result: dict,
        qa_result: Optional[dict] = None
    ) -> Optional[Order]:
        """Mark order as completed with results."""
        now = datetime.utcnow()
        return await self.update(
            order_id,
            status=OrderStatus.COMPLETED.value,
            completed_at=now,
            workflow_result=workflow_result,
            qa_result=qa_result
        )

    async def mark_failed(self, order_id: int, error_message: str) -> Optional[Order]:
        """Mark order as failed."""
        return await self.update(
            order_id,
            status=OrderStatus.FAILED.value,
            error_message=error_message,
            completed_at=datetime.utcnow()
        )

    async def increment_download_count(self, order_id: int) -> Optional[Order]:
        """Increment download counter."""
        order = await self.get_by_id(order_id)
        if not order:
            return None
        return await self.update(
            order_id,
            download_count=order.download_count + 1,
            last_downloaded_at=datetime.utcnow()
        )
```

#### 6.1.4 Database Session Management

**database/session.py**:
```python
"""Database session management."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from config.settings import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI endpoints to get database session.

    Usage:
        @app.get("/orders/{order_id}")
        async def get_order(order_id: int, session: AsyncSession = Depends(get_session)):
            repo = OrderRepository(session)
            return await repo.get_by_id(order_id)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of FastAPI.

    Usage:
        async with session_scope() as session:
            repo = OrderRepository(session)
            order = await repo.create(...)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

#### 6.1.5 Database Migrations (Alembic)

**Initial Migration** (database/migrations/versions/001_initial_schema.py):
```python
"""Initial schema

Revision ID: 001
Create Date: 2025-12-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""

    # Customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('company_website', sa.String(length=500), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('company_size', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_customer_email', 'customers', ['email'])

    # Orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.String(length=50), nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('tier', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('pain_point', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('workflow_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('qa_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('email_sent_at', sa.DateTime(), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_downloaded_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id'),
        sa.UniqueConstraint('order_number')
    )
    op.create_index('idx_order_run_id', 'orders', ['run_id'])
    op.create_index('idx_order_customer_id', 'orders', ['customer_id'])
    op.create_index('idx_order_status', 'orders', ['status'])
    op.create_index('idx_order_created_at', 'orders', ['created_at'])

    # Payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='usd'),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('failure_reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_payment_intent_id'),
        sa.UniqueConstraint('order_id')
    )
    op.create_index('idx_payment_stripe_id', 'payments', ['stripe_payment_intent_id'])
    op.create_index('idx_payment_order_id', 'payments', ['order_id'])

    # Refunds table
    op.create_table(
        'refunds',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('auto_approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('denied_at', sa.DateTime(), nullable=True),
        sa.Column('denial_reason', sa.Text(), nullable=True),
        sa.Column('stripe_refund_id', sa.String(length=255), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )
    op.create_index('idx_refund_order_id', 'refunds', ['order_id'])
    op.create_index('idx_refund_status', 'refunds', ['status'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('refunds')
    op.drop_table('payments')
    op.drop_table('orders')
    op.drop_table('customers')
```

---

### 6.2 New Component: Stripe Payment Integration

**Status**: Does not exist (0%)
**Priority**: P0
**Estimated Effort**: 1 week

#### 6.2.1 File Structure
```
workflow_system/
├── infrastructure/
│   └── payment/                   # NEW DIRECTORY
│       ├── __init__.py
│       ├── stripe_adapter.py      # Stripe API client
│       └── models.py              # Payment domain models
├── web/
│   └── api/
│       ├── payment.py             # NEW FILE - Payment endpoints
│       └── webhooks.py            # NEW FILE - Stripe webhooks
└── config/
    └── dependency_injection.py    # Add PaymentClient protocol + provider
```

#### 6.2.2 Stripe Adapter Specification

**infrastructure/payment/stripe_adapter.py**:
```python
"""Stripe payment adapter."""
import stripe
from typing import Optional, Dict, Any
import structlog
from config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripeAdapter:
    """
    Adapter for Stripe API.

    Handles payment intent creation, refunds, and customer management.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        stripe.api_key = api_key

    async def create_payment_intent(
        self,
        amount_cents: int,
        currency: str = "usd",
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe Payment Intent.

        Args:
            amount_cents: Amount in cents (e.g., 4900 for $49.00)
            currency: Currency code (default: "usd")
            metadata: Optional metadata dict (order_id, tier, etc.)

        Returns:
            Payment intent dict with 'id' and 'client_secret'
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True},
            )

            logger.info(
                "stripe_payment_intent_created",
                intent_id=intent.id,
                amount_cents=amount_cents,
                metadata=metadata,
            )

            return {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "amount": amount_cents,
                "currency": currency,
                "status": intent.status,
            }

        except stripe.error.StripeError as e:
            logger.error(
                "stripe_payment_intent_failed",
                error=str(e),
                amount_cents=amount_cents,
            )
            raise

    async def get_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve a payment intent by ID.

        Args:
            payment_intent_id: Stripe payment intent ID

        Returns:
            Payment intent dict
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "id": intent.id,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status,
                "metadata": intent.metadata,
            }
        except stripe.error.StripeError as e:
            logger.error(
                "stripe_get_payment_intent_failed",
                error=str(e),
                intent_id=payment_intent_id,
            )
            raise

    async def create_refund(
        self,
        payment_intent_id: str,
        amount_cents: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment intent.

        Args:
            payment_intent_id: Stripe payment intent ID
            amount_cents: Optional partial refund amount (None = full refund)
            reason: Refund reason ("requested_by_customer", "fraudulent", etc.)

        Returns:
            Refund dict with 'id' and 'status'
        """
        try:
            refund_params = {
                "payment_intent": payment_intent_id,
            }

            if amount_cents is not None:
                refund_params["amount"] = amount_cents

            if reason:
                refund_params["reason"] = reason

            refund = stripe.Refund.create(**refund_params)

            logger.info(
                "stripe_refund_created",
                refund_id=refund.id,
                payment_intent_id=payment_intent_id,
                amount_cents=refund.amount,
                status=refund.status,
            )

            return {
                "id": refund.id,
                "amount": refund.amount,
                "currency": refund.currency,
                "status": refund.status,
                "payment_intent": payment_intent_id,
            }

        except stripe.error.StripeError as e:
            logger.error(
                "stripe_refund_failed",
                error=str(e),
                intent_id=payment_intent_id,
            )
            raise

    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        webhook_secret: str,
    ) -> stripe.Event:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Raw request body (as string)
            signature: Stripe-Signature header value
            webhook_secret: Webhook signing secret from Stripe dashboard

        Returns:
            Verified Stripe Event object

        Raises:
            stripe.error.SignatureVerificationError: If signature is invalid
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            logger.debug(
                "stripe_webhook_verified",
                event_type=event["type"],
                event_id=event["id"],
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(
                "stripe_webhook_verification_failed",
                error=str(e),
            )
            raise
```

#### 6.2.3 Payment API Endpoints

**web/api/payment.py**:
```python
"""Payment API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from config import get_container
from database.session import get_session
from infrastructure.database.customer_repository import CustomerRepository
from infrastructure.database.order_repository import OrderRepository
from infrastructure.database.payment_repository import PaymentRepository
from models.order import OrderStatus
from models.payment import PaymentStatus

logger = structlog.get_logger()
router = APIRouter()


class CreatePaymentIntentRequest(BaseModel):
    """Request to create payment intent."""
    tier: str  # "Starter", "Standard", "Premium"
    company_name: str
    email: str
    # ... other form fields


class CreatePaymentIntentResponse(BaseModel):
    """Response with payment intent client secret."""
    client_secret: str
    amount_cents: int
    order_id: str


TIER_PRICES = {
    "Starter": 4900,   # $49.00
    "Standard": 14900,  # $149.00
    "Premium": 39900,   # $399.00
}


@router.post("/create-payment-intent", response_model=CreatePaymentIntentResponse)
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a Stripe Payment Intent for checkout.

    Flow:
    1. Validate tier and calculate amount
    2. Create/find customer in database
    3. Create order record (status='payment_pending')
    4. Create payment intent via Stripe
    5. Create payment record in database
    6. Return client_secret to frontend
    """
    container = get_container()

    try:
        # Validate tier
        if request.tier not in TIER_PRICES:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {request.tier}")

        amount_cents = TIER_PRICES[request.tier]

        # Create or get customer
        customer_repo = CustomerRepository(session)
        customer = await customer_repo.get_or_create_by_email(
            email=request.email,
            name=request.contact_name,
            company_name=request.company_name,
            # ... other fields
        )

        # Create order record
        order_repo = OrderRepository(session)
        order = await order_repo.create(
            customer_id=customer.id,
            run_id=str(uuid.uuid4())[:8],
            order_number=generate_order_number(),  # e.g., "ORD-2025-0001"
            tier=request.tier,
            status=OrderStatus.PAYMENT_PENDING.value,
            prompt=request.prompt,
            pain_point=request.pain_point,
        )

        # Create Stripe payment intent
        stripe_adapter = container.payment_client()
        intent = await stripe_adapter.create_payment_intent(
            amount_cents=amount_cents,
            currency="usd",
            metadata={
                "order_id": str(order.id),
                "run_id": order.run_id,
                "tier": request.tier,
                "company": request.company_name,
            },
        )

        # Create payment record
        payment_repo = PaymentRepository(session)
        await payment_repo.create(
            stripe_payment_intent_id=intent["id"],
            order_id=order.id,
            amount_cents=amount_cents,
            currency="usd",
            status=PaymentStatus.PENDING.value,
        )

        logger.info(
            "payment_intent_created",
            order_id=order.id,
            run_id=order.run_id,
            tier=request.tier,
            amount_cents=amount_cents,
        )

        return CreatePaymentIntentResponse(
            client_secret=intent["client_secret"],
            amount_cents=amount_cents,
            order_id=order.run_id,
        )

    except Exception as e:
        logger.error(
            "create_payment_intent_failed",
            error=str(e),
            tier=request.tier,
            email=request.email,
        )
        raise HTTPException(status_code=500, detail=str(e))
```

#### 6.2.4 Stripe Webhook Handler

**web/api/webhooks.py**:
```python
"""Stripe webhook handlers."""
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from config import get_container, get_settings
from database.session import get_session
from infrastructure.database.order_repository import OrderRepository
from infrastructure.database.payment_repository import PaymentRepository
from models.order import OrderStatus
from models.payment import PaymentStatus
from tasks.workflow_processing import process_order_task  # Celery task

logger = structlog.get_logger()
router = APIRouter()
settings = get_settings()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    session: AsyncSession = Depends(get_session),
):
    """
    Handle Stripe webhook events.

    Events handled:
    - payment_intent.succeeded: Mark payment as succeeded, queue order processing
    - payment_intent.payment_failed: Mark payment as failed, notify user
    - charge.refunded: Mark order as refunded, update database
    """
    container = get_container()

    # Get raw request body for signature verification
    payload = await request.body()

    try:
        # Verify webhook signature
        stripe_adapter = container.payment_client()
        event = stripe_adapter.verify_webhook_signature(
            payload=payload.decode("utf-8"),
            signature=stripe_signature,
            webhook_secret=settings.stripe_webhook_secret,
        )

        logger.info(
            "stripe_webhook_received",
            event_type=event["type"],
            event_id=event["id"],
        )

        # Handle different event types
        if event["type"] == "payment_intent.succeeded":
            await handle_payment_succeeded(event, session)
        elif event["type"] == "payment_intent.payment_failed":
            await handle_payment_failed(event, session)
        elif event["type"] == "charge.refunded":
            await handle_refund_processed(event, session)
        else:
            logger.info(
                "stripe_webhook_ignored",
                event_type=event["type"],
            )

        return {"status": "success"}

    except Exception as e:
        logger.error(
            "stripe_webhook_failed",
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))


async def handle_payment_succeeded(event: dict, session: AsyncSession):
    """
    Handle payment_intent.succeeded event.

    Actions:
    1. Update payment status to 'succeeded'
    2. Send confirmation email to customer
    3. Queue background job to process order
    """
    payment_intent = event["data"]["object"]
    payment_intent_id = payment_intent["id"]

    # Find payment record
    payment_repo = PaymentRepository(session)
    payment = await payment_repo.get_by_stripe_id(payment_intent_id)

    if not payment:
        logger.error(
            "payment_not_found",
            payment_intent_id=payment_intent_id,
        )
        return

    # Update payment status
    await payment_repo.update(
        payment.id,
        status=PaymentStatus.SUCCEEDED.value,
        paid_at=datetime.utcnow(),
    )

    # Get order
    order_repo = OrderRepository(session)
    order = await order_repo.get_by_id(payment.order_id)

    if not order:
        logger.error(
            "order_not_found",
            order_id=payment.order_id,
        )
        return

    logger.info(
        "payment_succeeded",
        order_id=order.id,
        run_id=order.run_id,
        amount_cents=payment.amount_cents,
    )

    # Send confirmation email
    # TODO: Implement email sending

    # Queue background job to process order
    process_order_task.delay(order_id=order.id)

    logger.info(
        "order_queued_for_processing",
        order_id=order.id,
        run_id=order.run_id,
    )


async def handle_payment_failed(event: dict, session: AsyncSession):
    """
    Handle payment_intent.payment_failed event.

    Actions:
    1. Update payment status to 'failed'
    2. Send failure notification to customer
    """
    payment_intent = event["data"]["object"]
    payment_intent_id = payment_intent["id"]
    failure_message = payment_intent.get("last_payment_error", {}).get("message", "Unknown error")

    # Find payment record
    payment_repo = PaymentRepository(session)
    payment = await payment_repo.get_by_stripe_id(payment_intent_id)

    if not payment:
        logger.error(
            "payment_not_found",
            payment_intent_id=payment_intent_id,
        )
        return

    # Update payment status
    await payment_repo.update(
        payment.id,
        status=PaymentStatus.FAILED.value,
        failure_reason=failure_message,
    )

    logger.warning(
        "payment_failed",
        order_id=payment.order_id,
        payment_intent_id=payment_intent_id,
        failure_reason=failure_message,
    )

    # TODO: Send failure notification email


async def handle_refund_processed(event: dict, session: AsyncSession):
    """
    Handle charge.refunded event.

    Actions:
    1. Update refund status to 'processed'
    2. Send refund confirmation email
    """
    # Implementation similar to above
    pass
```

---

This document is getting quite long. I'll continue with the remaining sections in the next part.

**CONTINUED IN NEXT MESSAGE...**
