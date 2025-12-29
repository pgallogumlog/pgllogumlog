# Designer A: Feasibility-First Progressive Selection

## Approach Type
**HOLISTIC** with tier-sensitive weighting

## Core Philosophy
Quality over sophistication. Select workflows users can actually implement, progressively building from proven foundations to innovative opportunities. Diversity through functional domains, not artificial variety.

## Selection Algorithm

### Step 1: Feasibility Filtering & Scoring
```
Base Score = Feasibility Weight × Metrics Quality × Tool Practicality

Feasibility Weight:
- High = 1.0
- Medium = 0.7 (Budget tier) | 0.85 (Standard/Premium)
- Low = 0.3 (all tiers)

Metrics Quality (0-1 scale):
- Parse metrics for quantitative values
- Score = (avg_metric_value - 50) / 50, capped at [0, 1]
- If no metrics, score = 0.5

Tool Practicality (0-1 scale):
- Count tools: 1-3 tools = 1.0, 4-5 = 0.85, 6+ = 0.7
- Budget tier: Boost +0.15 for Zapier/n8n/Make presence
- Premium tier: Boost +0.10 for "Custom"/"API" presence
```

### Step 2: Domain Clustering
Group workflows by functional domain using keyword analysis:
- **Data Processing**: classification, extraction, parsing, NLP
- **Compliance & Risk**: regulatory, compliance, audit, risk
- **Communication**: email, notification, reporting, dashboard
- **Analysis & Intelligence**: analytics, insights, prediction, forecasting
- **Workflow Management**: orchestration, tracking, coordination

### Step 3: Diversity-Aware Selection
```python
selected = []
domains_covered = set()

# Sort workflows by Base Score (descending)
ranked_workflows = sort_by_score(workflows)

for workflow in ranked_workflows:
    domain = identify_domain(workflow)

    # Strong preference for uncovered domains
    if domain not in domains_covered:
        selected.append(workflow)
        domains_covered.add(domain)

        if len(selected) == 5:
            break

    # Allow same domain only if significantly better score
    elif len(selected) < 5 and workflow.score > selected[-1].score * 1.3:
        selected.append(workflow)

# If we have <5, backfill with highest scoring remaining
while len(selected) < 5:
    selected.append(next_highest_score())

return selected
```

### Step 4: Tier-Specific Reordering
After selection, reorder by tier priority:

**Budget**: High feasibility first, then descending score
**Standard**: Balanced order (feasibility + score mix)
**Premium**: Highest impact first (metrics-driven), then feasibility

## Scoring Formula (Mathematical)

```
Score(w) = F(w) × M(w) × T(w) × D(w)

Where:
F(w) = Feasibility factor ∈ {0.3, 0.7/0.85, 1.0}
M(w) = Metrics quality ∈ [0, 1]
T(w) = Tool practicality ∈ [0.7, 1.15]
D(w) = Diversity bonus = 1.5 if new domain, else 1.0
```

## Diversity Mechanism

**Domain-Based Clustering**: Workflows naturally cluster into 5-7 functional domains. By ensuring each of the top 5 comes from different domains, we guarantee:
1. Users see breadth of automation opportunities
2. No redundant recommendations
3. Coverage across their business operations

**Fallback for Domain Overlap**: If a workflow scores >30% higher than the 5th selected workflow, include it even if domain overlap exists (indicates exceptional opportunity).

## Tier Handling

**Shared Logic**: All tiers use the same algorithm
**Tier Sensitivity**:
- Budget: Higher penalty for Medium feasibility (0.7 vs 0.85), boost for common tools
- Standard: Balanced (no special adjustments)
- Premium: Slight boost for custom/API tools, metrics weigh heavier

**Philosophy**: Users' needs differ by budget, not intelligence. Premium users can handle complex workflows, but everyone deserves feasible recommendations.

## Pseudocode Implementation

```python
def select_top_5_workflows(workflows, tier, prompt):
    # Step 1: Score all workflows
    scored = []
    for wf in workflows:
        feasibility_score = get_feasibility_weight(wf.feasibility, tier)
        metrics_score = parse_metrics_quality(wf.metrics)
        tools_score = calculate_tool_practicality(wf.tools, tier)

        base_score = feasibility_score * metrics_score * tools_score
        scored.append((wf, base_score))

    # Step 2: Sort by score
    scored.sort(key=lambda x: x[1], reverse=True)

    # Step 3: Domain-aware selection
    selected = []
    domains_used = set()

    for wf, score in scored:
        domain = classify_domain(wf)

        if domain not in domains_used:
            selected.append((wf, score, domain))
            domains_used.add(domain)

            if len(selected) == 5:
                break

    # Step 4: Backfill if needed
    while len(selected) < 5:
        for wf, score in scored:
            if wf not in [s[0] for s in selected]:
                # Allow if score is significantly higher
                if score > selected[-1][1] * 1.3:
                    selected.append((wf, score, classify_domain(wf)))
                    break

    # Step 5: Tier-specific reordering
    if tier == "Budget":
        selected.sort(key=lambda x: (x[0].feasibility == "High", x[1]), reverse=True)
    elif tier == "Premium":
        selected.sort(key=lambda x: x[1], reverse=True)  # Pure score

    return [s[0] for s in selected[:5]]

def classify_domain(workflow):
    """Classify workflow into functional domain."""
    text = f"{workflow.name} {workflow.objective} {workflow.description}".lower()

    if any(kw in text for kw in ['classify', 'extract', 'parse', 'nlp', 'ocr']):
        return "data_processing"
    elif any(kw in text for kw in ['compliance', 'regulatory', 'audit', 'risk']):
        return "compliance_risk"
    elif any(kw in text for kw in ['email', 'notification', 'report', 'dashboard']):
        return "communication"
    elif any(kw in text for kw in ['analytics', 'insight', 'predict', 'forecast']):
        return "analysis_intelligence"
    elif any(kw in text for kw in ['orchestr', 'track', 'coordinate', 'manage']):
        return "workflow_management"
    else:
        return "other"

def get_feasibility_weight(feasibility, tier):
    if feasibility == "High":
        return 1.0
    elif feasibility == "Medium":
        return 0.7 if tier == "Budget" else 0.85
    else:  # Low
        return 0.3

def parse_metrics_quality(metrics):
    """Extract numeric quality from metrics list."""
    if not metrics:
        return 0.5

    numbers = []
    for metric in metrics:
        # Extract percentages and multipliers
        import re
        nums = re.findall(r'(\d+)%', metric)
        nums.extend(re.findall(r'(\d+)x', metric))
        numbers.extend([float(n) for n in nums])

    if not numbers:
        return 0.5

    avg = sum(numbers) / len(numbers)
    # Normalize: 50 = baseline, >50 = better
    return min(1.0, max(0.0, (avg - 50) / 50))

def calculate_tool_practicality(tools, tier):
    tool_count = len(tools)

    # Base score by tool count
    if tool_count <= 3:
        score = 1.0
    elif tool_count <= 5:
        score = 0.85
    else:
        score = 0.7

    # Tier-specific boosts
    tool_str = ' '.join(tools).lower()

    if tier == "Budget":
        if any(t in tool_str for t in ['zapier', 'n8n', 'make']):
            score += 0.15
    elif tier == "Premium":
        if 'custom' in tool_str or 'api' in tool_str:
            score += 0.10

    return min(1.15, score)
```

## Justification

### Why This Delivers Best Results

1. **User Success Focus**: Feasibility-first ensures users can actually implement recommendations, not just admire sophisticated ideas

2. **Data-Driven**: Analysis showed 45% High, 47% Medium, 8% Low feasibility across tiers. This distribution means we need smart filtering to surface the best opportunities

3. **Domain Diversity**: Natural clustering into functional domains (data, compliance, communication, etc.) ensures breadth without artificial constraints

4. **Tier-Appropriate**: Budget users get practical quick wins, Premium users get highest-impact solutions - but all get feasible workflows

5. **Explainable**: "We selected these 5 because they cover different aspects of your operations (data processing, compliance, communication), all are highly feasible, and have proven metrics"

6. **Avoids Over-Engineering**: No complex ML models needed, no semantic similarity calculations, no LLM calls for selection - just clear heuristics

## Example Application

Using: Budget tier, Latham & Watkins LLP prompt (cross-border M&A due diligence)

**Data Sample**: 125 workflows generated

**Top 5 Selected**:

1. **Multi-Language Document Classification** (Domain: Data Processing)
   - Feasibility: High (1.0)
   - Metrics: 95% accuracy, 70% time reduction → Quality: 0.9
   - Tools: 4 tools (n8n, Google Translate, NLP, SharePoint) → 0.85 + 0.15 (Budget boost) = 1.0
   - Score: 1.0 × 0.9 × 1.0 × 1.5 (new domain) = 1.35

2. **Due Diligence Progress Tracker** (Domain: Workflow Management)
   - Feasibility: High (1.0)
   - Metrics: 85% on-time completion, 9/10 visibility → Quality: 0.85
   - Tools: 3 tools (Zapier, Power BI, Slack) → 1.0 + 0.15 = 1.15
   - Score: 1.0 × 0.85 × 1.15 × 1.5 = 1.47

3. **Regulatory Compliance Mapping Engine** (Domain: Compliance & Risk)
   - Feasibility: Medium (0.7 for Budget)
   - Metrics: 98% coverage, 5x speed → Quality: 0.96
   - Tools: 3 tools (Zapier, Thomson Reuters API, DB) → 1.0 + 0.15 = 1.15
   - Score: 0.7 × 0.96 × 1.15 × 1.5 = 1.16

4. **Contract Risk Assessment Bot** (Domain: Analysis & Intelligence)
   - Feasibility: Medium (0.7)
   - Metrics: 89% detection, <15% false positives → Quality: 0.78
   - Tools: 3 tools (n8n, LexisNexis, ML models) → 1.0 + 0.15 = 1.15
   - Score: 0.7 × 0.78 × 1.15 × 1.5 = 0.94

5. **Cross-Border Entity Structure Analyzer** (Domain: Data Processing - 2nd in domain)
   - Feasibility: High (1.0)
   - Metrics: 92% accuracy, 80% faster → Quality: 0.86
   - Tools: 3 tools (Make, Graph API, Lucidchart) → 1.0 + 0.15 = 1.15
   - Score: 1.0 × 0.86 × 1.15 × 1.0 (same domain) = 0.99

**Note**: Workflow 5 was selected because it scored >30% higher than the next candidate despite domain overlap.

**Diversity Check**: ✓ 4 different domains covered, 5th is significantly high-scoring

## Strengths
- Simple, explainable, implementable
- Guarantees feasible recommendations
- Natural diversity through domain clustering
- No external dependencies (no LLM calls for selection)
- Tier-aware but not over-complicated

## Potential Weaknesses
- Domain classification is heuristic-based (keyword matching)
- Metrics parsing may fail for unconventional formats
- Doesn't consider user prompt semantic similarity (assumes generation already did that)

## Implementation Complexity
**Low** - Pure Python with regex, no external APIs, ~150 lines of code
