# Designer C: Semantic Relevance & Impact Maximization

## Approach Type
**HOLISTIC** with AI-assisted semantic analysis

## Core Philosophy
Trust the generation system to produce relevant workflows. Our job is to select the MOST RELEVANT and HIGHEST IMPACT subset. Use semantic similarity to user prompt + impact metrics as the north star. Diversity is a constraint, not the goal.

## Selection Algorithm

### Step 1: Prompt-Workflow Semantic Alignment

**Challenge**: Current approaches ignore the user's actual prompt! They assume all 125 workflows are equally relevant.

**Solution**: Calculate semantic relevance score for each workflow against the user prompt.

```python
def semantic_relevance(workflow, user_prompt):
    """
    Calculate how well workflow matches user's stated needs.
    Uses keyword overlap + domain matching + objective alignment.
    """
    # Extract key intent from prompt
    prompt_keywords = extract_keywords(user_prompt)
    prompt_domain = identify_domain(user_prompt)

    # Extract workflow signals
    wf_text = f"{workflow.name} {workflow.objective} {workflow.description}"
    wf_keywords = extract_keywords(wf_text)
    wf_domain = classify_domain(workflow)

    # Keyword overlap (TF-IDF weighted)
    keyword_score = calculate_keyword_overlap(prompt_keywords, wf_keywords)

    # Domain match
    domain_score = 2.0 if wf_domain == prompt_domain else 1.0

    # Objective alignment (does workflow solve stated problem?)
    objective_score = score_objective_alignment(workflow.objective, user_prompt)

    return keyword_score * domain_score * objective_score
```

**Why This Matters**: Data shows 125 workflows per prompt. Many are tangentially related at best. Semantic scoring surfaces the truly relevant ones.

### Step 2: Impact Quantification

**Philosophy**: Metrics tell the truth. A workflow claiming "95% accuracy" is objectively more impactful than "50% accuracy" (all else equal).

```python
def calculate_impact_score(workflow):
    """
    Quantify expected business impact from metrics.
    Higher numbers = higher impact.
    """
    if not workflow.metrics:
        return 1.0  # Baseline for no metrics

    impact_signals = []

    for metric in workflow.metrics:
        # Extract percentages (accuracy, reduction, etc.)
        percentages = extract_percentages(metric)
        for pct in percentages:
            if 'accura' in metric.lower() or 'precision' in metric.lower():
                # Accuracy: 90%+ is excellent
                impact_signals.append(pct / 100)
            elif 'reduc' in metric.lower() or 'sav' in metric.lower():
                # Time/cost savings: direct impact
                impact_signals.append(pct / 50)  # 50% = 1.0 impact
            elif 'improv' in metric.lower():
                impact_signals.append(pct / 60)
            else:
                impact_signals.append(pct / 100)

        # Extract multipliers (5x faster, 10x more)
        multipliers = extract_multipliers(metric)
        for mult in multipliers:
            impact_signals.append(mult)  # Direct usage

    if not impact_signals:
        return 1.0

    # Use max impact (best metric) rather than average
    # A workflow with one exceptional metric > workflow with all mediocre metrics
    return min(5.0, max(impact_signals))
```

### Step 3: Feasibility Gating

**Reality Check**: High relevance + high impact means nothing if infeasible.

```python
def feasibility_multiplier(workflow, tier):
    """
    Feasibility acts as a multiplier, not a filter.
    We want to see Medium feasibility workflows if they're exceptional.
    """
    base = {"High": 1.0, "Medium": 0.75, "Low": 0.4}[workflow.feasibility]

    # Tier adjustment: Premium users more tolerant of complexity
    if tier == "Premium" and workflow.feasibility == "Medium":
        base = 0.9  # Less penalty
    elif tier == "Budget" and workflow.feasibility == "Medium":
        base = 0.6  # More penalty

    return base
```

### Step 4: Diversity-Constrained Selection

**Approach**: Select top-scoring workflows with diversity as a constraint.

```python
def select_top_5_with_diversity(scored_workflows, min_domain_diversity=3):
    """
    Greedy selection with diversity constraint.
    1. Sort by score
    2. Select highest scorer
    3. For remaining, penalize if too similar to already selected
    4. Repeat until 5 selected
    """
    selected = []
    domains_covered = set()

    # Sort by score descending
    candidates = sorted(scored_workflows, key=lambda x: x['score'], reverse=True)

    for candidate in candidates:
        if len(selected) == 5:
            break

        domain = classify_domain(candidate['workflow'])

        # First selection: take highest score
        if len(selected) == 0:
            selected.append(candidate)
            domains_covered.add(domain)
            continue

        # Subsequent selections: diversity penalty
        if domain in domains_covered:
            # Allow if score is significantly higher OR we have good diversity already
            if candidate['score'] > selected[-1]['score'] * 1.4:
                selected.append(candidate)
            elif len(domains_covered) >= min_domain_diversity:
                # Diversity target met, can add similar
                selected.append(candidate)
        else:
            # New domain: take it
            selected.append(candidate)
            domains_covered.add(domain)

    return [s['workflow'] for s in selected]
```

## Complete Scoring Formula

```
Final Score = Semantic Relevance × Impact Score × Feasibility Multiplier × Consensus Bonus

Where:
- Semantic Relevance ∈ [0.1, 5.0]
  - Keyword overlap: TF-IDF weighted
  - Domain match: 2x if matched, 1x otherwise
  - Objective alignment: 0.5-2.0 based on problem-solution fit

- Impact Score ∈ [1.0, 5.0]
  - Extracted from metrics (percentages, multipliers)
  - Uses MAX metric value (best-case impact)

- Feasibility Multiplier ∈ [0.4, 1.0]
  - High: 1.0
  - Medium: 0.6-0.9 (tier-dependent)
  - Low: 0.4

- Consensus Bonus ∈ [1.0, 1.2]
  - Strong consensus: 1.2
  - Moderate: 1.1
  - Weak: 1.0
  - (Available from workflow generation metadata)
```

## Tier Handling

**HOLISTIC approach**: Same algorithm across tiers, but tier affects feasibility penalty.

**Justification**: The user prompt already encodes tier expectations. A Budget user asking for "simple automation" will generate simpler workflows. A Premium user asking for "AI-powered analysis" will generate sophisticated workflows. The selection algorithm doesn't need to second-guess this.

**Tier-Specific Adjustment**: Only in feasibility penalty (shown above).

## Pseudocode Implementation

```python
import re
from collections import Counter
import math

def select_top_5_workflows(workflows, tier, user_prompt, consensus_strength=None):
    """Main selection function."""
    # Score all workflows
    scored = []

    for wf in workflows:
        semantic_score = calculate_semantic_relevance(wf, user_prompt)
        impact_score = calculate_impact_score(wf)
        feasibility_mult = get_feasibility_multiplier(wf.feasibility, tier)
        consensus_bonus = get_consensus_bonus(consensus_strength)

        final_score = semantic_score * impact_score * feasibility_mult * consensus_bonus

        scored.append({
            'workflow': wf,
            'score': final_score,
            'semantic': semantic_score,
            'impact': impact_score,
            'feasibility': feasibility_mult
        })

    # Select top 5 with diversity
    selected = select_with_diversity_constraint(scored, min_domains=3)

    return selected

def calculate_semantic_relevance(workflow, user_prompt):
    """Calculate how well workflow matches user's prompt."""
    # Keyword extraction (TF-IDF style)
    prompt_keywords = extract_important_keywords(user_prompt)
    wf_text = f"{workflow.name} {workflow.objective} {workflow.description}"
    wf_keywords = extract_important_keywords(wf_text)

    # Keyword overlap with TF-IDF weighting
    overlap_score = calculate_tfidf_overlap(prompt_keywords, wf_keywords)

    # Domain matching
    prompt_domain = identify_primary_domain(user_prompt)
    wf_domain = classify_domain(workflow)
    domain_bonus = 2.0 if prompt_domain == wf_domain else 1.0

    # Objective-problem alignment
    alignment = score_objective_alignment(workflow.objective, user_prompt)

    semantic_score = overlap_score * domain_bonus * alignment

    # Clamp to reasonable range
    return max(0.1, min(5.0, semantic_score))

def extract_important_keywords(text):
    """Extract meaningful keywords, weighted by importance."""
    # Remove stopwords, lowercase
    stopwords = {'the', 'and', 'or', 'for', 'with', 'to', 'of', 'in', 'a', 'an'}
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in stopwords and len(w) > 3]

    # Count frequencies (term frequency)
    freq = Counter(keywords)

    # Weight by TF (higher frequency = more important)
    # Simplified TF-IDF (we don't have document corpus for IDF)
    weighted = {term: math.log(1 + count) for term, count in freq.items()}

    return weighted

def calculate_tfidf_overlap(prompt_kw, wf_kw):
    """Calculate weighted keyword overlap."""
    if not prompt_kw or not wf_kw:
        return 0.5  # Baseline

    # Find common keywords
    common = set(prompt_kw.keys()) & set(wf_kw.keys())

    if not common:
        return 0.5  # Baseline for no overlap

    # Weight overlap by TF scores
    overlap_weight = sum(prompt_kw[kw] * wf_kw[kw] for kw in common)

    # Normalize by prompt keyword importance
    total_prompt_weight = sum(prompt_kw.values())

    score = overlap_weight / total_prompt_weight if total_prompt_weight > 0 else 0.5

    # Scale to [0.5, 3.0] range
    return 0.5 + (score * 2.5)

def identify_primary_domain(text):
    """Identify main business domain from text."""
    text_lower = text.lower()

    domains = {
        'legal': ['legal', 'law', 'contract', 'compliance', 'regulatory', 'due diligence'],
        'finance': ['financial', 'accounting', 'invoice', 'payment', 'revenue'],
        'hr': ['hr', 'human resources', 'recruiting', 'employee', 'talent'],
        'sales': ['sales', 'crm', 'lead', 'pipeline', 'customer'],
        'operations': ['operations', 'supply chain', 'logistics', 'inventory'],
        'marketing': ['marketing', 'campaign', 'email marketing', 'seo', 'content'],
        'support': ['support', 'customer service', 'helpdesk', 'ticket']
    }

    scores = {}
    for domain, keywords in domains.items():
        scores[domain] = sum(1 for kw in keywords if kw in text_lower)

    return max(scores, key=scores.get) if max(scores.values()) > 0 else 'general'

def classify_domain(workflow):
    """Classify workflow's functional domain."""
    text = f"{workflow.name} {workflow.objective} {workflow.description}".lower()

    if any(kw in text for kw in ['legal', 'law', 'contract', 'compliance', 'regulatory']):
        return 'legal'
    elif any(kw in text for kw in ['financial', 'invoice', 'payment', 'accounting']):
        return 'finance'
    elif any(kw in text for kw in ['hr', 'recruit', 'employee', 'talent']):
        return 'hr'
    elif any(kw in text for kw in ['sales', 'crm', 'lead', 'customer']):
        return 'sales'
    elif any(kw in text for kw in ['market', 'campaign', 'seo']):
        return 'marketing'
    elif any(kw in text for kw in ['support', 'helpdesk', 'ticket']):
        return 'support'
    else:
        return 'operations'

def score_objective_alignment(objective, user_prompt):
    """Score how well workflow objective addresses prompt."""
    # Check if objective contains key verbs/goals from prompt
    objective_lower = objective.lower()
    prompt_lower = user_prompt.lower()

    # Extract action verbs
    action_verbs = ['automate', 'analyze', 'classify', 'extract', 'detect',
                    'predict', 'optimize', 'streamline', 'improve', 'reduce']

    prompt_actions = [v for v in action_verbs if v in prompt_lower]
    objective_actions = [v for v in action_verbs if v in objective_lower]

    # Overlap in actions
    action_overlap = len(set(prompt_actions) & set(objective_actions))

    if action_overlap > 0:
        return 1.5  # Strong alignment
    elif any(v in objective_lower for v in action_verbs):
        return 1.2  # Has action verb, partial alignment
    else:
        return 0.8  # Weak alignment

def calculate_impact_score(workflow):
    """Calculate business impact from metrics."""
    if not workflow.metrics:
        return 1.0

    impact_values = []

    for metric in workflow.metrics:
        metric_lower = metric.lower()

        # Extract percentages
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', metric)
        for pct_str in percentages:
            pct = float(pct_str)

            # Context-aware impact
            if any(kw in metric_lower for kw in ['accura', 'precision', 'recall', 'f1']):
                # Accuracy: 90%+ is excellent, 70% is baseline
                impact = max(0.5, (pct - 70) / 20)
            elif any(kw in metric_lower for kw in ['reduc', 'sav', 'decreas']):
                # Reduction/savings: higher is better
                impact = pct / 50  # 50% = 1.0 impact
            elif any(kw in metric_lower for kw in ['improv', 'increas', 'boost']):
                # Improvement: higher is better
                impact = pct / 60
            else:
                # Generic percentage
                impact = pct / 100

            impact_values.append(impact)

        # Extract multipliers (5x, 10x)
        multipliers = re.findall(r'(\d+(?:\.\d+)?)\s*x', metric_lower)
        for mult_str in multipliers:
            mult = float(mult_str)
            impact_values.append(mult / 2)  # 2x = 1.0 impact

    if not impact_values:
        return 1.0

    # Use max impact (highlight best metric)
    max_impact = max(impact_values)

    # Clamp to [1.0, 5.0]
    return max(1.0, min(5.0, max_impact))

def get_feasibility_multiplier(feasibility, tier):
    """Feasibility penalty, tier-adjusted."""
    base_multipliers = {
        "High": 1.0,
        "Medium": 0.75,
        "Low": 0.4
    }

    multiplier = base_multipliers[feasibility]

    # Tier adjustments
    if tier == "Premium" and feasibility == "Medium":
        multiplier = 0.9  # Premium users more tolerant
    elif tier == "Budget" and feasibility == "Medium":
        multiplier = 0.6  # Budget users less tolerant

    return multiplier

def get_consensus_bonus(consensus_strength):
    """Bonus for strong consensus from generation."""
    if consensus_strength == "Strong":
        return 1.2
    elif consensus_strength == "Moderate":
        return 1.1
    else:
        return 1.0

def select_with_diversity_constraint(scored_workflows, min_domains=3):
    """Select top 5 with domain diversity constraint."""
    selected = []
    domains_covered = set()

    # Sort by score (descending)
    candidates = sorted(scored_workflows, key=lambda x: x['score'], reverse=True)

    for candidate in candidates:
        if len(selected) >= 5:
            break

        wf = candidate['workflow']
        domain = classify_domain(wf)

        # Always take first (highest score)
        if len(selected) == 0:
            selected.append(candidate)
            domains_covered.add(domain)
            continue

        # Check diversity
        if domain in domains_covered:
            # Allow if:
            # 1. Score is 40%+ higher than current 5th pick, OR
            # 2. We already have min_domains diversity
            if len(selected) < 5:
                if candidate['score'] > selected[-1]['score'] * 1.4:
                    selected.append(candidate)
                elif len(domains_covered) >= min_domains:
                    selected.append(candidate)
        else:
            # New domain: always add
            selected.append(candidate)
            domains_covered.add(domain)

    # Ensure we have 5 (backfill if needed)
    if len(selected) < 5:
        for candidate in candidates:
            if len(selected) >= 5:
                break
            if candidate not in selected:
                selected.append(candidate)

    return [s['workflow'] for s in selected[:5]]
```

## Justification

### Why This Delivers Best Results

1. **Prompt-Centric**: Unlike other approaches, this directly measures relevance to user's stated needs. The user's prompt is the ground truth.

2. **Impact-Driven**: Metrics contain objective evidence of value. A workflow with "95% accuracy, 10x faster" beats "70% accuracy, 2x faster" objectively.

3. **Data-Informed Diversity**: Diversity is a constraint (min 3 domains), not the goal. We don't artificially force variety at the cost of quality.

4. **Consensus-Aware**: Leverages the multi-temperature generation metadata. Strong consensus workflows get a bonus (they were consistent across temperatures).

5. **Explainable**: "We selected these 5 because they best match your stated needs (semantic relevance), have the highest proven impact (metrics), and are feasible for your tier."

6. **Simple Tier Handling**: User prompt + tier already determines sophistication. Selection doesn't need to second-guess.

## Example Application

Using: Standard tier, Latham & Watkins LLP prompt
"Analyze Latham & Watkins at https://www.lw.com and recommend the top 5 AI workflows for automation for automating cross-border M&A due diligence document review, based on real-world results from similar Global Law Firms and white papers."

**Key Prompt Elements**:
- Domain: Legal (M&A, due diligence, document review)
- Action: Automate, analyze
- Context: Cross-border, global law firms
- Keywords: M&A, due diligence, document review, cross-border

**Scoring Example**:

**Workflow 1: Multi-Language Document Classification**
- Semantic Relevance:
  - Keywords: "document" (match), "classification" (related to review)
  - Domain: Legal/Operations = 2.0 (domain match)
  - Objective: "Automate categorization" (action match) = 1.5
  - Total: 2.5 × 2.0 × 1.5 = 7.5 → clamped to 5.0
- Impact: 95% accuracy → (95-70)/20 = 1.25, 70% time reduction → 70/50 = 1.4 → max = 1.4
- Feasibility: High = 1.0
- Consensus: Moderate = 1.1
- **Final Score: 5.0 × 1.4 × 1.0 × 1.1 = 7.7**

**Workflow 2: Regulatory Compliance Mapping Engine**
- Semantic Relevance:
  - Keywords: "regulatory", "compliance" (high relevance to legal M&A)
  - Domain: Legal = 2.0
  - Objective: "Auto-identify jurisdiction-specific" = 1.5
  - Total: 3.0 × 2.0 × 1.5 = 9.0 → clamped to 5.0
- Impact: 98% coverage → 1.4, 5x speed → 5/2 = 2.5 → max = 2.5
- Feasibility: Medium = 0.75
- Consensus: Moderate = 1.1
- **Final Score: 5.0 × 2.5 × 0.75 × 1.1 = 10.3**

**Workflow 3: Due Diligence Progress Tracker**
- Semantic Relevance:
  - Keywords: "due diligence" (exact match!), "progress", "tracker"
  - Domain: Operations = 1.0 (not exact legal, but operations)
  - Objective: "Monitor review status" = 1.5
  - Total: 4.0 × 1.0 × 1.5 = 6.0 → clamped to 5.0
- Impact: 85% on-time → 0.75, 9/10 visibility (assume 90%) → 1.0 → max = 1.0
- Feasibility: High = 1.0
- Consensus: Moderate = 1.1
- **Final Score: 5.0 × 1.0 × 1.0 × 1.1 = 5.5**

**Workflow 4: Contract Risk Assessment Bot**
- Semantic Relevance:
  - Keywords: "contract", "risk", "assessment" (high relevance to M&A)
  - Domain: Legal = 2.0
  - Objective: "Identify high-risk clauses" = 1.5
  - Total: 3.5 × 2.0 × 1.5 = 10.5 → clamped to 5.0
- Impact: 89% detection → 0.95, <15% false positives (assume reverse: 85% accuracy) → 0.75 → max = 0.95
- Feasibility: Medium = 0.75
- Consensus: Moderate = 1.1
- **Final Score: 5.0 × 0.95 × 0.75 × 1.1 = 3.9**

**Workflow 5: Cross-Border Entity Structure Analyzer**
- Semantic Relevance:
  - Keywords: "cross-border" (exact match!), "entity structure" (M&A core)
  - Domain: Legal/Finance = 2.0
  - Objective: "Visualize complex international corporate structures" = 1.5
  - Total: 4.5 × 2.0 × 1.5 = 13.5 → clamped to 5.0
- Impact: 92% accuracy → 1.1, 80% faster → 1.6 → max = 1.6
- Feasibility: High = 1.0
- Consensus: Moderate = 1.1
- **Final Score: 5.0 × 1.6 × 1.0 × 1.1 = 8.8**

**Top 5 Selected** (after diversity check):
1. Regulatory Compliance Mapping Engine (Score: 10.3, Domain: Legal/Compliance)
2. Cross-Border Entity Structure Analyzer (Score: 8.8, Domain: Legal/Finance)
3. Multi-Language Document Classification (Score: 7.7, Domain: Operations/Data)
4. Due Diligence Progress Tracker (Score: 5.5, Domain: Operations/Tracking)
5. Contract Risk Assessment Bot (Score: 3.9, Domain: Legal/Risk) - *allowed despite 3rd legal domain because diversity target (3) met*

**Diversity Check**: ✓ Legal (3), Operations (2) - Different sub-domains within legal (Compliance, Finance, Risk)

## Strengths
- Directly measures prompt relevance (other approaches ignore this!)
- Impact-driven with objective metrics
- Leverages consensus metadata from generation
- Simple tier handling (prompt already encodes expectations)
- Explainable to users

## Potential Weaknesses
- TF-IDF is simplified (no true document corpus for IDF calculation)
- Domain classification is still heuristic-based
- Metrics parsing may fail on unusual formats
- Semantic scoring doesn't use embeddings/LLMs (could be enhanced)

## Implementation Complexity
**Medium** - More sophisticated than Designer A, but no external API calls. Pure Python with regex/keyword analysis, ~250 lines of code.

## Future Enhancements
If we wanted to invest more:
1. Use sentence embeddings (e.g., sentence-transformers) for true semantic similarity
2. LLM-based relevance scoring (call Claude to rate relevance 1-10)
3. Learn from user feedback (which selected workflows get implemented?)
4. Dynamic diversity thresholds based on workflow count and score distribution
