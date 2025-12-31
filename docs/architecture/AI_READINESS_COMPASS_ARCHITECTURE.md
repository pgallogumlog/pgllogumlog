# AI Readiness Compass - Technical Architecture

**Document Type:** Technical Design Document (TDD)
**Version:** 1.0
**Date:** 2025-12-31
**Author:** Architect Agent
**Status:** Proposed

---

## Executive Summary

This document defines the technical architecture for the AI Readiness Compass, a premium ($497) AI-powered research and report generation system. The system performs deep research on a client's company, their industry's AI landscape, and relevant technologies to produce a personalized 10-15 page executive report with actionable AI solution recommendations.

**Key Architectural Decisions:**
1. **New Context Module** - Clean separation from existing workflow system
2. **Multi-Stage Research Pipeline** - Orchestrated async research with multiple AI agents
3. **Job Queue Pattern** - Background processing with status tracking
4. **Stripe Payment Authorization** - Hold funds upfront, capture after QA gate
5. **Template + Generative Hybrid** - Structured report with AI-generated content sections

---

## System Architecture Diagram

```
                                    AI READINESS COMPASS - SYSTEM ARCHITECTURE

    +-------------------------------------------------------------------------------------------+
    |                                        CLIENT LAYER                                        |
    +-------------------------------------------------------------------------------------------+
    |                                                                                           |
    |    [Browser]                                                                              |
    |        |                                                                                  |
    |        v                                                                                  |
    |    +------------------+     +-----------------+     +------------------+                  |
    |    | Submission Form  |---->| Stripe.js       |---->| Payment Confirm  |                  |
    |    | (company info,   |     | (card capture,  |     | (redirect/webhook)|                 |
    |    |  pain points)    |     |  hold $497)     |     |                  |                  |
    |    +------------------+     +-----------------+     +------------------+                  |
    |                                                                                           |
    +-------------------------------------------------------------------------------------------+
                                              |
                                              | HTTPS
                                              v
    +-------------------------------------------------------------------------------------------+
    |                                        API LAYER                                          |
    +-------------------------------------------------------------------------------------------+
    |                                                                                           |
    |    +------------------+     +------------------+     +------------------+                  |
    |    | POST /api/       |     | GET /api/        |     | POST /webhooks/  |                 |
    |    |   compass/submit |     |   compass/status |     |   stripe         |                 |
    |    +------------------+     +------------------+     +------------------+                  |
    |            |                        |                        |                            |
    |            v                        v                        v                            |
    |    +------------------------------------------------------------------+                   |
    |    |                     FastAPI Application                          |                   |
    |    |  - Request validation (Pydantic)                                 |                   |
    |    |  - Authentication/rate limiting                                  |                   |
    |    |  - Job creation and status queries                               |                   |
    |    +------------------------------------------------------------------+                   |
    |                                                                                           |
    +-------------------------------------------------------------------------------------------+
                                              |
                                              v
    +-------------------------------------------------------------------------------------------+
    |                                      JOB LAYER                                            |
    +-------------------------------------------------------------------------------------------+
    |                                                                                           |
    |    +------------------+     +------------------+     +------------------+                  |
    |    | Job Queue        |     | Job Processor    |     | Status Store     |                 |
    |    | (SQLite/Redis)   |<--->| (Background      |<--->| (SQLite)         |                 |
    |    |                  |     |  Worker)         |     |                  |                 |
    |    +------------------+     +------------------+     +------------------+                  |
    |                                     |                                                     |
    |                                     v                                                     |
    |    +------------------------------------------------------------------+                   |
    |    |                    COMPASS ENGINE (Orchestrator)                 |                   |
    |    +------------------------------------------------------------------+                   |
    |                                     |                                                     |
    +-------------------------------------------------------------------------------------------+
                                              |
                                              v
    +-------------------------------------------------------------------------------------------+
    |                                   RESEARCH LAYER                                          |
    +-------------------------------------------------------------------------------------------+
    |                                                                                           |
    |    +-----------------------+    +-----------------------+    +-----------------------+    |
    |    | STAGE 1: Company      |    | STAGE 2: Industry     |    | STAGE 3: White Paper  |    |
    |    | Research Agent        |    | AI Research Agent     |    | Research Agent        |    |
    |    +-----------------------+    +-----------------------+    +-----------------------+    |
    |    | - Web scrape company  |    | - Industry AI cases   |    | - Academic papers     |    |
    |    | - LinkedIn presence   |    | - Competitor analysis |    | - Vendor white papers |    |
    |    | - News/press          |    | - Success stories     |    | - Implementation      |    |
    |    | - Size/funding        |    | - Failure lessons     |    |   guides              |    |
    |    +-----------------------+    +-----------------------+    +-----------------------+    |
    |             |                          |                           |                      |
    |             +----------+---------------+---------------+-----------+                      |
    |                        |                               |                                  |
    |                        v                               v                                  |
    |    +-----------------------+              +-----------------------+                       |
    |    | Research Aggregator   |              | Source Validator      |                       |
    |    | (Merge & Dedupe)      |              | (Quality Filter)      |                       |
    |    +-----------------------+              +-----------------------+                       |
    |                                                                                           |
    +-------------------------------------------------------------------------------------------+
                                              |
                                              v
    +-------------------------------------------------------------------------------------------+
    |                                  ANALYSIS LAYER                                           |
    +-------------------------------------------------------------------------------------------+
    |                                                                                           |
    |    +------------------+     +------------------+     +------------------+                  |
    |    | Solution Matcher |     | Feasibility      |     | ROI Estimator    |                 |
    |    | (AI Agent)       |---->| Analyzer         |---->| (AI Agent)       |                 |
    |    |                  |     | (AI Agent)       |     |                  |                 |
    |    +------------------+     +------------------+     +------------------+                  |
    |                                                                                           |
    |    Solution Categories:                                                                   |
    |    +------------------+  +------------------+  +------------------+                        |
    |    | RAG Orchestrator |  | Agentic          |  | Workflow Tools   |                       |
    |    | (Knowledge Base) |  | Orchestrator     |  | (n8n, Make)      |                       |
    |    +------------------+  +------------------+  +------------------+                        |
    |    +------------------+  +------------------+                                             |
    |    | Training         |  | Open Source AI   |                                             |
    |    | Adapters (LoRA)  |  | (LLaMA, Mistral) |                                             |
    |    +------------------+  +------------------+                                             |
    |                                                                                           |
    +-------------------------------------------------------------------------------------------+
                                              |
                                              v
    +-------------------------------------------------------------------------------------------+
    |                                 GENERATION LAYER                                          |
    +-------------------------------------------------------------------------------------------+
    |                                                                                           |
    |    +------------------------------------------------------------------+                   |
    |    |                    Report Generator                              |                   |
    |    +------------------------------------------------------------------+                   |
    |    |                                                                  |                   |
    |    |  +------------------+    +------------------+    +-------------+ |                   |
    |    |  | Executive        |    | Solution         |    | HTML/PDF    | |                   |
    |    |  | Summary Writer   |    | Detail Writer    |    | Renderer    | |                   |
    |    |  | (AI Agent)       |    | (AI Agent x3)    |    | (Jinja2)    | |                   |
    |    |  +------------------+    +------------------+    +-------------+ |                   |
    |    |                                                                  |                   |
    |    +------------------------------------------------------------------+                   |
    |                                                                                           |
    +-------------------------------------------------------------------------------------------+
                                              |
                                              v
    +-------------------------------------------------------------------------------------------+
    |                                    QA LAYER                                               |
    +-------------------------------------------------------------------------------------------+
    |                                                                                           |
    |    +------------------+     +------------------+     +------------------+                  |
    |    | Content QA       |     | Technical QA     |     | Business QA      |                 |
    |    | - Factual checks |     | - Link validity  |     | - Relevance      |                 |
    |    | - Coherence      |     | - Format check   |     | - Actionability  |                 |
    |    | - Tone           |     | - Completeness   |     | - Value prop     |                 |
    |    +------------------+     +------------------+     +------------------+                  |
    |                                     |                                                     |
    |                                     v                                                     |
    |                          +------------------+                                             |
    |                          | QA Gate          |                                             |
    |                          | Score >= 7/10    |------> [FAIL: Refund & Alert]               |
    |                          +------------------+                                             |
    |                                     |                                                     |
    |                                     | PASS                                                |
    |                                     v                                                     |
    +-------------------------------------------------------------------------------------------+
                                              |
                                              v
    +-------------------------------------------------------------------------------------------+
    |                                  DELIVERY LAYER                                           |
    +-------------------------------------------------------------------------------------------+
    |                                                                                           |
    |    +------------------+     +------------------+     +------------------+                  |
    |    | Stripe Capture   |     | Gmail Delivery   |     | Sheets Logger    |                 |
    |    | (Charge $497)    |     | (PDF + HTML)     |     | (Audit Trail)    |                 |
    |    +------------------+     +------------------+     +------------------+                  |
    |                                                                                           |
    +-------------------------------------------------------------------------------------------+
```

---

## Component Breakdown

### 1. New Context: `contexts/compass/`

**Purpose:** Encapsulate all AI Readiness Compass business logic, keeping it cleanly separated from the existing workflow system.

```
contexts/compass/
    __init__.py
    models.py           # Domain models (Submission, Report, Solution, etc.)
    engine.py           # Main orchestrator (CompassEngine)
    research/
        __init__.py
        company_agent.py    # Company research agent
        industry_agent.py   # Industry AI research agent
        whitepaper_agent.py # White paper discovery agent
        aggregator.py       # Merge and dedupe research
    analysis/
        __init__.py
        solution_matcher.py # Match solutions to needs
        feasibility.py      # Assess implementation difficulty
        roi_estimator.py    # Estimate ROI for solutions
    generation/
        __init__.py
        report_writer.py    # Orchestrate report sections
        templates/          # Jinja2 report templates
            executive_summary.html
            solution_detail.html
            appendix.html
    qa/
        __init__.py
        content_validator.py  # Factual/coherence checks
        business_validator.py # Relevance/value checks
        qa_gate.py           # Final pass/fail decision
```

### 2. Infrastructure Extensions

**New Adapters:**

```
infrastructure/
    web/
        scraper_adapter.py    # Web scraping (Playwright/requests)
        search_adapter.py     # Web search API (SerpAPI/Brave)
    payments/
        stripe_adapter.py     # Stripe API (hold, capture, refund)
    documents/
        pdf_generator.py      # HTML to PDF (WeasyPrint/Puppeteer)
```

### 3. API Endpoints

```
web/api/compass.py

POST /api/compass/submit
    - Validates submission data
    - Creates Stripe PaymentIntent (hold)
    - Enqueues job
    - Returns job_id + client_secret

GET /api/compass/status/{job_id}
    - Returns job status, progress %, ETA
    - If complete: returns download link

POST /webhooks/stripe
    - Handles payment_intent.succeeded
    - Triggers job processing

GET /api/compass/report/{job_id}
    - Returns report (authenticated)
    - PDF or HTML format
```

### 4. Job Processing

**Job States:**
```
PENDING      -> Payment hold created, awaiting confirmation
RESEARCHING  -> Research agents running (30-40%)
ANALYZING    -> Solution matching in progress (40-60%)
GENERATING   -> Report being written (60-80%)
QA_REVIEW    -> Quality checks running (80-95%)
COMPLETED    -> Report ready, payment captured
FAILED       -> QA failed, payment released
REFUNDED     -> Manual refund processed
```

---

## Data Flow

### Happy Path Flow

```
1. USER SUBMITS FORM
   |
   +-> Validate input (company name, URL, industry, pain points, email)
   +-> Create Stripe PaymentIntent with capture_method: 'manual' ($497 hold)
   +-> Create Job record (status: PENDING, payment_intent_id)
   +-> Return job_id + Stripe client_secret to frontend

2. STRIPE PAYMENT CONFIRMATION
   |
   +-> Stripe.js confirms card on frontend
   +-> Webhook: payment_intent.succeeded
   +-> Update Job status: RESEARCHING
   +-> Dispatch to background worker

3. RESEARCH PIPELINE (Parallel)
   |
   +-> Company Research Agent
   |   +-> Web scrape company website
   |   +-> Search for company news/press
   |   +-> Extract: size, funding, tech stack, culture
   |
   +-> Industry AI Research Agent
   |   +-> Search: "[industry] AI automation case studies"
   |   +-> Search: "[industry] AI implementation success stories"
   |   +-> Extract: common AI use cases, ROI examples
   |
   +-> White Paper Research Agent
   |   +-> Search: AI solutions for pain points
   |   +-> Search: vendor white papers, implementation guides
   |   +-> Extract: solution comparisons, best practices
   |
   +-> Aggregator: Merge research, dedupe, validate sources
   +-> Update Job status: ANALYZING (progress: 40%)

4. ANALYSIS PIPELINE (Sequential)
   |
   +-> Solution Matcher
   |   +-> Input: pain points + research pack
   |   +-> Output: ranked solutions (RAG, Agentic, Workflow, Training, OSS)
   |   +-> Select top 2-3 based on fit score
   |
   +-> Feasibility Analyzer (per solution)
   |   +-> Assess: technical complexity, data requirements, integration effort
   |   +-> Output: implementation difficulty (1-5), timeline estimate
   |
   +-> ROI Estimator (per solution)
   |   +-> Estimate: cost savings, productivity gains, revenue potential
   |   +-> Output: ROI projection (12-month, 24-month)
   |
   +-> Update Job status: GENERATING (progress: 60%)

5. REPORT GENERATION (Sequential)
   |
   +-> Executive Summary Writer
   |   +-> Input: company profile, top solutions, key metrics
   |   +-> Output: 5-page executive summary
   |
   +-> Solution Detail Writer (x3)
   |   +-> Input: solution, feasibility, ROI, implementation steps
   |   +-> Output: 1-2 pages per solution
   |
   +-> Appendix Generator
   |   +-> Input: research sources, methodology
   |   +-> Output: 1-2 pages references
   |
   +-> HTML Renderer (Jinja2 templates)
   +-> PDF Generator
   +-> Update Job status: QA_REVIEW (progress: 80%)

6. QA GATE
   |
   +-> Content QA
   |   +-> Check: factual accuracy (citations match claims)
   |   +-> Check: coherence (sections flow logically)
   |   +-> Check: tone (professional, actionable)
   |
   +-> Technical QA
   |   +-> Check: all links valid
   |   +-> Check: PDF renders correctly
   |   +-> Check: all sections present
   |
   +-> Business QA
   |   +-> Check: solutions address stated pain points
   |   +-> Check: recommendations are actionable
   |   +-> Check: ROI estimates are reasonable
   |
   +-> Aggregate Score
   |   +-> IF score >= 7: PROCEED
   |   +-> IF score < 7: FAIL (release payment, alert team)

7. DELIVERY
   |
   +-> Stripe: Capture PaymentIntent ($497)
   +-> Gmail: Send email with PDF attachment + HTML preview
   +-> Sheets: Log delivery (job_id, email, timestamp, QA score)
   +-> Update Job status: COMPLETED (progress: 100%)
```

### Failure Path Flow

```
QA FAILS (score < 7)
   |
   +-> Stripe: Cancel PaymentIntent (release hold)
   +-> Gmail: Send apology email to customer
   +-> Sheets: Log failure (job_id, QA score, reasons)
   +-> Slack/Email: Alert operations team
   +-> Update Job status: FAILED
   +-> Human review: decide refund vs. manual fix
```

---

## Key Technical Decisions

### 1. Research Pipeline: Parallel Agents with Aggregation

**Decision:** Use 3 specialized research agents running in parallel, followed by aggregation.

**Rationale:**
- **Parallel execution:** Reduces total time from 45+ minutes (sequential) to 15-20 minutes
- **Specialization:** Each agent optimized for its domain (company info vs. industry trends vs. technical papers)
- **Aggregation:** Deduplication and quality filtering before analysis
- **Fault tolerance:** If one agent fails, others can still provide value

**Implementation:**
```python
async def run_research_pipeline(submission: CompassSubmission) -> ResearchPack:
    # Run all three agents in parallel
    company_task = company_agent.research(submission.company_url, submission.company_name)
    industry_task = industry_agent.research(submission.industry, submission.pain_points)
    whitepaper_task = whitepaper_agent.research(submission.pain_points)

    company, industry, whitepapers = await asyncio.gather(
        company_task, industry_task, whitepaper_task,
        return_exceptions=True
    )

    # Handle partial failures gracefully
    return aggregator.merge(company, industry, whitepapers)
```

### 2. AI Orchestration: Sequential Analysis with Consensus

**Decision:** Sequential analysis pipeline (match -> feasibility -> ROI) with optional consensus voting for solution selection.

**Rationale:**
- **Sequential:** Each stage depends on previous output (can't estimate ROI without knowing the solution)
- **Consensus optional:** For solution matching, run at 3 temperatures and take majority vote to reduce hallucination
- **Single-pass for detail:** Feasibility and ROI are factual enough that consensus adds time without proportional value

**Trade-off:** Slightly longer analysis phase, but higher quality solution recommendations.

### 3. Report Generation: Template + Generative Hybrid

**Decision:** Use Jinja2 templates for structure, AI for content sections.

**Rationale:**
- **Templates provide:**
  - Consistent branding and formatting
  - Predictable page layout
  - Easy maintenance of non-content elements (headers, footers, ToC)

- **AI generation provides:**
  - Personalized narrative
  - Company-specific insights
  - Natural language flow

**Implementation:**
```python
# Template defines structure
<section class="executive-summary">
    <h1>{{ company_name }} AI Readiness Assessment</h1>
    <div class="ai-generated">
        {{ executive_summary_content }}  <!-- AI writes this -->
    </div>
</section>

# AI generates content to fill template slots
executive_summary_content = await ai.generate(
    prompt=f"Write a 5-page executive summary for {company_name}...",
    system_prompt=EXECUTIVE_SUMMARY_SYSTEM,
    temperature=0.7,
    max_tokens=8000,
)
```

### 4. QA Gate: Three-Tier Validation

**Decision:** Content + Technical + Business validation with weighted scoring.

**Rationale:**
- **Content QA (40%):** Ensures factual accuracy and coherence
- **Technical QA (20%):** Ensures report renders correctly, links work
- **Business QA (40%):** Ensures recommendations are relevant and actionable

**Scoring:**
```python
def calculate_qa_score(content: float, technical: float, business: float) -> float:
    return (content * 0.4) + (technical * 0.2) + (business * 0.4)

# Pass threshold: 7.0 / 10.0
```

### 5. Payment Integration: Hold-Then-Capture Pattern

**Decision:** Create PaymentIntent with `capture_method: 'manual'`, capture only after QA passes.

**Rationale:**
- **Customer protection:** Don't charge until we deliver value
- **Fraud reduction:** Card validation happens upfront
- **Refund avoidance:** No charge = no refund processing fees
- **7-day hold window:** Stripe allows up to 7 days before auto-cancel (our target: 2 hours)

**Implementation:**
```python
# On submission
intent = stripe.PaymentIntent.create(
    amount=49700,  # $497.00
    currency='usd',
    capture_method='manual',
    metadata={'job_id': job_id}
)

# After QA passes
stripe.PaymentIntent.capture(intent.id)

# If QA fails
stripe.PaymentIntent.cancel(intent.id)
```

### 6. Async Processing: SQLite-Based Job Queue

**Decision:** Use SQLite for job queue and status tracking (not Redis/Celery).

**Rationale:**
- **Simplicity:** No additional infrastructure to maintain
- **Sufficient scale:** Expected volume is <100 reports/day initially
- **Existing pattern:** System already uses SQLite for other data
- **Upgrade path:** Can migrate to Redis/Celery if volume exceeds 1000/day

**Implementation:**
```python
class Job(SQLModel, table=True):
    id: str = Field(primary_key=True)
    status: JobStatus
    progress: int  # 0-100
    submission_data: dict  # JSON
    payment_intent_id: str
    created_at: datetime
    updated_at: datetime
    report_url: Optional[str]
    qa_score: Optional[float]
    error_message: Optional[str]
```

**Background Worker:**
```python
# Simple polling worker (can upgrade to proper task queue later)
async def job_worker():
    while True:
        job = await get_next_pending_job()
        if job:
            await process_job(job)
        else:
            await asyncio.sleep(5)  # Poll every 5 seconds
```

---

## Reuse vs. Build New

### Reuse from Existing System

| Component | Location | Reuse Strategy |
|-----------|----------|----------------|
| **ClaudeAdapter** | `infrastructure/ai/claude_adapter.py` | Direct reuse - add `generate_streaming` if needed |
| **CapturingAIAdapter** | `infrastructure/ai/capturing_adapter.py` | Direct reuse for QA capture |
| **GmailAdapter** | `infrastructure/email/gmail_adapter.py` | Direct reuse for delivery |
| **SheetsAdapter** | `infrastructure/storage/sheets_adapter.py` | Direct reuse for logging |
| **QAAuditor** | `contexts/qa/auditor.py` | Extend with Compass-specific prompts |
| **FastAPI App** | `web/app.py` | Add new router for compass endpoints |
| **Dependency Injection** | `config/dependency_injection.py` | Add new providers (Stripe, Scraper) |
| **Settings** | `config/settings.py` | Add Compass-specific settings |
| **structlog** | Throughout | Direct reuse |

### Build New

| Component | Priority | Complexity | Est. Effort |
|-----------|----------|------------|-------------|
| **CompassEngine** | P0 | High | 3-4 days |
| **Research Agents (3)** | P0 | Medium each | 2 days each |
| **Solution Matcher** | P0 | Medium | 2 days |
| **Report Generator** | P0 | High | 3-4 days |
| **Stripe Adapter** | P0 | Low | 1 day |
| **Job Queue + Worker** | P0 | Medium | 2 days |
| **Compass API Routes** | P0 | Low | 1 day |
| **Submission Form UI** | P0 | Medium | 2 days |
| **PDF Generator** | P1 | Low | 1 day |
| **Web Scraper Adapter** | P1 | Medium | 2 days |
| **Content QA Validators** | P1 | Medium | 2 days |
| **Business QA Validators** | P1 | Medium | 2 days |

**Total Estimated Effort:** 25-30 developer days

---

## Risk Assessment and Mitigations

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Research agent rate limiting** | High | Medium | Implement backoff, cache common queries, use multiple API keys |
| **AI hallucination in report** | Medium | High | Multi-stage QA, human review for first 20 reports |
| **PDF generation failures** | Low | Medium | Fallback to HTML-only delivery, retry logic |
| **Stripe webhook failures** | Low | High | Idempotency keys, webhook retry handling, manual reconciliation process |
| **Long processing time (>2 hours)** | Medium | Medium | Parallel research, progress updates, email notification when ready |

### Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **High QA failure rate** | Medium | High | Iterate on prompts, lower threshold initially (6.0), human review |
| **Customer disputes** | Low | Medium | Clear expectations, refund policy, quality guarantee |
| **Research source quality** | Medium | Medium | Source validation, prefer authoritative sources, cite everything |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **API cost overruns** | Medium | Medium | Token budgets per report, cost tracking, alerts |
| **Support volume** | Medium | Low | FAQ, status page, automated updates |
| **Scaling bottleneck** | Low | Medium | Monitor job queue length, horizontal scaling path defined |

---

## API Specification

### POST /api/compass/submit

**Request:**
```json
{
    "company_name": "Acme Corp",
    "company_url": "https://acme.com",
    "industry": "Manufacturing",
    "company_size": "50-200",
    "pain_points": [
        "Manual document processing taking too long",
        "Customer support overwhelmed with repetitive queries",
        "Inventory forecasting inaccurate"
    ],
    "email": "john@acme.com",
    "contact_name": "John Smith",
    "contact_title": "VP Operations"
}
```

**Response:**
```json
{
    "job_id": "cmp_abc123",
    "status": "pending",
    "stripe_client_secret": "pi_xxx_secret_yyy",
    "estimated_completion": "2025-12-31T14:30:00Z"
}
```

### GET /api/compass/status/{job_id}

**Response (in progress):**
```json
{
    "job_id": "cmp_abc123",
    "status": "analyzing",
    "progress": 55,
    "current_stage": "Matching AI solutions to your needs",
    "estimated_completion": "2025-12-31T14:30:00Z"
}
```

**Response (complete):**
```json
{
    "job_id": "cmp_abc123",
    "status": "completed",
    "progress": 100,
    "report_url": "/api/compass/report/cmp_abc123",
    "qa_score": 8.5,
    "completed_at": "2025-12-31T14:25:00Z"
}
```

### POST /webhooks/stripe

Handles:
- `payment_intent.succeeded` - Trigger job processing
- `payment_intent.payment_failed` - Mark job as failed
- `charge.refunded` - Update job status

---

## Configuration

### New Environment Variables

```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
COMPASS_PRICE_CENTS=49700

# Research APIs
SERPAPI_KEY=...          # For web search
SCRAPER_PROXY_URL=...    # Optional proxy for scraping

# Compass Settings
COMPASS_QA_MIN_SCORE=7.0
COMPASS_MAX_PROCESSING_HOURS=4
COMPASS_RESEARCH_TIMEOUT_SECONDS=300
COMPASS_REPORT_MAX_TOKENS=32000

# Notifications
COMPASS_ALERT_EMAIL=ops@company.com
COMPASS_ALERT_SLACK_WEBHOOK=https://hooks.slack.com/...
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Create `contexts/compass/` structure
- [ ] Implement CompassEngine skeleton
- [ ] Add Stripe adapter (hold/capture/cancel)
- [ ] Create job queue and worker
- [ ] Add API endpoints (submit, status)
- [ ] Basic submission form

### Phase 2: Research Pipeline (Week 2-3)
- [ ] Company research agent
- [ ] Industry AI research agent
- [ ] White paper research agent
- [ ] Research aggregator
- [ ] Source validator

### Phase 3: Analysis Pipeline (Week 3-4)
- [ ] Solution matcher
- [ ] Feasibility analyzer
- [ ] ROI estimator
- [ ] Solution ranking algorithm

### Phase 4: Report Generation (Week 4-5)
- [ ] Report templates (HTML)
- [ ] Executive summary writer
- [ ] Solution detail writer
- [ ] PDF generator
- [ ] Report renderer

### Phase 5: QA & Delivery (Week 5-6)
- [ ] Content QA validator
- [ ] Technical QA validator
- [ ] Business QA validator
- [ ] QA gate logic
- [ ] Email delivery integration
- [ ] Stripe capture integration

### Phase 6: Polish & Launch (Week 6-7)
- [ ] Error handling and recovery
- [ ] Monitoring and alerting
- [ ] Load testing
- [ ] Documentation
- [ ] Beta testing with 5-10 real customers

---

## Appendix: Domain Models

```python
# contexts/compass/models.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    QA_REVIEW = "qa_review"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class SolutionCategory(str, Enum):
    RAG_ORCHESTRATOR = "rag_orchestrator"
    AGENTIC_ORCHESTRATOR = "agentic_orchestrator"
    WORKFLOW_TOOL = "workflow_tool"
    TRAINING_ADAPTER = "training_adapter"
    OPEN_SOURCE_AI = "open_source_ai"


@dataclass
class CompassSubmission:
    company_name: str
    company_url: str
    industry: str
    company_size: str
    pain_points: list[str]
    email: str
    contact_name: str
    contact_title: str


@dataclass
class CompanyResearch:
    name: str
    url: str
    description: str
    size_estimate: str
    funding_status: Optional[str]
    tech_stack_indicators: list[str]
    recent_news: list[dict]
    linkedin_presence: Optional[dict]
    sources: list[str]


@dataclass
class IndustryResearch:
    industry: str
    ai_adoption_level: str  # low, medium, high
    common_use_cases: list[dict]
    success_stories: list[dict]
    failure_lessons: list[dict]
    key_vendors: list[str]
    sources: list[str]


@dataclass
class WhitePaperResearch:
    papers: list[dict]  # title, url, summary, relevance_score
    implementation_guides: list[dict]
    vendor_comparisons: list[dict]
    sources: list[str]


@dataclass
class ResearchPack:
    company: CompanyResearch
    industry: IndustryResearch
    whitepapers: WhitePaperResearch
    aggregated_at: datetime


@dataclass
class Solution:
    category: SolutionCategory
    name: str
    description: str
    fit_score: float  # 0-100
    feasibility: dict  # complexity, timeline, prerequisites
    roi_estimate: dict  # 12_month, 24_month, confidence
    implementation_steps: list[str]
    recommended_vendors: list[str]
    risks: list[str]


@dataclass
class CompassReport:
    job_id: str
    company_name: str
    executive_summary: str  # HTML content
    solutions: list[Solution]
    appendix: str  # HTML content
    html_content: str  # Full report HTML
    pdf_url: Optional[str]
    qa_score: float
    generated_at: datetime


@dataclass
class CompassJob:
    id: str
    status: JobStatus
    progress: int
    submission: CompassSubmission
    payment_intent_id: str
    research_pack: Optional[ResearchPack]
    report: Optional[CompassReport]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-31 | Architect Agent | Initial design |

---

**Next Steps:**
1. Review with COO for resource allocation
2. Prioritize Phase 1 implementation
3. Spike on research API options (SerpAPI vs. alternatives)
4. Design submission form UI with Designer agent
