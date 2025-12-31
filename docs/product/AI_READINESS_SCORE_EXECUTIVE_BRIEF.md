# AI Readiness Score: One-Page Executive Brief
## For: COO | From: Architect

---

## THE QUESTION
How much can we automatically infer about a company's AI readiness vs. how much must we ask the user?

## THE ANSWER: 60/40 RULE

**60% must come from user input** (they know their business)
**40% can be inferred** (tech stack, industry, benchmarks)

---

## WHAT TO ASK USERS (60%)

**These 3 Things Only - Takes 5 Minutes**:

1. **What's your biggest operational pain point?**
   - How many times per month? (100? 1,000? 10,000?)
   - Is it highly repetitive or requires judgment?
   - Score: ±15 points

2. **What's your current tech infrastructure?**
   - Cloud? Legacy databases? Custom integrations?
   - Any automation experience with Zapier/n8n?
   - Score: ±15 points

3. **What constraints exist?**
   - Timeline urgency?
   - Available budget?
   - Compliance/regulatory requirements?
   - Score: ±10 points

**Why**: These are invisible from outside. Only the company knows.

---

## WHAT WE CAN INFER (40%)

### Website Analysis (If they provide it)
- **Tech Stack**: React? WordPress? Outdated PHP?
- **AI/Automation Tools**: Using Zapier? Stripe? Intercom chatbot?
- **Company Maturity**: Mobile-optimized? Modern security?
- Impact: **±8 points**

### Industry Benchmarks (Free Data)
- **Peer Comparison**: "You're 72nd percentile for Healthcare"
- **Size Baseline**: "Mid-market companies like you average 65/100"
- **Starting Point**: "Top 3 companies in your industry automate these workflows"
- Impact: **±15 points**

### Public Research (Optional, Post-Launch)
- LinkedIn: Hiring in AI/tech? Headcount trends?
- Press: Recent innovation announcements?
- Job Posts: What roles are they hiring?
- Impact: **±5 points** (only if high confidence)

---

## THE SCORE MODEL

```
AI Readiness Score (0-100)

├─ User Input Component (60%)
│  ├─ Pain Point Severity: 20 points
│  ├─ Tech Maturity: 20 points
│  └─ Business Fit: 20 points
│
└─ Inference Component (40%)
   ├─ Website Analysis: 15 points (if available)
   ├─ Industry Benchmark: 20 points
   └─ Public Research: 5 points (future)
```

**Example Calculation**:
- User provides comprehensive input: **60/60**
- Website shows modern cloud infrastructure: **+12/15**
- Industry average is 65, they're above: **+15/20**
- **Final Score: 87/100 (HIGH readiness)**

---

## FEASIBILITY & TIMELINE

| Component | Effort | Launch |
|-----------|--------|--------|
| Expand form (add questions) | 2-3 days | Week 1 ✓ |
| Score calculation engine | 3 days | Week 2 ✓ |
| Website analysis module | 5-7 days | Week 3-4 |
| Benchmark integration | 2 days | Week 4 |
| **Total MVP** | **~4 weeks** | **Ready by Week 4** |
| LinkedIn + press data | 3-4 weeks | Week 8+ |

**Graceful Degradation**: If website analysis fails, falls back to user input + benchmarks (still 80% value)

---

## WHY THIS MATTERS FOR PRICING

**Current Situation**:
- Form → Processing → Email report
- User thinks: "This could be a ChatGPT prompt"
- Pricing power: LOW

**With AI Readiness Score**:
- Form + Website Analysis → Research → Consensus Vote → Personalized Score + Report
- User thinks: "They analyzed our specific situation deeply"
- Pricing power: **HIGH**

**Impact**:
- Justifies $149 Standard (vs $99 competitor)
- Justifies $399 Premium (adds strategy call + benchmarking context)
- Can upsell follow-up services ("Re-assess quarterly" = recurring revenue)

---

## RISK SUMMARY

**Technical Risk**: **LOW**
- Website scraping fails? Fall back to benchmarks only
- Public research APIs unavailable? Still works with form + benchmarks
- No single point of failure

**Business Risk**: **LOW**
- Extra 2 weeks delays launch slightly
- But significantly improves product-market fit
- ROI: Worth the delay

**Privacy Risk**: **LOW**
- Transparent in form ("We'll analyze your website")
- Respect robots.txt, minimal scraping
- No personal data collection
- GDPR/CCPA compliant

---

## RECOMMENDATION

### GO WITH HYBRID MODEL

**Do NOT do**:
- ❌ Form-only (too generic, weak pricing power)
- ❌ Full inference-only (too risky, poor accuracy)

**DO this**:
- ✅ Phase 1 (Week 1-2): Form-based scoring
- ✅ Phase 2 (Week 3-4): Add website analysis
- ✅ Phase 3 (Week 5+): Add public research

**Launch MVP with Phases 1-2 combined** (ready Week 4)
- Users get highly personalized analysis
- We look like we did real research
- Justifies premium pricing
- Competitive moat (hard to copy with inference alone)

---

## FOR THE PREMIUM REPORT ($399)

The "AI Readiness Score" becomes the narrative anchor:

```
CLIENT SEES:
┌─────────────────────────────────────────┐
│ Your AI Readiness Score: 87/100        │
│ Industry Position: 72nd percentile      │
│                                         │
│ Why This Score:                        │
│ • Strong tech infrastructure (+12pts)   │
│ • High-volume pain points (+18pts)      │
│ • Above-average company size (+8pts)    │
│ • Limited automation experience (-8pts) │
│                                         │
│ Key Strengths                          │
│ • Cloud-ready infrastructure           │
│ • 5,000+ monthly process instances     │
│ • Modern customer data platform        │
│                                         │
│ Gap to Address                         │
│ • Team lacks n8n/Zapier experience     │
│ • Regulatory compliance complexity     │
│ • Limited integration patterns         │
│                                         │
│ Your Starting Point (Phase 1)          │
│ 1. Lead Qualification Automation      │
│    (Most feasible, high ROI)          │
│ 2. Invoice Processing                 │
│ 3. Email Triage & Routing             │
└─────────────────────────────────────────┘
```

**This narrative** = Why they paid $399 instead of $99

---

## NEXT STEPS

1. **This Week**: Review document with Product & Engineering
2. **Next Week**: Start expanding form with suggested questions
3. **Week 2**: Implement score calculation (form input only)
4. **Week 3-4**: Add website analysis
5. **Week 4**: Deploy to production with monitoring

**Decision Required**: Proceed with hybrid model? (2-week delay, major competitive advantage)

**My Vote**: Yes. The extra 2 weeks is worth 3-5x the pricing power.

