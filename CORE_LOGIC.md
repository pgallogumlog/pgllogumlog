# CORE_LOGIC.md - The Soul of the Application

**Generated:** January 5, 2026
**Product:** AI Readiness Compass ($497 Premium Report)
**Version:** Two-Call Architecture

---

## TABLE OF CONTENTS

1. [Product Overview](#1-product-overview)
2. [Primary User Workflows](#2-primary-user-workflows)
3. [Core Data Schemas](#3-core-data-schemas)
4. [Scoring & Mathematical Rules](#4-scoring--mathematical-rules)
5. [External Dependencies](#5-external-dependencies)
6. [Quality Assurance Pipeline](#6-quality-assurance-pipeline)
7. [Payment & Delivery Flow](#7-payment--delivery-flow)

---

## 1. PRODUCT OVERVIEW

### What It Does

The AI Readiness Compass generates personalized AI adoption strategy reports for businesses. For $497, customers receive:

- **AI Readiness Score** (0-100) - Hybrid score combining self-assessment and AI research
- **Top 3 Business Priorities** - Each with a specific vendor/product recommendation
- **90-Day Implementation Roadmap** - Month-by-month action plan with budgets
- **Anti-Recommendations** - What to avoid and why (premium differentiator)
- **Research-Backed Insights** - Real web citations, not hallucinated advice

### Architecture Philosophy

```
TWO-CALL DESIGN PRINCIPLE:
"Complete context produces complete answers"

Call 1: Deep Research    → Gather ALL data with web search (86+ citations)
Call 2: Strategic Synthesis → Generate recommendations from FULL context

Benefits:
- Better quality (synthesis sees everything)
- Lower cost (2 calls vs 4+ agent calls)
- Simpler debugging
- Cacheable research context
```

---

## 2. PRIMARY USER WORKFLOWS

### 2.1 Complete Assessment Flow (Happy Path)

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: SUBMISSION (User Action)                                    │
├─────────────────────────────────────────────────────────────────────┤
│ User fills web form:                                                │
│ • Company name, website, industry, size                             │
│ • Self-assessment questions (3 questions, 1-5 scale each)           │
│ • Pain point description                                            │
│ • Email for delivery                                                │
│ • Payment method (Stripe)                                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: PAYMENT AUTHORIZATION                                       │
├─────────────────────────────────────────────────────────────────────┤
│ POST /api/compass/create-payment-intent                             │
│ • Stripe creates PaymentIntent with manual_capture                  │
│ • Funds HELD but NOT charged ($497)                                 │
│ • Customer sees pending authorization                               │
│ • Returns: client_secret, payment_intent_id                         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: SELF-ASSESSMENT SCORING                                     │
├─────────────────────────────────────────────────────────────────────┤
│ SelfAssessmentScorer.score(assessment)                              │
│ Input: data_maturity, automation_experience, change_readiness (1-5) │
│ Output: 20-100 score (30% of final AI Readiness Score)              │
│ Also: Readiness level (Beginner/Developing/Established/Advanced)    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: CALL 1 - DEEP RESEARCH (Claude + Web Search)                │
├─────────────────────────────────────────────────────────────────────┤
│ _call_1_deep_research(request)                                      │
│ • Calls Claude with web_search_20250305 tool enabled                │
│ • Up to 15 web searches performed                                   │
│ • Returns: research_findings (JSON), metadata, citations (list)     │
│                                                                     │
│ Research sections populated:                                        │
│ • company_analysis (website findings, current tech stack)           │
│ • industry_intelligence (market stats, trends, benchmarks)          │
│ • implementation_patterns (case studies, success/failure stories)   │
│ • technology_landscape (vendor analysis, pricing, integrations)     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: RESEARCH QUALITY GATE (HARD BLOCKER)                        │
├─────────────────────────────────────────────────────────────────────┤
│ ResearchQualityGate.validate()                                      │
│                                                                     │
│ ALL must pass:                                                      │
│ ✓ >= 10 verified web sources (HTTP 200 response)                    │
│ ✓ >= 3 unique domains in citations                                  │
│ ✓ <= 30% NOT_FOUND in required fields                               │
│ ✓ >= 1 company-specific finding                                     │
│ ✓ >= 1 industry statistic with source                               │
│                                                                     │
│ IF FAILS → Cancel payment authorization, notify customer, STOP      │
│ IF PASSES → Continue to synthesis                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6: CALL 1 QA VALIDATION                                        │
├─────────────────────────────────────────────────────────────────────┤
│ Call1Validator.validate(research_findings, request)                 │
│ • Checks relevance to company context                               │
│ • Validates completeness of research sections                       │
│ • Verifies metadata (finding counts, sources)                       │
│ • Returns: CallQAResult (passed, score 1-10, issues)                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 7: HYBRID SCORING                                              │
├─────────────────────────────────────────────────────────────────────┤
│ Calculate AI Readiness Score:                                       │
│                                                                     │
│ overall = (self_assessment × 0.30) + (research_score × 0.70)        │
│                                                                     │
│ research_score derived from:                                        │
│ • Website maturity signals                                          │
│ • Tech stack indicators                                             │
│ • Industry position                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 8: CALL 2 - STRATEGIC SYNTHESIS                                │
├─────────────────────────────────────────────────────────────────────┤
│ _call_2_synthesis(request, research_findings, ai_readiness_score)   │
│                                                                     │
│ Input context includes:                                             │
│ • Complete research from Call 1                                     │
│ • Company profile and pain point                                    │
│ • AI Readiness Score and tier                                       │
│                                                                     │
│ Generates:                                                          │
│ • Top 3 Business Priorities (each with 1 specific solution)         │
│ • 90-Day Roadmap (3 phases with budgets)                            │
│ • Anti-Recommendations (2-3 "what to avoid")                        │
│ • Executive summary and key metrics                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 9: CALL 2 QA VALIDATION                                        │
├─────────────────────────────────────────────────────────────────────┤
│ Call2Validator.validate(synthesis_output, request)                  │
│ • Checks specificity (not generic advice)                           │
│ • Validates vendor/product names present                            │
│ • Verifies roadmap completeness                                     │
│ • Returns: CallQAResult (passed, score 1-10, issues)                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 10: CROSS-CALL VALIDATION                                      │
├─────────────────────────────────────────────────────────────────────┤
│ CrossCallValidator.validate(research_findings, synthesis_output)    │
│ • Verifies synthesis actually USES research                         │
│ • Counts research findings referenced in recommendations            │
│ • Detects orphaned research (unused findings)                       │
│ • Calculates research_used_percent                                  │
│ • Returns: CrossCallQAResult (passed, score, utilization %)         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 11: HALLUCINATION DETECTION (Grounding Check)                  │
├─────────────────────────────────────────────────────────────────────┤
│ _check_synthesis_grounding(synthesis, research)                     │
│ • AI-powered check that recommendations trace to research           │
│ • Counts claims not grounded in research data                       │
│ • IF >= 3 hallucinations detected:                                  │
│   → Retry synthesis with stricter prompt (max 1 retry)              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 12: REPORT GENERATION                                          │
├─────────────────────────────────────────────────────────────────────┤
│ CompassReportGenerator.generate_html(report_data)                   │
│ • Jinja2 template rendering                                         │
│ • Premium styling (8-10 page PDF-ready layout)                      │
│ • Injects company name, scores, recommendations                     │
│ • Includes citations and research sources                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 13: AGGREGATE QA & DECISION                                    │
├─────────────────────────────────────────────────────────────────────┤
│ Aggregate all QA results:                                           │
│ • call_1_qa.passed                                                  │
│ • call_2_qa.passed                                                  │
│ • cross_call_qa.passed                                              │
│ • research_quality.passed                                           │
│                                                                     │
│ IF ALL PASS:                                                        │
│   → Capture payment ($497 charged)                                  │
│   → Send email with report                                          │
│   → Log success to Google Sheets                                    │
│                                                                     │
│ IF ANY FAIL:                                                        │
│   → Cancel payment authorization                                    │
│   → Notify customer (not charged, issue explained)                  │
│   → Log failure details to Google Sheets                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 14: LOGGING & RETURN                                           │
├─────────────────────────────────────────────────────────────────────┤
│ Log to Google Sheets (QA summary row):                              │
│ • Timestamp, run_id, company_name                                   │
│ • call_1_qa, call_2_qa, cross_call_qa scores                        │
│ • research_quality metrics                                          │
│ • payment_captured, email_sent status                               │
│ • total_tokens, duration                                            │
│                                                                     │
│ Return TwoCallResult with complete metadata                         │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Test Execution Workflow (Development)

```
Test Request (via API or CLI)
         │
         ▼
┌─────────────────────────────────────────────┐
│ CompassTestLoader.load_test(test_id)        │
│ • Loads from data/compass_test_suite.json   │
│ • 29 real companies with verified URLs      │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ CompassTestOrchestrator.run_test()          │
│ • Creates CompassRequest from test case     │
│ • Invokes TwoCallCompassEngine.process()    │
│ • Captures full result including QA metrics │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ Output:                                     │
│ • Generated report HTML                     │
│ • QA scores (call_1, call_2, cross_call)    │
│ • Citation count and verification stats     │
│ • Pass/fail verdict                         │
└─────────────────────────────────────────────┘
```

---

## 3. CORE DATA SCHEMAS

### 3.1 Input Schema: CompassRequest

```python
@dataclass
class CompassRequest:
    """Complete submission for AI Readiness Compass report."""

    # Company Information
    company_name: str          # e.g., "Robin Hood Foundation"
    website: str               # e.g., "https://robinhood.org"
    industry: str              # e.g., "Nonprofit & Philanthropy"
    company_size: str          # e.g., "51-200 employees"

    # Self-Assessment (1-5 scale each)
    self_assessment: SelfAssessment
        data_maturity: int           # How structured is business data?
        automation_experience: int   # Current automation adoption level
        change_readiness: int        # Ability to adopt new technology

    # Problem Statement
    pain_point: str            # e.g., "Donor engagement tracking"
    description: str           # Detailed context about the challenge

    # Delivery
    email: str                 # Where to send the report
    contact_name: str          # Personalization
```

### 3.2 Output Schema: CompassReport

```python
@dataclass
class CompassReport:
    """Complete AI Readiness Compass report deliverable."""

    run_id: str                            # Unique identifier (UUID)
    company_name: str                      # Company being analyzed
    timestamp: datetime                    # When report was generated

    # Core Scores
    ai_readiness_score: AIReadinessScore
        self_assessment_score: float       # 0-100 (from user inputs)
        research_score: float              # 0-100 (from AI analysis)
        overall_score: float               # 0-100 (weighted combination)
        breakdown: dict[str, float]        # Per-component scores

    # Recommendations (Top 3 Priorities)
    priorities: list[BusinessPriority]     # Each with ONE specific solution
        rank: int                          # 1, 2, or 3
        problem_name: str                  # e.g., "Donor Engagement Gap"
        problem_description: str           # Why this matters
        solution: AISolution               # Specific vendor recommendation

    # Implementation Plan
    roadmap: list[RoadmapPhase]            # 3-month plan
        month: int                         # 1, 2, or 3
        focus: str                         # e.g., "Quick Win - Deploy Chatbot"
        specific_deliverables: list[str]   # What to produce
        tools_to_implement: list[str]      # Products to deploy
        budget: str                        # e.g., "$2,000-$3,000"
        decision_gate: str                 # Success metric

    # What to Avoid
    avoid: list[AntiRecommendation]        # 2-3 anti-recommendations
        name: str                          # e.g., "Custom LLM Fine-tuning"
        vendor_examples: list[str]         # Who offers this
        why_tempting: str                  # Why it seems attractive
        why_wrong_for_them: str            # Why it's wrong for THIS company
        cost_of_mistake: str               # What they'd waste

    # Supporting Data
    research_insights: dict                # Raw research from Call 1
    html_content: str                      # Rendered premium HTML
    qa_report: Optional[CompassQAReport]   # QA validation details
```

### 3.3 Solution Schema: AISolution

```python
@dataclass
class AISolution:
    """Specific AI solution recommendation (PREMIUM - includes vendor details)."""

    name: str                    # e.g., "Intercom Fin AI Bot" (SPECIFIC)
    vendor: str                  # e.g., "Intercom" (SPECIFIC VENDOR)
    approach_type: str           # RAG, Agentic, Automation, Platform
    description: str             # What it does
    why_this_fits: str           # Tied to AI Readiness + research

    # Features & Integrations
    specific_features: list[str] # Features addressing their pain
    integrations: list[str]      # Systems they can integrate with

    # Economics
    pricing: SolutionPricing
        model: str               # per_user, per_usage, flat_rate
        estimated_monthly: str   # e.g., "$500-$1,500/month"
        implementation_cost: str # e.g., "$5,000 one-time"

    # Impact
    expected_impact: str         # e.g., "40% ticket reduction in 60 days"
    complexity: str              # Low, Medium, High
    time_to_value: str           # e.g., "4-6 weeks"
```

### 3.4 QA Validation Schemas

```python
@dataclass
class CallQAResult:
    """Per-call validation result (Call 1 or Call 2)."""

    call_id: str                 # Unique call identifier
    call_number: int             # 1 or 2
    call_type: str               # "Research" or "Synthesis"
    passed: bool                 # Overall pass/fail
    score: int                   # 1-10 quality score

    # Semantic Checks
    is_relevant: bool            # Content relevant to request
    is_specific: bool            # Not generic boilerplate
    is_complete: bool            # All required sections present

    # Issues & Guidance
    issues: list[str]            # What failed
    recommendations: list[str]   # How to improve

    # Metrics
    input_tokens: int            # Prompt tokens
    output_tokens: int           # Response tokens
    duration_ms: float           # Call duration

@dataclass
class CrossCallQAResult:
    """Cross-call validation (Call 1 ↔ Call 2 coherence)."""

    passed: bool                     # Overall coherence check
    score: int                       # 1-10
    call_2_references_call_1: bool   # Does synthesis cite research?
    research_used_count: int         # How many findings used
    research_total_count: int        # Total findings available

    @property
    def research_used_percent(self) -> float:
        return (research_used_count / research_total_count) * 100

    issues: list[str]
    recommendations: list[str]

@dataclass
class ResearchQualityResult:
    """Research Quality Gate result (HARD BLOCKER)."""

    passed: bool                     # ALL checks must pass
    verified_source_count: int       # URLs that return HTTP 200
    unique_domain_count: int         # Distinct domains in citations
    not_found_ratio: float           # % of fields with NOT_FOUND

    has_company_data: bool           # Found company-specific info
    has_industry_stats: bool         # Found industry statistics

    issues: list[str]                # What failed
    should_cancel_authorization: bool  # Cancel payment if failed

    total_citations: int             # Total citations returned
    verification_duration_ms: float  # How long verification took
```

---

## 4. SCORING & MATHEMATICAL RULES

### 4.1 Self-Assessment Score (30% of Final)

**Formula:** Weighted average of 3 dimensions (1-5 scale → 0-100)

```python
class SelfAssessmentScorer:
    WEIGHTS = {
        "data_maturity": 0.40,         # Most critical for AI success
        "automation_experience": 0.35, # Indicates existing capability
        "change_readiness": 0.25,      # Organizational factor
    }

    def score(self, assessment: SelfAssessment) -> float:
        # Convert 1-5 scale to 0-100 percentage
        data_pct = (assessment.data_maturity / 5) * 100
        automation_pct = (assessment.automation_experience / 5) * 100
        change_pct = (assessment.change_readiness / 5) * 100

        # Apply weights
        weighted_score = (
            data_pct * 0.40 +      # 40% weight
            automation_pct * 0.35 + # 35% weight
            change_pct * 0.25       # 25% weight
        )

        return weighted_score  # Range: 20-100
```

**Output Range:** 20-100 (minimum when all inputs are 1/5)

**Readiness Levels:**
| Score Range | Level | Description |
|-------------|-------|-------------|
| 0-30 | Beginner | Just starting AI journey |
| 31-50 | Developing | Building foundation |
| 51-70 | Established | Ready for sophisticated solutions |
| 71-85 | Advanced | Can handle complex implementations |
| 86-100 | Leading | AI-first organization |

### 4.2 Hybrid AI Readiness Score

**Formula:** Weighted combination of self-assessment and research

```python
class TwoCallCompassEngine:
    SELF_ASSESSMENT_WEIGHT = 0.30
    RESEARCH_WEIGHT = 0.70

    def calculate_hybrid_score(
        self,
        self_assessment_score: float,  # 0-100
        research_score: float           # 0-100
    ) -> float:
        overall = (
            self_assessment_score * 0.30 +  # User's input: 30%
            research_score * 0.70           # AI research: 70%
        )
        return overall  # Range: 0-100
```

**Why 70/30 Split:**
- Self-assessment alone is subjective (people overestimate readiness)
- Research provides objective signals (website tech, industry position)
- 70% research prevents gaming by inflating self-scores

### 4.3 Research Quality Gate Thresholds

**ALL must pass or report is blocked:**

```python
# Hard-coded thresholds (non-negotiable)
MIN_VERIFIED_SOURCES = 10     # At least 10 URLs must return HTTP 200
MIN_UNIQUE_DOMAINS = 3        # At least 3 different websites cited
MAX_NOT_FOUND_RATIO = 0.30    # Max 30% of fields can be NOT_FOUND
URL_VERIFICATION_TIMEOUT = 5  # 5 seconds per URL check
```

**NOT_FOUND Detection Patterns:**
```python
not_found_patterns = [
    r"not[\s_]*found",       # "not found", "NOT_FOUND"
    r"no[\s_]*data",         # "no data"
    r"unable[\s_]*to[\s_]*find",
    r"not[\s_]*available",
    r"n/a",
]
```

### 4.4 QA Call Scoring

**Severity-Based Deductions:**

```python
class CallScorer:
    # Weight by check importance
    WEIGHTS = {
        "json_validity": 3.0,           # Critical for generate_json
        "truncation_detection": 2.5,    # Data loss is serious
        "token_limit_warning": 0.5,     # Minor warning
        "response_empty": 2.0,          # Useless response
        "prompt_relevance": 2.0,        # Quality indicator
        "hallucination_detection": 2.5, # Accuracy critical
    }

    # Score deductions by severity
    SEVERITY_DEDUCTIONS = {
        Severity.CRITICAL: 8,  # 10 → 2
        Severity.HIGH: 5,      # 10 → 5
        Severity.MEDIUM: 3,    # 10 → 7
        Severity.LOW: 1,       # 10 → 9
        Severity.NONE: 0,      # No deduction
    }

    min_pass_score = 7  # Must score >= 7/10 to pass
```

**Scoring Algorithm:**
```python
def score(self, capture: AICallCapture) -> CallScore:
    base_score = 10.0

    # Calculate total weight for normalization
    total_weight = sum(
        self.WEIGHTS.get(r.check_name, 1.0)
        for r in capture.validation_results
    )

    for result in capture.validation_results:
        deduction = self.SEVERITY_DEDUCTIONS[result.severity]
        weight = self.WEIGHTS.get(result.check_name, 1.0)

        # Weighted deduction (normalized)
        weighted_deduction = (deduction * weight) / max(total_weight, 1.0)
        base_score -= weighted_deduction

    overall_score = max(1, min(10, round(base_score)))
    passed = overall_score >= 7

    return CallScore(overall_score=overall_score, passed=passed, ...)
```

---

## 5. EXTERNAL DEPENDENCIES

### 5.1 Anthropic Claude API (Core AI)

**Purpose:** All AI-powered content generation and analysis

| Aspect | Details |
|--------|---------|
| **Package** | `anthropic>=0.39.0` |
| **Model** | `claude-sonnet-4-20250514` (default) |
| **Key Features Used** | `messages.create()`, `web_search_20250305` tool |
| **Rate Limiting** | Exponential backoff (2-60s delays, max 5 retries) |
| **Max Tokens** | 8192 for research, 4096 for synthesis |

**Why Claude:**
- Native web search tool (`web_search_20250305`) for real-time research
- Structured JSON output mode for reliable parsing
- High-quality reasoning for strategic recommendations

**API Methods Used:**
```python
# Text generation
await client.messages.create(model, messages, max_tokens, temperature)

# JSON generation with web search
await client.messages.create(
    model,
    messages,
    max_tokens=8192,
    tools=[{
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 15,
    }]
)
```

### 5.2 Stripe Payment API

**Purpose:** Payment authorization and capture

| Aspect | Details |
|--------|---------|
| **Package** | `stripe` (implicit via API) |
| **Flow** | Manual capture (authorize → hold → capture/cancel) |
| **Amount** | $497 (49700 cents) |
| **Test Mode** | Enabled via `COMPASS_TEST_MODE=True` |

**Why Stripe:**
- Manual capture allows charge ONLY after QA passes
- If report fails quality, authorization is cancelled (no charge)
- Customer never pays for failed reports

**Payment Flow:**
```python
# Step 1: Create PaymentIntent (holds funds)
payment_intent = await stripe.PaymentIntent.create(
    amount=49700,
    currency="usd",
    capture_method="manual",  # KEY: Don't charge yet
    payment_method=payment_method_id,
    confirm=True,
)

# Step 2a: If QA passes → Capture payment
await stripe.PaymentIntent.capture(payment_intent_id)

# Step 2b: If QA fails → Cancel authorization
await stripe.PaymentIntent.cancel(payment_intent_id)
```

### 5.3 Google Sheets API

**Purpose:** QA logging and metrics tracking

| Aspect | Details |
|--------|---------|
| **Package** | `google-api-python-client>=2.108.0`, `gspread>=5.12.0` |
| **Auth** | Service Account credentials |
| **Sheets Used** | QA Call Log, QA Summary |

**Why Google Sheets:**
- Easy visualization of QA metrics over time
- Shareable with non-technical stakeholders
- No database infrastructure needed
- Real-time collaboration

**Data Logged:**
```
QA Summary Row:
| Timestamp | Run ID | Company | Call1 Score | Call2 Score | CrossCall Score |
| Research Quality | Payment Captured | Email Sent | Total Tokens | Duration |
```

### 5.4 SMTP Email (Gmail)

**Purpose:** Report delivery

| Aspect | Details |
|--------|---------|
| **Package** | `aiohttp>=3.9.0` (for async), built-in `smtplib` |
| **Host** | `smtp.gmail.com` (default) |
| **Port** | 587 (TLS) or 465 (SSL) |
| **Auth** | Gmail App Passwords |

**Why SMTP:**
- Universal email delivery
- No vendor lock-in
- Simple integration

### 5.5 aiohttp (HTTP Client)

**Purpose:** URL verification in Research Quality Gate

| Aspect | Details |
|--------|---------|
| **Package** | `aiohttp>=3.9.0` |
| **Use Case** | HTTP HEAD requests to verify citation URLs |
| **Concurrency** | Semaphore limits to 10 parallel requests |
| **Timeout** | 5 seconds per URL |

**Why aiohttp:**
- Async HTTP for parallel URL verification
- Non-blocking during quality gate checks
- Fast verification of 86+ citations

### 5.6 FastAPI (Web Framework)

**Purpose:** REST API for submissions and status

| Aspect | Details |
|--------|---------|
| **Package** | `fastapi>=0.104.0` |
| **Server** | Uvicorn (`uvicorn[standard]>=0.24.0`) |
| **Features** | Pydantic validation, async handlers, OpenAPI docs |

**Endpoints:**
```
POST /api/compass/create-payment-intent  → Authorize payment
POST /api/compass/submit                 → Submit assessment
GET  /api/compass/status/{run_id}        → Check processing status
GET  /api/compass/report/{run_id}        → Retrieve completed report
GET  /api/health                         → Health check
```

### 5.7 Jinja2 (Templating)

**Purpose:** Premium report HTML generation

| Aspect | Details |
|--------|---------|
| **Package** | `jinja2>=3.1.2` |
| **Templates** | `web/ui/templates/compass/` |
| **Output** | 8-10 page PDF-ready HTML |

### 5.8 structlog (Logging)

**Purpose:** Structured, async-safe logging

| Aspect | Details |
|--------|---------|
| **Package** | `structlog>=23.2.0` |
| **Features** | JSON output, context binding, async-safe |
| **Log Fields** | run_id, company_name, call_number, tokens, duration |

---

## 6. QUALITY ASSURANCE PIPELINE

### 6.1 Multi-Level Validation Architecture

```
Level 1: Research Quality Gate (HARD BLOCKER)
    ├── >= 10 verified URLs
    ├── >= 3 unique domains
    ├── <= 30% NOT_FOUND
    ├── Has company-specific data
    └── Has industry statistics
         │
         ▼ (Only continues if ALL pass)

Level 2: Call 1 Validation (Research Quality)
    ├── Relevance to company context
    ├── Completeness of sections
    └── Metadata validation
         │
         ▼

Level 3: Call 2 Validation (Synthesis Quality)
    ├── Specificity (not generic)
    ├── Vendor names present
    └── Roadmap completeness
         │
         ▼

Level 4: Cross-Call Validation (Coherence)
    ├── Synthesis references research
    ├── Research utilization percentage
    └── Orphaned research detection
         │
         ▼

Level 5: Hallucination Detection (Grounding)
    ├── AI-powered grounding check
    ├── Claims traced to research
    └── Retry on >= 3 hallucinations
         │
         ▼

Level 6: Post-Generation QA (Optional Phase 1)
    ├── Content semantic analysis
    ├── Professional tone check
    └── Completeness verification
```

### 6.2 Deterministic Validators (Fast, No API)

```python
DETERMINISTIC_VALIDATORS = [
    JSONValidityValidator,      # Check JSON parses correctly
    TruncationDetector,         # Detect incomplete responses
    TokenLimitWarning,          # Warn if approaching limits
    EmptyResponseDetector,      # Detect empty/null responses
    TokenCountRangeValidator,   # Check token counts reasonable
]
```

### 6.3 Probabilistic Validators (Semantic, Requires API)

```python
PROBABILISTIC_VALIDATORS = [
    PromptRelevanceValidator,   # Does response match prompt intent?
    HallucinationDetector,      # Are claims grounded in facts?
    SemanticCoherenceValidator, # Is content internally consistent?
]
```

---

## 7. PAYMENT & DELIVERY FLOW

### 7.1 Manual Capture Pattern

```
Customer Submits Form
        │
        ▼
┌───────────────────────────────────┐
│ AUTHORIZE (Hold Funds)            │
│ PaymentIntent.create(             │
│   capture_method="manual"         │
│ )                                 │
│ Customer sees pending $497        │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ PROCESS REPORT                    │
│ - Deep Research (web search)      │
│ - Quality Gate validation         │
│ - Strategic Synthesis             │
│ - Multi-level QA validation       │
└───────────────────────────────────┘
        │
        ├──────────────────────────────────────┐
        │                                      │
        ▼ (QA PASSED)                          ▼ (QA FAILED)
┌───────────────────────┐          ┌────────────────────────────┐
│ CAPTURE Payment       │          │ CANCEL Authorization       │
│ Customer charged $497 │          │ Hold released              │
│                       │          │ Customer NOT charged       │
│ SEND Email            │          │                            │
│ Report delivered      │          │ NOTIFY Customer            │
│                       │          │ "We couldn't complete..."  │
│ LOG Success           │          │ "You have not been charged"│
│ to Google Sheets      │          │                            │
└───────────────────────┘          └────────────────────────────┘
```

### 7.2 Key Principle

> **"No research = No report = No charge"**

The customer is NEVER charged unless we deliver a quality report. No refunds needed because no charge occurs on failure.

---

## APPENDIX: File Locations

| Component | File Path |
|-----------|-----------|
| Two-Call Engine | `contexts/compass/two_call_engine.py` |
| Self-Assessment Scorer | `contexts/compass/scoring.py` |
| Research Quality Gate | `contexts/compass/validators/research_quality_gate.py` |
| Domain Models | `contexts/compass/models.py` |
| QA Scoring Pipeline | `contexts/qa/scoring.py` |
| Claude Adapter | `infrastructure/ai/claude_adapter.py` |
| Stripe Adapter | `infrastructure/payments/stripe_adapter.py` |
| API Routes | `web/api/compass.py` |
| Settings | `config/settings.py` |
| Dependency Injection | `config/dependency_injection.py` |
| Test Suite | `data/compass_test_suite.json` |
